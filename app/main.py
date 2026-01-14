import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from .models import RecommendRequest, RecommendResponse, HealthResponse, Recommendation, FairnessScore, PurposeScore
from .geocoder import VWorldGeocoder
from .candidates import CandidateGenerator
from .estimator import TransitEstimator
from .scoring import Scoring
from .explanation import ExplanationGenerator

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


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="ok", service="MeetPlanner MCP")


@app.get("/mcp.json")
async def get_mcp_spec():
    """MCP 명세 파일 반환"""
    mcp_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mcp.json")
    try:
        with open(mcp_path, "r", encoding="utf-8") as f:
            return JSONResponse(content=json.load(f))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="mcp.json not found")


@app.post("/recommend", response_model=RecommendResponse)
async def recommend(request: RecommendRequest):
    if len(request.participants) < 2:
        raise HTTPException(status_code=400, detail="최소 2명 이상의 참가자가 필요합니다.")

    # 1. 지오코딩
    participant_coords = {}
    for p in request.participants:
        coords = await geocoder.geocode(p.origin_text)
        if coords is None:
            raise HTTPException(
                status_code=400,
                detail=f"'{p.origin_text}' 주소를 찾을 수 없습니다."
            )
        participant_coords[p.name] = coords

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
        purpose_score = scoring.calculate_purpose_score(candidate, request.purpose)
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
            request.purpose
        )
        recommendations.append(Recommendation(
            rank=rank,
            label=item["candidate"]["label"],
            lat=item["candidate"]["lat"],
            lng=item["candidate"]["lng"],
            eta_by_participant=item["eta_by_participant"],
            fairness=FairnessScore(std=item["fairness"]["std"], mean=item["fairness"]["mean"]),
            purpose=PurposeScore(score=item["purpose_score"]),
            why=why
        ))

    return RecommendResponse(recommendations=recommendations)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
