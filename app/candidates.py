import math
from typing import Optional


class CandidateGenerator:
    """중심점 기반 후보 장소 생성기"""

    # 서울 주요 지하철역 및 만남 장소 데이터
    MAJOR_LOCATIONS = [
        {"label": "강남역", "lat": 37.4979, "lng": 127.0276, "type": "station", "features": ["cafe", "restaurant", "shopping"]},
        {"label": "홍대입구역", "lat": 37.5571, "lng": 126.9244, "type": "station", "features": ["cafe", "restaurant", "culture"]},
        {"label": "신촌역", "lat": 37.5551, "lng": 126.9368, "type": "station", "features": ["cafe", "restaurant", "culture"]},
        {"label": "합정역", "lat": 37.5495, "lng": 126.9139, "type": "station", "features": ["cafe", "restaurant", "culture"]},
        {"label": "잠실역", "lat": 37.5132, "lng": 127.1001, "type": "station", "features": ["shopping", "entertainment", "restaurant"]},
        {"label": "건대입구역", "lat": 37.5403, "lng": 127.0694, "type": "station", "features": ["cafe", "restaurant", "shopping"]},
        {"label": "왕십리역", "lat": 37.5615, "lng": 127.0378, "type": "station", "features": ["shopping", "restaurant"]},
        {"label": "서울역", "lat": 37.5547, "lng": 126.9707, "type": "station", "features": ["restaurant", "shopping"]},
        {"label": "시청역", "lat": 37.5654, "lng": 126.9778, "type": "station", "features": ["restaurant", "culture"]},
        {"label": "을지로입구역", "lat": 37.5660, "lng": 126.9824, "type": "station", "features": ["restaurant", "shopping"]},
        {"label": "종각역", "lat": 37.5700, "lng": 126.9828, "type": "station", "features": ["cafe", "restaurant", "culture"]},
        {"label": "광화문역", "lat": 37.5710, "lng": 126.9768, "type": "station", "features": ["culture", "restaurant"]},
        {"label": "명동역", "lat": 37.5609, "lng": 126.9860, "type": "station", "features": ["shopping", "restaurant", "cafe"]},
        {"label": "동대문역", "lat": 37.5713, "lng": 127.0095, "type": "station", "features": ["shopping", "restaurant"]},
        {"label": "성수역", "lat": 37.5446, "lng": 127.0557, "type": "station", "features": ["cafe", "culture"]},
        {"label": "삼성역", "lat": 37.5089, "lng": 127.0634, "type": "station", "features": ["shopping", "restaurant", "business"]},
        {"label": "선릉역", "lat": 37.5045, "lng": 127.0490, "type": "station", "features": ["cafe", "restaurant", "business"]},
        {"label": "역삼역", "lat": 37.5007, "lng": 127.0365, "type": "station", "features": ["cafe", "restaurant", "business"]},
        {"label": "교대역", "lat": 37.4934, "lng": 127.0145, "type": "station", "features": ["cafe", "restaurant"]},
        {"label": "사당역", "lat": 37.4766, "lng": 126.9816, "type": "station", "features": ["cafe", "restaurant"]},
        {"label": "이태원역", "lat": 37.5345, "lng": 126.9947, "type": "station", "features": ["restaurant", "culture", "cafe"]},
        {"label": "압구정역", "lat": 37.5273, "lng": 127.0283, "type": "station", "features": ["cafe", "shopping", "restaurant"]},
        {"label": "청담역", "lat": 37.5193, "lng": 127.0533, "type": "station", "features": ["cafe", "shopping", "restaurant"]},
        {"label": "여의도역", "lat": 37.5216, "lng": 126.9244, "type": "station", "features": ["restaurant", "business"]},
        {"label": "당산역", "lat": 37.5347, "lng": 126.9027, "type": "station", "features": ["cafe", "restaurant"]},
        {"label": "영등포구청역", "lat": 37.5253, "lng": 126.8965, "type": "station", "features": ["restaurant", "shopping"]},
        {"label": "노량진역", "lat": 37.5134, "lng": 126.9423, "type": "station", "features": ["restaurant", "cafe"]},
        {"label": "신림역", "lat": 37.4842, "lng": 126.9296, "type": "station", "features": ["cafe", "restaurant"]},
        {"label": "대림역", "lat": 37.4930, "lng": 126.8975, "type": "station", "features": ["restaurant"]},
        {"label": "구로디지털단지역", "lat": 37.4852, "lng": 126.9016, "type": "station", "features": ["cafe", "restaurant", "business"]},
        {"label": "신도림역", "lat": 37.5089, "lng": 126.8913, "type": "station", "features": ["shopping", "restaurant"]},
        {"label": "고속터미널역", "lat": 37.5049, "lng": 127.0050, "type": "station", "features": ["shopping", "restaurant"]},
        {"label": "강변역", "lat": 37.5352, "lng": 127.0944, "type": "station", "features": ["shopping", "entertainment"]},
        {"label": "뚝섬역", "lat": 37.5474, "lng": 127.0474, "type": "station", "features": ["cafe", "culture"]},
        {"label": "공덕역", "lat": 37.5441, "lng": 126.9516, "type": "station", "features": ["cafe", "restaurant"]},
        {"label": "마포역", "lat": 37.5397, "lng": 126.9459, "type": "station", "features": ["restaurant"]},
        {"label": "망원역", "lat": 37.5560, "lng": 126.9103, "type": "station", "features": ["cafe", "culture"]},
        {"label": "상수역", "lat": 37.5478, "lng": 126.9227, "type": "station", "features": ["cafe", "culture"]},
        {"label": "이수역", "lat": 37.4856, "lng": 126.9820, "type": "station", "features": ["cafe", "restaurant"]},
        {"label": "낙성대역", "lat": 37.4768, "lng": 126.9637, "type": "station", "features": ["cafe", "restaurant"]},
        {"label": "서울대입구역", "lat": 37.4813, "lng": 126.9528, "type": "station", "features": ["cafe", "restaurant"]},
        {"label": "봉천역", "lat": 37.4827, "lng": 126.9416, "type": "station", "features": ["restaurant"]},
        {"label": "신대방역", "lat": 37.4875, "lng": 126.9132, "type": "station", "features": ["restaurant"]},
        {"label": "보라매역", "lat": 37.4943, "lng": 126.9198, "type": "station", "features": ["cafe", "restaurant"]},
        {"label": "동작역", "lat": 37.5076, "lng": 126.9510, "type": "station", "features": ["restaurant"]},
        {"label": "총신대입구역", "lat": 37.4869, "lng": 126.9821, "type": "station", "features": ["restaurant"]},
        {"label": "남부터미널역", "lat": 37.4849, "lng": 127.0145, "type": "station", "features": ["restaurant"]},
        {"label": "양재역", "lat": 37.4841, "lng": 127.0343, "type": "station", "features": ["cafe", "restaurant", "business"]},
        {"label": "매봉역", "lat": 37.4869, "lng": 127.0465, "type": "station", "features": ["restaurant"]},
        {"label": "도곡역", "lat": 37.4914, "lng": 127.0547, "type": "station", "features": ["cafe", "restaurant"]},
    ]

    def generate(self, participant_coords: list[dict], max_candidates: int = 50) -> list[dict]:
        """
        참가자들의 위치를 기반으로 후보 장소 생성

        Args:
            participant_coords: [{"lat": float, "lng": float}, ...]
            max_candidates: 최대 후보 수

        Returns:
            후보 장소 리스트
        """
        if not participant_coords:
            return []

        # 중심점 계산
        centroid = self._calculate_centroid(participant_coords)

        # 중심점에서 각 후보까지의 거리 계산 후 정렬
        candidates_with_distance = []
        for loc in self.MAJOR_LOCATIONS:
            distance = self._haversine_distance(
                centroid["lat"], centroid["lng"],
                loc["lat"], loc["lng"]
            )
            candidates_with_distance.append({
                **loc,
                "distance_from_centroid": distance
            })

        # 거리 기준 정렬
        candidates_with_distance.sort(key=lambda x: x["distance_from_centroid"])

        return candidates_with_distance[:max_candidates]

    def _calculate_centroid(self, coords: list[dict]) -> dict:
        """좌표들의 중심점 계산"""
        avg_lat = sum(c["lat"] for c in coords) / len(coords)
        avg_lng = sum(c["lng"] for c in coords) / len(coords)
        return {"lat": avg_lat, "lng": avg_lng}

    def _haversine_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """두 좌표 간의 거리 계산 (km)"""
        R = 6371  # 지구 반경 (km)

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)

        a = math.sin(delta_lat / 2) ** 2 + \
            math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c
