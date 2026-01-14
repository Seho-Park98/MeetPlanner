# -*- coding: utf-8 -*-
"""MCP JSON-RPC Method Implementations"""

import json
from typing import Any, Callable


def handle_initialize(params: dict) -> dict:
    """initialize 메서드 처리"""
    return {
        "protocolVersion": "2024-11-05",
        "serverInfo": {
            "name": "MeetPlanner MCP",
            "version": "1.0.0"
        },
        "capabilities": {
            "tools": {
                "listChanged": False
            }
        }
    }


def handle_tools_list(params: dict) -> dict:
    """tools/list 메서드 처리"""
    return {
        "tools": [
            {
                "name": "recommend_meeting_place",
                "description": "여러 참가자의 출발 위치와 만남 목적을 기반으로 최적의 만남 장소를 추천합니다.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "participants": {
                            "type": "array",
                            "description": "참가자 목록. 각 항목은 name과 origin_text를 포함",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {
                                        "type": "string",
                                        "description": "참가자 이름"
                                    },
                                    "origin_text": {
                                        "type": "string",
                                        "description": "출발 위치 (예: 강남역, 홍대입구역)"
                                    }
                                },
                                "required": ["name", "origin_text"]
                            },
                            "minItems": 2
                        },
                        "purpose": {
                            "type": "string",
                            "description": "만남 목적",
                            "enum": ["cafe_talk", "restaurant", "shopping", "business", "culture", "entertainment", "study", "date"],
                            "default": "cafe_talk"
                        }
                    },
                    "required": ["participants"]
                }
            }
        ]
    }


async def handle_tools_call(params: dict, recommend_func: Callable) -> dict:
    """tools/call 메서드 처리"""
    tool_name = params.get("name")
    arguments = params.get("arguments", {})

    if tool_name != "recommend_meeting_place":
        raise ValueError(f"Unknown tool: {tool_name}")

    # 기존 추천 로직 직접 호출
    participants = arguments.get("participants", [])
    purpose = arguments.get("purpose", "cafe_talk")

    # recommend_func 호출 (기존 REST API 로직)
    result = await recommend_func(participants, purpose)

    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(result, ensure_ascii=False, indent=2)
            }
        ]
    }
