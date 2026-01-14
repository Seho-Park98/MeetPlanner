# -*- coding: utf-8 -*-
import json
import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from .models import RecommendRequest, RecommendResponse, HealthResponse, Recommendation, FairnessScore, PurposeScore
from .geocoder import VWorldGeocoder
from .candidates import CandidateGenerator
from .estimator import TransitEstimator
from .scoring import Scoring
from .explanation import ExplanationGenerator
from .mcp.handler import MCPHandler

load_dotenv()

app = FastAPI(
    title="MeetPlanner MCP",
    description="여러 사용자의 출발 위치와 만남 목적을 입력받아 최적의 만남 장소를 추천하는 MCP 서버",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

geocoder = VWorldGeocoder()
candidate_generator = CandidateGenerator()
estimator = TransitEstimator()
scoring = Scoring()
explanation_generator = ExplanationGenerator()


# ============================================================
# 핵심 추천 로직 (REST API와 MCP에서 공유)
# ============================================================
async def recommend_logic(participants: list, purpose: str = "cafe_talk") -> dict:
    """추천 로직 (내부 함수)"""
    if len(participants) < 2:
        raise ValueError("최소 2명 이상의 참가자가 필요합니다.")

    # 1. 지오코딩
    participant_coords = {}
    for p in participants:
        name = p.get("name") if isinstance(p, dict) else p.name
        origin_text = p.get("origin_text") if isinstance(p, dict) else p.origin_text

        coords = await geocoder.geocode(origin_text)
        if coords is None:
            raise ValueError(f"'{origin_text}' 주소를 찾을 수 없습니다.")
        participant_coords[name] = coords

    # 2. 후보 장소 생성
    candidates = candidate_generator.generate(list(participant_coords.values()))

    # 3. 각 후보에 대해 ETA 계산
    scored_candidates = []
    for candidate in candidates:
        eta_by_participant = {}
        for name, coords in participant_coords.items():
            eta = estimator.estimate(coords, candidate)
            eta_by_participant[name] = eta

        # 4. 공정성 및 목적 적합도 점수 계산
        fairness = scoring.calculate_fairness(list(eta_by_participant.values()))
        purpose_score = scoring.calculate_purpose_score(candidate, purpose)
        total_score = scoring.calculate_total_score(fairness, purpose_score)

        scored_candidates.append({
            "candidate": candidate,
            "eta_by_participant": eta_by_participant,
            "fairness": fairness,
            "purpose_score": purpose_score,
            "total_score": total_score
        })

    # 5. 점수 기준 정렬 및 상위 5개 선택
    scored_candidates.sort(key=lambda x: x["total_score"], reverse=True)
    top_candidates = scored_candidates[:5]

    # 6. 추천 결과 생성
    recommendations = []
    for rank, item in enumerate(top_candidates, 1):
        why = explanation_generator.generate(
            item["candidate"],
            item["eta_by_participant"],
            item["fairness"],
            purpose
        )
        recommendations.append({
            "rank": rank,
            "label": item["candidate"]["label"],
            "lat": item["candidate"]["lat"],
            "lng": item["candidate"]["lng"],
            "eta_by_participant": item["eta_by_participant"],
            "fairness": {"std": item["fairness"]["std"], "mean": item["fairness"]["mean"]},
            "purpose": {"score": item["purpose_score"]},
            "why": why
        })

    return {"recommendations": recommendations}


# MCP Handler 초기화
mcp_handler = MCPHandler(recommend_logic)


# ============================================================
# REST API Endpoints
# ============================================================
@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="ok", service="MeetPlanner MCP")


@app.get("/mcp.json")
async def get_mcp_spec():
    """MCP 명세 파일 반환"""
    possible_paths = [
        "/app/mcp.json",
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "mcp.json"),
        "mcp.json"
    ]
    for mcp_path in possible_paths:
        if os.path.exists(mcp_path):
            with open(mcp_path, "r", encoding="utf-8") as f:
                return JSONResponse(content=json.load(f))
    raise HTTPException(status_code=404, detail="mcp.json not found")


@app.post("/recommend", response_model=RecommendResponse)
async def recommend(request: RecommendRequest):
    """REST API: 만남 장소 추천"""
    try:
        result = await recommend_logic(
            [{"name": p.name, "origin_text": p.origin_text} for p in request.participants],
            request.purpose
        )
        # Pydantic 모델로 변환
        recommendations = []
        for r in result["recommendations"]:
            recommendations.append(Recommendation(
                rank=r["rank"],
                label=r["label"],
                lat=r["lat"],
                lng=r["lng"],
                eta_by_participant=r["eta_by_participant"],
                fairness=FairnessScore(std=r["fairness"]["std"], mean=r["fairness"]["mean"]),
                purpose=PurposeScore(score=r["purpose"]["score"]),
                why=r["why"]
            ))
        return RecommendResponse(recommendations=recommendations)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# MCP JSON-RPC Endpoint
# ============================================================
@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """MCP JSON-RPC 2.0 엔드포인트"""
    try:
        body = await request.json()
        response = await mcp_handler.handle_request(body)
        return JSONResponse(content=response)
    except json.JSONDecodeError:
        return JSONResponse(content={
            "jsonrpc": "2.0",
            "error": {"code": -32700, "message": "Parse error"},
            "id": None
        })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
