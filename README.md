# incar_stock

> 인카금융서비스(211050) 주가 수집 · Claude 분석 · 대시보드 — C-level 보고용 내부 도구

## 주요 기능

- **주가 자동 수집**: pykrx로 KRX 공식 데이터 수집 (OHLCV + 펀더멘털 + 투자자별 동향)
- **AI 분석**: Anthropic Claude API로 종목 코멘트 및 시장 요약 자동 생성
- **4탭 대시보드**: 시세 현황 / 종목 정보 / 투자자 동향 / 주가 차트
- **자동 스케줄링**: 매 거래일 KST 16:10 자동 수집 + 과거 7영업일 백필
- **DART 연동**: DART OpenAPI로 분기 재무제표 수집, TTM 당기순이익 계산

## 빠른 시작

```bash
pip install -r requirements.txt
# .env에 ANTHROPIC_API_KEY 설정 (DART_API_KEY는 선택)
python backend/main.py
# 브라우저: http://localhost:8000
```

## 기술 스택

| 구분 | 기술 |
|------|------|
| 주가 데이터 | pykrx (KRX 공식) |
| AI 분석 | Anthropic Claude API |
| 재무 데이터 | dart-fss (DART OpenAPI) |
| 웹 프레임워크 | FastAPI + uvicorn |
| 스케줄러 | APScheduler |
| 저장소 | JSON 파일 (reports/YYYY-MM-DD.json) |
| 프론트엔드 | Vanilla JS + Chart.js (인라인 CSS) |

## 문서

| 문서 | 설명 |
|------|------|
| [docs/PLAN.md](docs/PLAN.md) | 프로젝트 기획, 목표, 마일스톤 |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 시스템 설계, 데이터 흐름, JSON 스키마 |
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) | 개발 환경 세팅, API 엔드포인트 |
| [docs/TASK.md](docs/TASK.md) | 현재 진행 중인 태스크 |
| [docs/BACKLOG.md](docs/BACKLOG.md) | 추후 개발 예정 태스크 |
| [docs/CHANGELOG.md](docs/CHANGELOG.md) | 버전별 변경 이력 |
