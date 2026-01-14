# MeetPlanner MCP

여러 사용자의 출발 위치와 만남 목적을 입력받아, 대중교통 이동 시간의 공정성과 공간적 목적 적합도를 기준으로 최적의 만남 장소를 추천하는 MCP 기반 공간 의사결정 시스템입니다.

## 주요 기능

- **이동 시간 공정성(Fairness)**: 모든 참가자가 비슷한 시간 내에 도착할 수 있는 장소 추천
- **목적 적합도(Intent Fit)**: 만남 목적에 맞는 장소 특성 고려
- **설명 가능성(Explainability)**: 추천 결과에 대한 한국어 설명 제공
- **MCP 호환**: Claude / ChatGPT에서 외부 도구로 호출 가능

## 설치 및 실행

### 1. 환경 설정

```bash
# Conda 환경 생성
conda create -n PlayMCP python=3.11 -y
conda activate PlayMCP

# 패키지 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일을 생성하고 VWorld API 키를 설정합니다:

```
VWORLD_API_KEY=your_vworld_api_key_here
```

VWorld API 키는 [VWorld 오픈API](https://www.vworld.kr/dev/v4api.do)에서 발급받을 수 있습니다.

### 3. 서버 실행

```bash
# 개발 모드
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 프로덕션 모드
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API 엔드포인트

### GET /health

서버 상태 확인

**응답 예시:**
```json
{
  "status": "ok",
  "service": "MeetPlanner MCP"
}
```

### POST /recommend

만남 장소 추천 요청

**요청 예시:**
```json
{
  "participants": [
    {"name": "A", "origin_text": "강남역"},
    {"name": "B", "origin_text": "홍대입구역"}
  ],
  "purpose": "cafe_talk"
}
```

**응답 예시:**
```json
{
  "recommendations": [
    {
      "rank": 1,
      "label": "공덕역",
      "lat": 37.5441,
      "lng": 126.9516,
      "eta_by_participant": {"A": 35, "B": 33},
      "fairness": {"std": 1.41, "mean": 34.0},
      "purpose": {"score": 140.0},
      "why": "모든 참가자가 비슷한 시간에 도착할 수 있습니다. 평균 약 34분이면 도착 가능합니다. 카페가 많은 지역입니다. 카페에서 대화하기에 좋은 장소입니다."
    }
  ]
}
```

## 지원하는 목적(Purpose)

| 목적 | 설명 |
|------|------|
| `cafe_talk` | 카페에서 대화하기 (기본값) |
| `restaurant` | 식사하기 |
| `shopping` | 쇼핑하기 |
| `business` | 업무 미팅 |
| `culture` | 문화 활동 |
| `entertainment` | 오락/여가 |
| `study` | 스터디/공부 |
| `date` | 데이트 |

## 기술 스택

- **Backend**: FastAPI + Python 3.11
- **Geocoding**: VWorld Address API
- **Deployment**: Render Web Service

## 알고리즘

### ETA 계산
```
ETA(분) = (거리_km / 18) * 60 + 8
```
- 평균 대중교통 속도: 18 km/h
- 기본 대기/환승 시간: 8분

### 점수 계산
- **공정성 점수**: 이동 시간 표준편차(std)와 평균(mean) 기반
- **목적 적합도**: 장소 특성과 목적 매칭 점수
- **종합 점수**: 목적 적합도 - (std * 5) - (mean * 0.5)

## Render 배포

1. Render에서 새 Web Service 생성
2. 저장소 연결
3. 환경 변수 설정:
   - `VWORLD_API_KEY`: VWorld API 키
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

## 라이선스

MIT License
