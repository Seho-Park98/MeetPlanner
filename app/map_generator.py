# -*- coding: utf-8 -*-
"""VWorld 지도 HTML 생성기"""

import os
import webbrowser
from datetime import datetime


class MapGenerator:
    """VWorld 지도를 사용해서 추천 결과를 시각화하는 HTML 생성기"""

    def __init__(self):
        self.api_key = os.getenv("VWORLD_API_KEY", "")

    def generate_map_html(
        self,
        recommendations: list[dict],
        participants: dict[str, dict],
        output_path: str = None,
        open_browser: bool = True
    ) -> str:
        """
        추천 결과를 VWorld 지도에 표시하는 HTML 파일 생성

        Args:
            recommendations: 추천 장소 리스트
            participants: 참가자 좌표 딕셔너리 {"이름": {"lat": float, "lng": float}}
            output_path: 출력 파일 경로 (None이면 자동 생성)
            open_browser: 생성 후 브라우저에서 열기

        Returns:
            생성된 HTML 파일 경로
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                f"map_result_{timestamp}.html"
            )

        # 중심점 계산
        all_lats = [r["lat"] for r in recommendations[:5]]
        all_lngs = [r["lng"] for r in recommendations[:5]]
        for coords in participants.values():
            all_lats.append(coords["lat"])
            all_lngs.append(coords["lng"])

        center_lat = sum(all_lats) / len(all_lats)
        center_lng = sum(all_lngs) / len(all_lngs)

        # 마커 데이터 생성
        markers_js = self._generate_markers_js(recommendations, participants)

        html_content = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>MeetPlanner - 추천 장소 지도</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/ol@v7.4.0/ol.css">
    <script src="https://cdn.jsdelivr.net/npm/ol@v7.4.0/dist/ol.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Malgun Gothic', sans-serif; }}
        #map {{ width: 100%; height: 70vh; }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }}
        .header h1 {{ font-size: 24px; margin-bottom: 5px; }}
        .header p {{ font-size: 14px; opacity: 0.9; }}
        .legend {{
            padding: 15px 20px;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
            display: flex;
            gap: 30px;
            flex-wrap: wrap;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
        }}
        .legend-marker {{
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 12px;
            font-weight: bold;
        }}
        .marker-recommend {{ background: #e74c3c; }}
        .marker-participant {{ background: #3498db; }}
        .info-panel {{
            padding: 20px;
            max-height: 30vh;
            overflow-y: auto;
        }}
        .info-panel h2 {{
            font-size: 18px;
            margin-bottom: 15px;
            color: #333;
        }}
        .place-card {{
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 10px;
        }}
        .place-card.rank-1 {{ border-left: 4px solid #e74c3c; }}
        .place-card.rank-2 {{ border-left: 4px solid #e67e22; }}
        .place-card.rank-3 {{ border-left: 4px solid #f1c40f; }}
        .place-header {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 8px;
        }}
        .rank-badge {{
            background: #e74c3c;
            color: white;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: bold;
        }}
        .place-name {{ font-size: 16px; font-weight: bold; color: #333; }}
        .place-info {{ font-size: 13px; color: #666; line-height: 1.6; }}
        .eta-list {{ margin-top: 8px; }}
        .eta-item {{
            display: inline-block;
            background: #e8f4f8;
            padding: 3px 8px;
            border-radius: 4px;
            margin-right: 5px;
            margin-bottom: 5px;
            font-size: 12px;
        }}
        .ol-popup {{
            position: absolute;
            background-color: white;
            box-shadow: 0 1px 4px rgba(0,0,0,0.2);
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #cccccc;
            bottom: 12px;
            left: -50px;
            min-width: 200px;
        }}
        .ol-popup:after, .ol-popup:before {{
            top: 100%;
            border: solid transparent;
            content: " ";
            height: 0;
            width: 0;
            position: absolute;
            pointer-events: none;
        }}
        .ol-popup:after {{
            border-top-color: white;
            border-width: 10px;
            left: 48px;
            margin-left: -10px;
        }}
        .ol-popup:before {{
            border-top-color: #cccccc;
            border-width: 11px;
            left: 48px;
            margin-left: -11px;
        }}
        .ol-popup-closer {{
            text-decoration: none;
            position: absolute;
            top: 2px;
            right: 8px;
        }}
        .ol-popup-closer:after {{
            content: "✖";
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>MeetPlanner 추천 결과</h1>
        <p>VWorld 지도에서 추천 장소를 확인하세요</p>
    </div>

    <div class="legend">
        <div class="legend-item">
            <div class="legend-marker marker-recommend">1</div>
            <span>추천 장소 (숫자 = 순위)</span>
        </div>
        <div class="legend-item">
            <div class="legend-marker marker-participant">P</div>
            <span>참가자 출발 위치</span>
        </div>
    </div>

    <div id="map"></div>

    <div id="popup" class="ol-popup">
        <a href="#" id="popup-closer" class="ol-popup-closer"></a>
        <div id="popup-content"></div>
    </div>

    <div class="info-panel">
        <h2>추천 장소 상세</h2>
        {self._generate_place_cards_html(recommendations)}
    </div>

    <script>
        // VWorld 타일 레이어
        var vworldLayer = new ol.layer.Tile({{
            source: new ol.source.XYZ({{
                url: 'https://api.vworld.kr/req/wmts/1.0.0/{self.api_key}/Base/{{z}}/{{y}}/{{x}}.png'
            }})
        }});

        // 지도 생성
        var map = new ol.Map({{
            target: 'map',
            layers: [vworldLayer],
            view: new ol.View({{
                center: ol.proj.fromLonLat([{center_lng}, {center_lat}]),
                zoom: 12
            }})
        }});

        // 팝업 설정
        var container = document.getElementById('popup');
        var content = document.getElementById('popup-content');
        var closer = document.getElementById('popup-closer');

        var overlay = new ol.Overlay({{
            element: container,
            autoPan: true,
            autoPanAnimation: {{
                duration: 250
            }}
        }});
        map.addOverlay(overlay);

        closer.onclick = function() {{
            overlay.setPosition(undefined);
            closer.blur();
            return false;
        }};

        // 마커 생성 함수
        function createMarker(lon, lat, label, color, isRank) {{
            var feature = new ol.Feature({{
                geometry: new ol.geom.Point(ol.proj.fromLonLat([lon, lat])),
                name: label
            }});

            // SVG 마커 스타일
            var svg = '<svg width="32" height="40" xmlns="http://www.w3.org/2000/svg">' +
                '<path d="M16 0C7.163 0 0 7.163 0 16c0 12 16 24 16 24s16-12 16-24C32 7.163 24.837 0 16 0z" fill="' + color + '"/>' +
                '<circle cx="16" cy="14" r="8" fill="white"/>' +
                '<text x="16" y="18" text-anchor="middle" font-size="10" font-weight="bold" fill="' + color + '">' + (isRank ? label : 'P') + '</text>' +
                '</svg>';

            var style = new ol.style.Style({{
                image: new ol.style.Icon({{
                    src: 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg),
                    anchor: [0.5, 1],
                    scale: 1
                }})
            }});

            feature.setStyle(style);
            return feature;
        }}

        // 마커 추가
        var features = [];

        {markers_js}

        // 벡터 레이어 생성
        var vectorSource = new ol.source.Vector({{
            features: features
        }});

        var vectorLayer = new ol.layer.Vector({{
            source: vectorSource
        }});

        map.addLayer(vectorLayer);

        // 클릭 이벤트
        map.on('click', function(evt) {{
            var feature = map.forEachFeatureAtPixel(evt.pixel, function(feature) {{
                return feature;
            }});
            if (feature) {{
                var coordinates = feature.getGeometry().getCoordinates();
                content.innerHTML = '<strong>' + feature.get('name') + '</strong>';
                overlay.setPosition(coordinates);
            }} else {{
                overlay.setPosition(undefined);
            }}
        }});

        // 커서 변경
        map.on('pointermove', function(e) {{
            var pixel = map.getEventPixel(e.originalEvent);
            var hit = map.hasFeatureAtPixel(pixel);
            map.getTarget().style.cursor = hit ? 'pointer' : '';
        }});
    </script>
</body>
</html>'''

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        if open_browser:
            webbrowser.open(f'file://{os.path.abspath(output_path)}')

        return output_path

    def _generate_markers_js(self, recommendations: list[dict], participants: dict[str, dict]) -> str:
        """마커 JavaScript 코드 생성"""
        js_lines = []

        # 추천 장소 마커 (빨간색, 숫자)
        for i, rec in enumerate(recommendations[:5], 1):
            js_lines.append(
                f"features.push(createMarker({rec['lng']}, {rec['lat']}, '{i}', '#e74c3c', true));  // {rec['label']}"
            )

        # 참가자 출발 위치 마커 (파란색)
        for name, coords in participants.items():
            js_lines.append(
                f"features.push(createMarker({coords['lng']}, {coords['lat']}, '{name}', '#3498db', false));"
            )

        return '\n        '.join(js_lines)

    def _generate_place_cards_html(self, recommendations: list[dict]) -> str:
        """장소 카드 HTML 생성"""
        cards = []
        for i, rec in enumerate(recommendations[:5], 1):
            eta_items = ''.join([
                f'<span class="eta-item">{name}: {eta}분</span>'
                for name, eta in rec.get("eta_by_participant", {}).items()
            ])

            cards.append(f'''
        <div class="place-card rank-{i}">
            <div class="place-header">
                <div class="rank-badge">{i}</div>
                <span class="place-name">{rec["label"]}</span>
            </div>
            <div class="place-info">
                <div>평균 이동시간: {rec.get("fairness", {}).get("mean", 0):.0f}분 | 표준편차: {rec.get("fairness", {}).get("std", 0):.1f}분</div>
                <div class="eta-list">{eta_items}</div>
                <div style="margin-top: 8px; color: #555;">{rec.get("why", "")}</div>
            </div>
        </div>''')

        return '\n'.join(cards)
