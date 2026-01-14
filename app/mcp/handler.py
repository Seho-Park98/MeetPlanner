# -*- coding: utf-8 -*-
"""MCP JSON-RPC 2.0 Handler"""

from typing import Any, Optional
from .methods import handle_initialize, handle_tools_list, handle_tools_call


class MCPHandler:
    """MCP JSON-RPC 요청 처리기"""

    def __init__(self, recommend_func):
        """
        Args:
            recommend_func: 추천 로직 함수 (기존 REST API 로직)
        """
        self.recommend_func = recommend_func

    async def handle_request(self, request: dict) -> dict:
        """JSON-RPC 요청 처리"""
        jsonrpc = request.get("jsonrpc")
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        # JSON-RPC 2.0 검증
        if jsonrpc != "2.0":
            return self._error_response(
                request_id, -32600, "Invalid Request: jsonrpc must be '2.0'"
            )

        if not method:
            return self._error_response(
                request_id, -32600, "Invalid Request: method is required"
            )

        # 메서드 디스패치
        try:
            if method == "initialize":
                result = handle_initialize(params)
            elif method == "tools/list":
                result = handle_tools_list(params)
            elif method == "tools/call":
                result = await handle_tools_call(params, self.recommend_func)
            else:
                return self._error_response(
                    request_id, -32601, f"Method not found: {method}"
                )

            return self._success_response(request_id, result)

        except Exception as e:
            return self._error_response(
                request_id, -32603, f"Internal error: {str(e)}"
            )

    def _success_response(self, request_id: Optional[int], result: Any) -> dict:
        """성공 응답 생성"""
        return {
            "jsonrpc": "2.0",
            "result": result,
            "id": request_id
        }

    def _error_response(self, request_id: Optional[int], code: int, message: str) -> dict:
        """에러 응답 생성"""
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": code,
                "message": message
            },
            "id": request_id
        }
