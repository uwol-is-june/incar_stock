# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- [TASK-022] AI 분석 탭 마크다운 렌더링 — marked.js CDN 추가, `renderAI()`에서 `marked.parse()` 적용, `.ai-text` 하위 `h3`·`strong`·`ul/li` CSS 스타일 구조화
- [TASK-020] AI 분석 탭 신설 — 주가 차트 탭 우측에 "AI 분석" 탭 추가, market_summary·comment 마크다운 카드 표시
- [TASK-019] Gemini AI 분석 백엔드 연동 — analyzer.py를 Claude(유료)→Gemini 2.5 Flash Lite(무료)로 교체, 투자자·거래량·지수 데이터 프롬프트에 포함
- [TASK-029] `equity`(자본총액) 필드 수집 및 종목 정보 탭 표시 — `BPS × 상장주식수`로 계산, UI에서 조 단위 포맷으로 표시

### Changed
- [TASK-021] AI 종목 분석 코멘트 상세화 — 프롬프트를 5개 항목(가격/등락·투자자·거래량·시장대비·종합) 마크다운 구조로 변경, `max_output_tokens` 1024→2048 상향
- [TASK-029] BPS 수집 방식 변경 — `round(close / PBR)` 역산에서 pykrx `get_market_fundamental()` BPS 컬럼 직접 조회로 전환
- [TASK-029] `_fetch_dart_financials()` → `_fetch_dart_fs()`로 함수 확장 — 재무상태표(BS) `fs['bs']`에서 자본총계 추출 로직 추가 (기존 IS 당기순이익 로직 유지)
- AI 뱃지 워딩 변경 — "Gemini AI" → "AI"

### Fixed
- AI 분석 프롬프트 JSON 파싱 오류 수정 — JSON 템플릿 안에 이스케이프되지 않은 줄바꿈이 포함돼 `json.loads()` 실패하던 문제. JSON 예시를 placeholder로 단순화하고 형식 지시를 블록 밖으로 분리
- [TASK-028] 시총 순위 항상 None 반환 수정 — `_fetch_market_cap_ranking()`이 KOSPI로 조회했으나 WATCHLIST 종목은 KOSDAQ 종목. `market="KOSDAQ"`으로 수정, 프론트엔드 뱃지도 KOSDAQ으로 변경

---

## [0.2.0] - 2026-05-08

### Added
- [TASK-020] APScheduler 자동 수집 — 매 거래일 KST 16:10 cron job, FastAPI lifespan 내 등록
- [TASK-020] 과거 7영업일 자동 백필 — 서버 기동 시 및 generate 완료 후 백그라운드 실행
- [TASK-021] 외국인 소진율 카드 및 progress bar UI 추가 (`exhaustion_rate`, `foreign_pct`)
- [TASK-021] BPS 카드 추가 (`bps = close / pbr` 계산)
- [TASK-022] 당기순이익(TTM) 카드 추가 (`net_income_ttm`)
- [TASK-023] DART API 키 환경변수 추가 (`DART_API_KEY`)
- [TASK-024] DART 분기 재무제표 수집 모듈 구현 (`_fetch_dart_financials`) — Q4=연간-9M 계산 포함
- KOSPI/KOSDAQ 지수 스트립 (대시보드 상단)
- 4탭 대시보드 — 시세현황·종목정보·투자자동향·주가차트
- 투자자별 순매수 동향 (기관·개인·외국인 + 세부 기관 7개)
- Chart.js 주가 라인 차트 + 네이버 10년 주가 차트 이미지
- 시총 순위 카드 UI (`cap_rank`) — 수집은 KRX 인증 문제로 미해결
- OHLCV 상세 필드 수집 (시가·고가·저가·거래량·거래대금·52주고저)

### Changed
- [TASK-017] 종가 배너 개선 — data_date 기준일 표시, is_fallback 뱃지 적용
- [TASK-019] 장중/장마감 수집 정책 확정 — KST 16:00 기준 `_market_closed()`, 장중 is_fallback=True
- API 경로 변경: `POST /api/report/generate` → `POST /api/generate`, `GET /api/report/list` → `GET /api/dates`
- requirements.txt: `uvicorn` → `uvicorn[standard]`, `apscheduler` 추가

### Removed
- [TASK-018] 7일 현황 테이블 행의 "전일" 뱃지 제거 (배너에만 표시)
- DPS 카드 제거

---

## [0.1.0] - 2026-05-07

### Added
- 프로젝트 초기 세팅
- pykrx 기반 OHLCV 수집 + 장중 fallback 처리 (`collector.py`)
- Anthropic Claude API 종목 코멘트·시장 요약 생성 (`analyzer.py`)
- JSON 파일 저장/조회 (`reporter.py`)
- FastAPI 서버 + index.html 대시보드 서빙 (`main.py`)
- 등락률 한국 색상 컨벤션 (상승=빨강, 하락=파랑)
