import express from "express";
import crypto from "crypto";

const FASTAPI_URL = process.env.FASTAPI_URL || "http://127.0.0.1:8000";

// =============================================================================
// MCP Protocol Constants - Compliant with MCP 2025-03-26+
// Reference: https://modelcontextprotocol.io/specification/2025-03-26
// =============================================================================
const MCP_PROTOCOL_VERSION = "2025-03-26";
const JSONRPC_VERSION = "2.0";

// =============================================================================
// Tool Definition - Strict Schema Validation (PlayMCP Compatible)
// All tools MUST have: name, description (non-null string), inputSchema
// =============================================================================
const TOOL_DEFINITION = {
  name: "recommend_meeting_place",
  // CRITICAL: description MUST be a non-null string for PlayMCP compatibility
  description:
    "Recommend a fair meeting location based on transit-time fairness and purpose. Analyzes travel times from multiple participant locations to suggest optimal meeting points in Seoul/Korea.",
  inputSchema: {
    type: "object",
    properties: {
      participants: {
        type: "array",
        description: "List of participants with their origin locations",
        items: {
          type: "object",
          properties: {
            name: {
              type: "string",
              description: "Participant name",
            },
            origin_text: {
              type: "string",
              description:
                "Origin location (address or place name, e.g., 강남역, 홍대입구)",
            },
          },
          required: ["origin_text"],
        },
        minItems: 2,
      },
      purpose: {
        type: "string",
        description: "Meeting purpose",
        enum: [
          "cafe_talk",
          "restaurant",
          "shopping",
          "business",
          "culture",
          "entertainment",
          "study",
          "date",
        ],
      },
    },
    required: ["participants"],
  },
};

// =============================================================================
// Server Info - MCP Implementation Interface
// =============================================================================
const SERVER_INFO = {
  name: "meetplanner-mcp",
  version: "1.0.0",
};

// =============================================================================
// Server Capabilities Declaration
// =============================================================================
const SERVER_CAPABILITIES = {
  tools: {
    listChanged: false,
  },
};

// =============================================================================
// Tool Execution Function (Stateless - No Session Dependency)
// =============================================================================
async function executeRecommendTool(args) {
  try {
    // Add default name if not provided
    const participants = (args?.participants || []).map((p, idx) => ({
      name: p.name || `Participant${idx + 1}`,
      origin_text: p.origin_text,
    }));

    // Call FastAPI backend
    const response = await fetch(`${FASTAPI_URL}/recommend`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        participants,
        purpose: args?.purpose || "cafe_talk",
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      return {
        content: [
          {
            type: "text",
            text: `Error: ${data.detail || "Failed to get recommendation"}`,
          },
        ],
        isError: true,
      };
    }

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(data, null, 2),
        },
      ],
      isError: false,
    };
  } catch (error) {
    return {
      content: [
        {
          type: "text",
          text: `Error: ${error.message}`,
        },
      ],
      isError: true,
    };
  }
}

// =============================================================================
// JSON-RPC Message Handlers
// =============================================================================
function handleInitialize(params) {
  // MCP 2025-03-26: Initialize response
  return {
    protocolVersion: MCP_PROTOCOL_VERSION,
    capabilities: SERVER_CAPABILITIES,
    serverInfo: SERVER_INFO,
  };
}

function handleToolsList() {
  // MCP 2025-03-26: tools/list response
  // CRITICAL: Every tool MUST have name, description (non-null), inputSchema
  return {
    tools: [TOOL_DEFINITION],
  };
}

async function handleToolsCall(params) {
  const { name, arguments: toolArgs } = params || {};

  if (name !== "recommend_meeting_place") {
    throw { code: -32602, message: `Unknown tool: ${name}` };
  }

  return await executeRecommendTool(toolArgs);
}

// =============================================================================
// Process Single JSON-RPC Message
// =============================================================================
async function processMessage(message) {
  const { jsonrpc, method, params, id } = message;

  // Validate JSON-RPC version
  if (jsonrpc !== JSONRPC_VERSION) {
    return {
      jsonrpc: JSONRPC_VERSION,
      error: { code: -32600, message: "Invalid Request: jsonrpc must be 2.0" },
      id: id || null,
    };
  }

  // Handle notification (no id = no response expected)
  const isNotification = id === undefined;

  try {
    let result;

    switch (method) {
      case "initialize":
        result = handleInitialize(params);
        break;

      case "notifications/initialized":
        // Notification - no response needed
        return null;

      case "notifications/cancelled":
        // Cancellation notification - no response needed
        return null;

      case "tools/list":
        result = handleToolsList();
        break;

      case "tools/call":
        result = await handleToolsCall(params);
        break;

      case "ping":
        result = {};
        break;

      default:
        if (isNotification) {
          return null; // Ignore unknown notifications
        }
        return {
          jsonrpc: JSONRPC_VERSION,
          error: { code: -32601, message: `Method not found: ${method}` },
          id,
        };
    }

    // Don't respond to notifications
    if (isNotification) {
      return null;
    }

    return {
      jsonrpc: JSONRPC_VERSION,
      result,
      id,
    };
  } catch (error) {
    if (isNotification) {
      return null;
    }
    return {
      jsonrpc: JSONRPC_VERSION,
      error: {
        code: error.code || -32603,
        message: error.message || "Internal error",
      },
      id,
    };
  }
}

// =============================================================================
// SSE Helper Functions (Streamable HTTP Transport)
// =============================================================================
function generateEventId() {
  return crypto.randomUUID();
}

function formatSSEEvent(data, eventId) {
  let event = "";
  if (eventId) {
    event += `id: ${eventId}\n`;
  }
  event += `data: ${JSON.stringify(data)}\n\n`;
  return event;
}

// =============================================================================
// Express Server Setup
// =============================================================================
const app = express();
app.use(express.json());

// =============================================================================
// MCP Endpoint - Streamable HTTP Transport
// Reference: https://modelcontextprotocol.io/specification/2025-03-26/basic/transports#streamable-http
// =============================================================================
app.route("/mcp")
  // -------------------------------------------------------------------------
  // POST /mcp - Client sends JSON-RPC messages
  // -------------------------------------------------------------------------
  .post(async (req, res) => {
    const body = req.body;
    const acceptHeader = req.headers.accept || "";
    const sessionId = req.headers["mcp-session-id"];

    console.log("MCP POST Request:", JSON.stringify(body, null, 2));

    // Determine if client accepts SSE
    const acceptsSSE = acceptHeader.includes("text/event-stream");
    const acceptsJSON = acceptHeader.includes("application/json");

    // Process messages (can be single message or batch)
    const messages = Array.isArray(body) ? body : [body];
    const responses = [];
    let hasRequests = false;
    let isInitialize = false;

    for (const message of messages) {
      // Check if this is a request (has id) vs notification
      if (message.id !== undefined) {
        hasRequests = true;
      }
      if (message.method === "initialize") {
        isInitialize = true;
      }

      const response = await processMessage(message);
      if (response !== null) {
        responses.push(response);
      }
    }

    // MCP 2025-03-26: If only notifications, return 202 Accepted with empty body
    if (!hasRequests) {
      return res.status(202).end();
    }

    // Generate new session ID for initialize requests (stateless - not stored)
    // For PlayMCP compatibility: server is stateless, session ID is for client tracking only
    if (isInitialize) {
      const newSessionId = crypto.randomUUID();
      res.setHeader("Mcp-Session-Id", newSessionId);
    }

    // Decide response format based on Accept header
    // MCP 2025-03-26: Server can respond with JSON or SSE stream
    if (acceptsSSE && responses.length > 0) {
      // Streamable HTTP: Respond with SSE
      res.setHeader("Content-Type", "text/event-stream");
      res.setHeader("Cache-Control", "no-cache");
      res.setHeader("Connection", "keep-alive");

      for (const response of responses) {
        const eventId = generateEventId();
        res.write(formatSSEEvent(response, eventId));
      }

      // Close the stream after sending all responses
      res.end();
    } else {
      // Respond with JSON
      res.setHeader("Content-Type", "application/json");

      if (responses.length === 1) {
        res.json(responses[0]);
      } else {
        res.json(responses);
      }
    }

    console.log("MCP Response sent:", responses.length, "messages");
  })

  // -------------------------------------------------------------------------
  // GET /mcp - Client opens SSE stream for server-initiated messages
  // -------------------------------------------------------------------------
  .get((req, res) => {
    const acceptHeader = req.headers.accept || "";
    const sessionId = req.headers["mcp-session-id"];
    const lastEventId = req.headers["last-event-id"];

    // MCP 2025-03-26: GET opens SSE stream for server-to-client messages
    if (!acceptHeader.includes("text/event-stream")) {
      return res.status(400).json({
        error: "Accept header must include text/event-stream",
      });
    }

    console.log("MCP GET Request - Opening SSE stream");

    // Set SSE headers
    res.setHeader("Content-Type", "text/event-stream");
    res.setHeader("Cache-Control", "no-cache");
    res.setHeader("Connection", "keep-alive");

    // Send initial comment to establish connection
    res.write(": MCP SSE stream established\n\n");

    // Keep connection alive with periodic pings
    const keepAliveInterval = setInterval(() => {
      res.write(": keepalive\n\n");
    }, 30000);

    // Handle client disconnect
    req.on("close", () => {
      clearInterval(keepAliveInterval);
      console.log("MCP SSE stream closed");
    });

    // NOTE: This is a stateless server - no server-initiated messages stored
    // The stream stays open for potential future server notifications
    // For PlayMCP compatibility, we don't send unsolicited messages
  })

  // -------------------------------------------------------------------------
  // DELETE /mcp - Client terminates session
  // -------------------------------------------------------------------------
  .delete((req, res) => {
    const sessionId = req.headers["mcp-session-id"];
    console.log("MCP DELETE Request - Session termination:", sessionId);

    // Stateless server: No session state to clean up
    // Just acknowledge the termination
    res.status(202).end();
  });

// =============================================================================
// Health Check Endpoint
// =============================================================================
app.get("/health", (req, res) => {
  res.json({
    status: "ok",
    service: "MeetPlanner MCP Server",
    protocol: MCP_PROTOCOL_VERSION,
    transport: "Streamable HTTP",
  });
});

// =============================================================================
// MCP.json Static Endpoint (for PlayMCP discovery)
// =============================================================================
app.get("/mcp.json", (req, res) => {
  res.json({
    protocolVersion: MCP_PROTOCOL_VERSION,
    serverInfo: SERVER_INFO,
    capabilities: SERVER_CAPABILITIES,
    endpoint: {
      method: "POST",
      url: "https://meetplanner.fly.dev/mcp",
    },
    tools: [TOOL_DEFINITION],
  });
});

// =============================================================================
// Start Server
// =============================================================================
const PORT = process.env.PORT || 3000;

app.listen(PORT, "0.0.0.0", () => {
  console.log(`MCP Server running on http://0.0.0.0:${PORT}`);
  console.log(`Protocol Version: ${MCP_PROTOCOL_VERSION}`);
  console.log(`Transport: Streamable HTTP`);
  console.log(`FastAPI backend: ${FASTAPI_URL}`);
});
