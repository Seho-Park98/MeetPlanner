import os
import httpx
from typing import Optional


class VWorldGeocoder:
    """VWorld Address API를 사용한 지오코더"""

    BASE_URL = "https://api.vworld.kr/req/address"

    def __init__(self):
        self.api_key = os.getenv("VWORLD_API_KEY")
        if not self.api_key:
            print("경고: VWORLD_API_KEY 환경변수가 설정되지 않았습니다. /recommend 엔드포인트가 작동하지 않을 수 있습니다.")

    async def geocode(self, address: str) -> Optional[dict]:
        """
        주소를 좌표로 변환

        Args:
            address: 검색할 주소 또는 장소명 (예: "강남역", "서울시 강남구")

        Returns:
            {"lat": float, "lng": float} 또는 None
        """
        if not self.api_key:
            raise ValueError("VWORLD_API_KEY 환경변수가 설정되지 않았습니다.")

        params = {
            "service": "address",
            "request": "getcoord",
            "version": "2.0",
            "crs": "epsg:4326",
            "address": address,
            "refine": "true",
            "simple": "false",
            "format": "json",
            "type": "road",
            "key": self.api_key
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()

                # VWorld API 응답 구조 확인
                if data.get("response", {}).get("status") == "OK":
                    result = data["response"]["result"]
                    if result and result.get("point"):
                        point = result["point"]
                        return {
                            "lat": float(point["y"]),
                            "lng": float(point["x"])
                        }

                # road 타입 실패시 parcel 타입으로 재시도
                params["type"] = "parcel"
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()

                if data.get("response", {}).get("status") == "OK":
                    result = data["response"]["result"]
                    if result and result.get("point"):
                        point = result["point"]
                        return {
                            "lat": float(point["y"]),
                            "lng": float(point["x"])
                        }

                # 주소 API 실패시 POI 검색으로 시도 (장소명 검색)
                return await self._search_poi(address)

            except Exception as e:
                print(f"Geocoding error for '{address}': {e}")
                return None

    async def _search_poi(self, query: str) -> Optional[dict]:
        """POI(관심 지점) 검색을 통한 좌표 반환"""
        search_url = "https://api.vworld.kr/req/search"
        params = {
            "service": "search",
            "request": "search",
            "version": "2.0",
            "crs": "epsg:4326",
            "size": "1",
            "page": "1",
            "query": query,
            "type": "place",
            "format": "json",
            "key": self.api_key
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(search_url, params=params)
                response.raise_for_status()
                data = response.json()

                if data.get("response", {}).get("status") == "OK":
                    items = data["response"].get("result", {}).get("items", [])
                    if items:
                        point = items[0].get("point", {})
                        if point:
                            return {
                                "lat": float(point["y"]),
                                "lng": float(point["x"])
                            }
                return None
            except Exception as e:
                print(f"POI search error for '{query}': {e}")
                return None
