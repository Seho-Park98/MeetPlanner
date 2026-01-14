from pydantic import BaseModel
from typing import Optional


class Participant(BaseModel):
    name: str
    origin_text: str


class RecommendRequest(BaseModel):
    participants: list[Participant]
    purpose: str = "cafe_talk"


class ETAByParticipant(BaseModel):
    pass


class FairnessScore(BaseModel):
    std: float
    mean: float


class PurposeScore(BaseModel):
    score: float


class Recommendation(BaseModel):
    rank: int
    label: str
    lat: float
    lng: float
    eta_by_participant: dict[str, int]
    fairness: FairnessScore
    purpose: PurposeScore
    why: str


class RecommendResponse(BaseModel):
    recommendations: list[Recommendation]


class HealthResponse(BaseModel):
    status: str
    service: str
