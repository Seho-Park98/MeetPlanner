import express from "express";

const FASTAPI_URL = process.env.FASTAPI_URL || "http://127.0.0.1:8000";

// Tool 정의
const TOOL_DEFINITION = {
  name: "recommend_meeting_place",
  description:
    "Recommend a fair meeting location based on transit-time fairness and purpose.",
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

// Server 정보
const SERVER_INFO = {
  name: "MeetPlanner MCP",
  version: "1.0.0",
};

// Tool 실행 함수
async function executeRecommendTool(args) {
  try {
    // participants에 name이 없으면 기본값 추가
    const participants = (args?.participants || []).map((p, idx) => ({
      name: p.name || `Participant${idx + 1}`,
      origin_text: p.origin_text,
    }));

    // FastAPI 서버의 /recommend 호출
    const response = await fetch(`${FASTAPI_URL}/recommend`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
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
            text: JSON.stringify({
              error: data.detail || "Failed to get recommendation",
            }),
          },
        ],
        isError: true,
      };
    }

    // MCP 규격에 맞게 content 배열로 반환
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(data, null, 2),
        },
      ],
    };
  } catch (error) {
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({ error: error.message }),
        },
      ],
      isError: true,
    };
  }
}

// Express 서버 설정
const app = express();
app.use(express.json());

// MCP JSON-RPC 엔드포인트
app.post("/mcp", async (req, res) => {
  const body = req.body;
  console.log("MCP Request:", JSON.stringify(body, null, 2));

  const { jsonrpc, method, params, id } = body;

  // JSON-RPC 2.0 검증
  if (jsonrpc !== "2.0") {
    return res.json({
      jsonrpc: "2.0",
      error: { code: -32600, message: "Invalid Request: jsonrpc must be 2.0" },
      id: id || null,
    });
  }

  try {
    let result;

    switch (method) {
      case "initialize": {
        // MCP 초기화 응답 - PlayMCP 최신 스펙 (2025-03-26) 준수
        result = {
          protocolVersion: "2025-03-26",
          serverInfo: SERVER_INFO,
          capabilities: {
            tools: {
              listChanged: false,
            },
          },
        };
        break;
      }

      case "notifications/initialized": {
        // 초기화 완료 알림 - 응답 불필요
        return res.status(204).end();
      }

      case "tools/list": {
        // Tool 목록 반환
        result = {
          tools: [TOOL_DEFINITION],
        };
        break;
      }

      case "tools/call": {
        const { name, arguments: toolArgs } = params || {};

        if (name !== "recommend_meeting_place") {
          return res.json({
            jsonrpc: "2.0",
            error: { code: -32601, message: `Unknown tool: ${name}` },
            id,
          });
        }

        result = await executeRecommendTool(toolArgs);
        break;
      }

      default:
        return res.json({
          jsonrpc: "2.0",
          error: { code: -32601, message: `Method not found: ${method}` },
          id,
        });
    }

    const response = {
      jsonrpc: "2.0",
      result,
      id,
    };

    console.log("MCP Response:", JSON.stringify(response, null, 2));
    res.json(response);
  } catch (error) {
    console.error("MCP Error:", error);
    res.json({
      jsonrpc: "2.0",
      error: { code: -32603, message: error.message },
      id,
    });
  }
});

// Health check
app.get("/health", (req, res) => {
  res.json({ status: "ok", service: "MeetPlanner MCP Node Server" });
});

const PORT = process.env.PORT || 3000;

app.listen(PORT, "0.0.0.0", () => {
  console.log(`MCP Server running on http://0.0.0.0:${PORT}`);
  console.log(`FastAPI backend: ${FASTAPI_URL}`);
});
