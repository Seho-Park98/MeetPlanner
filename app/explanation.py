class ExplanationGenerator:
    """추천 결과에 대한 한국어 설명 생성기"""

    PURPOSE_DESCRIPTIONS = {
        "cafe_talk": "카페에서 대화하기",
        "restaurant": "식사하기",
        "shopping": "쇼핑하기",
        "business": "업무 미팅",
        "culture": "문화 활동",
        "entertainment": "오락/여가",
        "study": "스터디/공부",
        "date": "데이트",
    }

    FEATURE_DESCRIPTIONS = {
        "cafe": "카페가 많은",
        "restaurant": "맛집이 많은",
        "shopping": "쇼핑 시설이 좋은",
        "business": "비즈니스 미팅에 적합한",
        "culture": "문화 시설이 있는",
        "entertainment": "놀거리가 많은",
    }

    def generate(
        self,
        candidate: dict,
        eta_by_participant: dict[str, int],
        fairness: dict,
        purpose: str
    ) -> str:
        """
        추천 결과에 대한 설명 생성

        Args:
            candidate: 후보 장소 정보
            eta_by_participant: 참가자별 예상 이동 시간
            fairness: 공정성 점수
            purpose: 만남 목적

        Returns:
            한국어 설명 문자열
        """
        parts = []

        # 이동 시간 공정성 설명
        std = fairness["std"]
        mean = fairness["mean"]

        if std < 3:
            parts.append("모든 참가자가 비슷한 시간에 도착할 수 있습니다")
        elif std < 7:
            parts.append("참가자들의 이동 시간 차이가 적당합니다")
        else:
            parts.append("이동 시간에 다소 차이가 있지만 접근성이 좋습니다")

        # 평균 이동 시간 언급
        if mean < 20:
            parts.append(f"평균 약 {round(mean)}분이면 도착 가능합니다")
        elif mean < 35:
            parts.append(f"평균 약 {round(mean)}분 정도 소요됩니다")
        else:
            parts.append(f"평균 약 {round(mean)}분 정도 걸리지만 모두에게 공정한 위치입니다")

        # 장소 특성 설명
        features = candidate.get("features", [])
        feature_desc = []
        for f in features[:2]:  # 최대 2개만
            if f in self.FEATURE_DESCRIPTIONS:
                feature_desc.append(self.FEATURE_DESCRIPTIONS[f])

        if feature_desc:
            parts.append(f"{', '.join(feature_desc)} 지역입니다")

        # 목적 적합성 언급
        purpose_desc = self.PURPOSE_DESCRIPTIONS.get(purpose, "만남")
        if any(f in features for f in self._get_purpose_features(purpose)):
            parts.append(f"{purpose_desc}에 좋은 장소입니다")

        return ". ".join(parts) + "."

    def _get_purpose_features(self, purpose: str) -> list[str]:
        """목적에 해당하는 특성 목록 반환"""
        mapping = {
            "cafe_talk": ["cafe", "culture"],
            "restaurant": ["restaurant"],
            "shopping": ["shopping"],
            "business": ["business", "cafe"],
            "culture": ["culture"],
            "entertainment": ["entertainment", "shopping"],
            "study": ["cafe", "culture"],
            "date": ["cafe", "restaurant", "culture"],
        }
        return mapping.get(purpose, ["cafe", "restaurant"])
