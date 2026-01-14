import math


class TransitEstimator:
    """대중교통 이동 시간 근사 추정기"""

    # 평균 대중교통 속도 (km/h) - 서울 지하철 평균
    AVG_SPEED_KMH = 18

    # 기본 대기/환승 시간 (분)
    BASE_WAIT_TIME = 8

    def estimate(self, origin: dict, destination: dict) -> int:
        """
        출발지에서 목적지까지의 예상 이동 시간 계산

        PRD 공식: ETA(min) = (거리_km / 18) * 60 + 8

        Args:
            origin: {"lat": float, "lng": float}
            destination: {"lat": float, "lng": float}

        Returns:
            예상 이동 시간 (분, 정수)
        """
        distance_km = self._haversine_distance(
            origin["lat"], origin["lng"],
            destination["lat"], destination["lng"]
        )

        # ETA 계산: (거리 / 속도) * 60 + 기본 대기시간
        eta_minutes = (distance_km / self.AVG_SPEED_KMH) * 60 + self.BASE_WAIT_TIME

        return round(eta_minutes)

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
