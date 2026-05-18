# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

_(없음)_

---

## [0.3.2] - 2026-05-18

### Changed
- [TASK-029] 자동 수집 스케줄러를 Vercel Cron → cron-job.org + GitHub Actions `workflow_dispatch`로 전환 — Vercel Hobby Cron 미작동 문제 해결, KST 16:10 정시 실행 보장
- [TASK-030] 보고서 파일명·`date` 필드를 실행일 기준 → `data_date`(실제 거래일) 기준으로 변경 — 장마감 후 pykrx가 전일 데이터 반환 시 파일명 불일치 해소

### Fixed
- [TASK-028] 모바일에서 PDF 출력 버튼 숨김 — 인쇄 불가 환경 고려
- `generated_at` UTC 표기 오류 수정 → KST(`+09:00`) 명시

### Removed
- Vercel Cron 설정 (`vercel.json` `crons` 블록) 제거
- `api/trigger-collect.js` (Vercel Cron 브리지 엔드포인트) 삭제

---

## [0.3.1] - 2026-05-15

### Changed
- [TASK-024] 주가 차트 OHLC 호버 레이블 한글화 — 툴팁의 O/H/L/C 약어를 시가·고가·저가·종가로 변경, ₩ 단위 표기
- [TASK-025] 거래량 차트 호버 툴팁 단위 추가 — 숫자만 표시되던 거래량 툴팁에 "주" 단위 추가
- [TASK-026] 코스피/코스닥 카드 수직 중앙정렬 — 카드 높이 확장, 지수명→가격→변동(변동률)→미니추세선 순서로 수직 배치

### Removed
- [TASK-027] 기업개요 탭 전체 삭제 — 탭 버튼·패널·renderCompanyInfo·_buildCompanyInfoHtml·관련 CSS 제거

---

## [0.3.0] - 2026-05-15

### Added
- [TASK-019] 코스피·코스닥 지수 카드 미니 추세선 + 글로우 닷 — 15일 SVG 스파크라인 인라인 삽입, 종가 끝점에 `glow-dot-svg` pulse 애니메이션 추가
- [TASK-023] 대시보드 상단 UI 2-tier 위계 구조 개편 — 인카 종가 + AI 한 줄 요약을 Hero 카드로 통합 (상단), 코스피·코스닥을 보조 행으로 재배치 (하단)
- Vercel Cron → GitHub Actions `workflow_dispatch` 자동 트리거 — `vercel.json`에 `10 7 * * 1-5` cron 설정, `/api/trigger-collect` 엔드포인트 추가

### Changed
- [TASK-018] 종가 배너 + AI 종합 의견 레이아웃 통합 — `price-banner` 좌측 컴팩트 묶음 + AI 의견 우측 flex row 배치 (이후 TASK-023에서 Hero 카드로 재편)
- [TASK-020] 지수 카드 Chart.js 긴 추세선 제거 — `sparkline-wrap` 캔버스 삭제, `drawSparkline()` 함수 제거
- [TASK-021] 지수 카드 레이아웃 재배치 — `이름 | 미니추세선·종가 | 변동값+변동률` 순서로 재구성
- [TASK-022] 글로우 닷 위치 이동 — `<span class="glow-dot">` 제거 → SVG `<circle>` (추세선 끝점)으로 이동

### Fixed
- GitHub Actions `schedule:` 트리거 피크 시간대 2~3시간 지연 — `schedule:` 제거 후 Vercel Cron + `workflow_dispatch` 방식으로 전환
- Vercel API 핸들러 GET/POST 버그 — Vercel Cron이 GET 요청을 보내는데 `POST`만 허용하던 405 오류 수정, `CRON_SECRET` 인증으로 대체
- AI 종합의견 정규식 버그 — `comment` 필드에서 "종합 의견" 섹션 추출 실패 수정
- 코스피/코스닥 스파크라인 히스토리 누락 — 히스토리 데이터 미포함 시 graceful fallback 추가

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
- Gemini AI 분석 백엔드 연동 — `analyzer.py`를 Claude(유료)→Gemini 2.5 Flash Lite(무료)로 교체, 투자자·거래량·지수 데이터 프롬프트에 포함
- AI 분석 탭 신설 — 주가 차트 탭 우측에 "AI 분석" 탭 추가, `market_summary`·`comment` 마크다운 카드 표시
- AI 분석 탭 마크다운 렌더링 — marked.js CDN 추가, `renderAI()`에서 `marked.parse()` 적용
- `equity`(자본총액) 필드 수집 및 종목 정보 탭 표시 — `BPS × 상장주식수`로 계산, UI에서 조 단위 포맷으로 표시
- KOSPI/KOSDAQ 지수 스트립 (대시보드 상단)
- 4탭 대시보드 — 시세현황·종목정보·투자자동향·주가차트
- 투자자별 순매수 동향 (기관·개인·외국인 + 세부 기관 7개)
- Chart.js 주가 라인 차트 + 네이버 10년 주가 차트 이미지
- 시총 순위 카드 UI (`cap_rank`) — 수집은 KRX 인증 문제로 미해결
- OHLCV 상세 필드 수집 (시가·고가·저가·거래량·거래대금·52주고저)

### Changed
- 종가 배너 개선 — `data_date` 기준일 표시, `is_fallback` 뱃지 적용
- 장중/장마감 수집 정책 확정 — KST 16:00 기준 `_market_closed()`, 장중 `is_fallback=True`
- AI 종목 분석 코멘트 상세화 — 프롬프트를 5개 항목 마크다운 구조로 변경, `max_output_tokens` 1024→2048 상향
- BPS 수집 방식 변경 — `round(close / PBR)` 역산에서 pykrx `get_market_fundamental()` BPS 컬럼 직접 조회로 전환
- `_fetch_dart_financials()` → `_fetch_dart_fs()`로 함수 확장 — 재무상태표(BS) 자본총계 추출 로직 추가
- AI 뱃지 워딩 변경 — "Gemini AI" → "AI"
- API 경로 변경: `POST /api/report/generate` → `POST /api/generate`, `GET /api/report/list` → `GET /api/dates`
- requirements.txt: `uvicorn` → `uvicorn[standard]`, `apscheduler` 추가

### Fixed
- AI 분석 프롬프트 JSON 파싱 오류 수정 — JSON 예시를 placeholder로 단순화
- 시총 순위 항상 None 반환 수정 — `market="KOSPI"` → `"KOSDAQ"` 수정

### Removed
- 7일 현황 테이블 행의 "전일" 뱃지 제거 (배너에만 표시)
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
