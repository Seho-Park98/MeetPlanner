# -*- coding: utf-8 -*-
"""MeetPlanner MCP Server (FastMCP 기반)"""

import os
from typing import Any
from dotenv import load_dotenv

from mcp.server.fastmcp import FastMCP

from app.geocoder import VWorldGeocoder
from app.candidates import CandidateGenerator
from app.estimator import TransitEstimator
from app.scoring import Scoring
from app.explanation import ExplanationGenerator
from app.map_generator import MapGenerator

# 환경 변수 로드
load_dotenv()

# FastMCP 서버 초기화
mcp = FastMCP("meetplanner")

# 모듈 인스턴스
geocoder = VWorldGeocoder()
candidate_generator = CandidateGenerator()
estimator = TransitEstimator()
scoring = Scoring()
explanation_generator = ExplanationGenerator()
map_generator = MapGenerator()


@mcp.tool()
async def recommend_meeting_place(
    participants: list[dict[str, str]],
    purpose: str = "cafe_talk",
    show_map: bool = False
) -> str:
    """여러 참가자의 출발 위치와 만남 목적을 기반으로 최적의 만남 장소를 추천합니다.

    Args:
        participants: 참가자 목록. 각 항목은 {"name": "이름", "origin_text": "출발위치"} 형식.
                     예: [{"name": "철수", "origin_text": "강남역"}, {"name": "영희", "origin_text": "홍대입구역"}]
        purpose: 만남 목적. cafe_talk, restaurant, shopping, business, culture, entertainment, study, date 중 선택.
                기본값은 cafe_talk.
        show_map: True로 설정하면 VWorld 지도에 추천 결과를 표시하는 HTML 파일을 생성하고 브라우저에서 엽니다.

    Returns:
        추천 장소 목록과 각 참가자별 이동 시간, 추천 이유를 포함한 결과.
    """
    if len(participants) < 2:
        return "오류: 최소 2명 이상의 참가자가 필요합니다."

    try:
        # 1. 지오코딩
        participant_coords = {}
        for p in participants:
            name = p.get("name", "Unknown")
            origin = p.get("origin_text", "")

            if not origin:
                return f"오류: 참가자 '{name}'의 출발 위치가 지정되지 않았습니다."

            coords = await geocoder.geocode(origin)
            if coords is None:
                return f"오류: '{origin}' 주소를 찾을 수 없습니다."
            participant_coords[name] = coords

        # 2. 후보 장소 생성
        candidates = candidate_generator.generate(list(participant_coords.values()))

        # 3. 각 후보에 대해 ETA 계산 및 점수 계산
        scored_candidates = []
        for candidate in candidates:
            eta_by_participant = {}
            for pname, coords in participant_coords.items():
                eta = estimator.estimate(coords, candidate)
                eta_by_participant[pname] = eta

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

        # 4. 점수 기준 정렬 및 상위 5개 선택
        scored_candidates.sort(key=lambda x: x["total_score"], reverse=True)
        top_candidates = scored_candidates[:5]

        # 5. 결과 텍스트 생성
        result_lines = ["## 추천 만남 장소\n"]

        recommendations_for_map = []

        for rank, item in enumerate(top_candidates, 1):
            candidate = item["candidate"]
            eta_by_participant = item["eta_by_participant"]
            fairness = item["fairness"]

            why = explanation_generator.generate(
                candidate,
                eta_by_participant,
                fairness,
                purpose
            )

            result_lines.append(f"### {rank}위: {candidate['label']}")
            result_lines.append(f"- 위치: ({candidate['lat']:.4f}, {candidate['lng']:.4f})")

            eta_str = ", ".join([f"{name}: {eta}분" for name, eta in eta_by_participant.items()])
            result_lines.append(f"- 예상 이동 시간: {eta_str}")
            result_lines.append(f"- 공정성 (표준편차): {fairness['std']:.1f}분")
            result_lines.append(f"- 평균 이동 시간: {fairness['mean']:.1f}분")
            result_lines.append(f"- 추천 이유: {why}")
            result_lines.append("")

            # 지도용 데이터 저장
            recommendations_for_map.append({
                "label": candidate["label"],
                "lat": candidate["lat"],
                "lng": candidate["lng"],
                "eta_by_participant": eta_by_participant,
                "fairness": fairness,
                "why": why
            })

        # 6. 지도 생성 (옵션)
        if show_map:
            try:
                map_path = map_generator.generate_map_html(
                    recommendations_for_map,
                    participant_coords,
                    open_browser=True
                )
                result_lines.append(f"\n📍 **지도가 브라우저에서 열렸습니다!**")
                result_lines.append(f"파일 위치: {map_path}")
            except Exception as map_error:
                result_lines.append(f"\n⚠️ 지도 생성 중 오류: {str(map_error)}")

        return "\n".join(result_lines)

    except Exception as e:
        return f"오류 발생: {str(e)}"


if __name__ == "__main__":
    mcp.run()
