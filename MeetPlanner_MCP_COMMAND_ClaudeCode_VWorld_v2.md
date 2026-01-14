# MeetPlanner MCP — COMMAND (Claude Code System Generation, VWorld Edition)

본 문서는 **Claude Code에게 직접 제공되는 시스템 생성 명령서**이다.

---

## 0. 최상위 지시문

당신은 MeetPlanner MCP 서버를 구현하는 개발 에이전트이다.

필수 조건:
1. FastAPI 기반 MCP 서버
2. VWorld getcoord 기반 지오코딩
3. heuristic ETA
4. 공정성 + 목적 적합도 추천
5. 한국어 설명 반환
6. Render 배포 가능

---

## 1. 엔드포인트

- GET /health
- POST /recommend

---

## 2. 내부 모듈

- VWorldGeocoder
- CandidateGenerator
- TransitEstimator
- Scoring
- ExplanationGenerator

---

## 3. 개발 단계

1. FastAPI + /health
2. /recommend 더미
3. VWorldGeocoder
4. 후보 생성
5. ETA + scoring
6. explanation
7. mcp.json + README
8. Render 배포

---

## 4. 제약
- API 키 하드코딩 금지
- 오류 처리 필수
