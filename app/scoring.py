import statistics
from typing import Optional


class Scoring:
    """공정성 및 목적 적합도 점수 계산기"""

    # 목적별 선호 특성 매핑
    PURPOSE_FEATURES = {
        "cafe_talk": ["cafe", "culture"],
        "restaurant": ["restaurant"],
        "shopping": ["shopping"],
        "business": ["business", "cafe"],
        "culture": ["culture"],
        "entertainment": ["entertainment", "shopping"],
        "study": ["cafe", "culture"],
        "date": ["cafe", "restaurant", "culture"],
    }

    # 목적별 기본 점수 (특성 매칭 시 가산)
    FEATURE_SCORE = 20

    def calculate_fairness(self, eta_list: list[int]) -> dict:
        """
        이동 시간 공정성 점수 계산

        Args:
            eta_list: 각 참가자의 예상 이동 시간 리스트

        Returns:
            {"std": float, "mean": float}
        """
        if len(eta_list) < 2:
            return {"std": 0.0, "mean": eta_list[0] if eta_list else 0.0}

        mean_eta = statistics.mean(eta_list)
        std_eta = statistics.stdev(eta_list)

        return {
            "std": round(std_eta, 2),
            "mean": round(mean_eta, 2)
        }

    def calculate_purpose_score(self, candidate: dict, purpose: str) -> float:
        """
        목적 적합도 점수 계산

        Args:
            candidate: 후보 장소 정보
            purpose: 만남 목적

        Returns:
            목적 적합도 점수
        """
        base_score = 100.0
        features = candidate.get("features", [])
        preferred_features = self.PURPOSE_FEATURES.get(purpose, ["cafe", "restaurant"])

        # 선호 특성이 후보 장소에 있으면 가산점
        matching_features = set(features) & set(preferred_features)
        feature_bonus = len(matching_features) * self.FEATURE_SCORE

        return base_score + feature_bonus

    def calculate_total_score(self, fairness: dict, purpose_score: float) -> float:
        """
        종합 점수 계산

        낮은 std(편차)가 좋고, 높은 purpose_score가 좋음

        Args:
            fairness: 공정성 점수 {"std": float, "mean": float}
            purpose_score: 목적 적합도 점수

        Returns:
            종합 점수 (높을수록 좋음)
        """
        # std가 낮을수록 좋으므로 역수 개념 적용
        # std가 0이면 최고 점수
        std_penalty = fairness["std"] * 5  # std 1분당 5점 감점

        # 평균 이동시간이 짧을수록 좋음
        mean_penalty = fairness["mean"] * 0.5  # 평균 1분당 0.5점 감점

        total = purpose_score - std_penalty - mean_penalty

        return round(total, 2)
