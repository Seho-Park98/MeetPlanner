# MeetPlanner MCP — PRD (Claude Code System Generation, VWorld Edition)

본 문서는 **Claude Code를 통해 시스템을 실제 생성·구현**하기 위한 최종 PRD이다.  
아이디어 설명용 문서가 아니라, **코드 생성·배포·검증까지 이어지는 실행 지침서**로 사용된다.

---

## 1. 프로젝트 개요

### 1.1 프로젝트명
MeetPlanner MCP

### 1.2 한 줄 정의
MeetPlanner MCP는 여러 사용자의 출발 위치와 만남 목적을 입력받아,  
대중교통 이동 시간의 공정성과 공간적 목적 적합도를 기준으로  
최적의 만남 장소를 추천하는 MCP 기반 공간 의사결정 시스템이다.

### 1.3 문제 정의
약속 장소 선정은 직관적 협의에 의존하여,
- 실제 이동 시간의 불균형
- 특정 참여자에게 집중되는 이동 부담
- 목적과 장소 특성의 불일치
가 반복적으로 발생한다.

### 1.4 목표
- 이동 시간 **공정성(fairness)** 기반 장소 선택
- 만남 목적 **적합도(intent fit)** 반영
- 결과에 대한 **설명 가능성(explainability)**
- Claude / ChatGPT가 외부 도구로 호출 가능한 **MCP 서버 구현**

---

## 2. 서비스 대상

- 일반 사용자(친구·지인 약속)
- 스터디·프로젝트 모임
- 소규모 오프라인 모임 기획자

---

## 3. 시스템 전체 구조 (MCP 관점)

User → LLM → PlayMCP → MeetPlanner MCP Server → LLM → User

---

## 4. 핵심 기술 선택

### 4.1 지오코딩
- **VWorld Address API**
- request=getcoord
- 좌표계 EPSG:4326

### 4.2 서버 환경
- FastAPI + Python
- Render Web Service
- Base URL: https://meetplanner.onrender.com

---

## 5. 입력 사양

```json
{
  "participants": [
    {"name": "A", "origin_text": "강남역"},
    {"name": "B", "origin_text": "홍대입구"}
  ],
  "purpose": "cafe_talk"
}
```

---

## 6. 처리 로직

### 6.1 지오코딩
- VWorld getcoord 사용
- 실패 시 오류 반환

### 6.2 후보 생성
- centroid + 행정동/주요 지점
- 최대 50개

### 6.3 이동 시간 근사
ETA(min) = (거리_km / 18) * 60 + 8

### 6.4 공정성 / 목적 점수
- std, mean
- 목적별 rule

---

## 7. 출력(JSON)

```json
{
  "recommendations": [
    {
      "rank": 1,
      "label": "공덕역",
      "eta_by_participant": {"A": 35, "B": 33},
      "fairness": {"std": 2.1},
      "purpose": {"score": 120},
      "why": "모두 비슷한 시간에 도착 가능하며 카페가 많은 지역입니다."
    }
  ]
}
```

---

## 8. 비기능 요구사항
- 환경변수 기반 API 키
- 개인정보 비저장
- Render Free 호환

---

## 9. 산출물
- FastAPI 서버
- mcp.json
- README.md
- PRD.md
- COMMAND.md
