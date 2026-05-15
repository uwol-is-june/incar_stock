# Tasks

> 포맷: `- [ ] [TASK-NNN] 태스크 이름 — 배경/이유`

## 진행 중

_(없음)_

---

## 예정

- [x] [TASK-011] Vercel Cron으로 정시 주가 수집 트리거 교체 — GitHub Actions scheduler 2~3시간 딜레이 문제 해결
  - **배경**: GitHub Actions `schedule` 트리거가 고부하 시간대에 2~3시간까지 지연되는 공식 한계 존재. KST 16:10 정시 업데이트 필요
  - **작업 1** (`.github/workflows/daily-collect.yml`): `schedule` 트리거 제거, `workflow_dispatch`만 유지 (수동 실행 전용)
  - **작업 2** (`vercel.json`): `crons` 설정 추가 — `path: /api/trigger-collect`, `schedule: "10 7 * * 1-5"` (UTC 07:10 = KST 16:10, 평일)
  - **작업 3** (Vercel 대시보드, 수동): `GITHUB_TOKEN` 환경변수 추가 — Fine-grained PAT (Repository: `uwol-is-june/incar_stock`, Permissions: Actions Read/Write). TASK-010과 공유
  - **비고**: `api/trigger-collect.js` 코드 변경 없음. Vercel Hobby(무료) 플랜 호환

- [x] [TASK-010] 관리자 탭 AI 분석 업데이트 버튼 수정 — Vercel 정적 배포 환경에서 로컬 FastAPI 없어 버튼 404 오류
  - **배경**: "AI 분석 업데이트" 버튼이 `/api/backfill-ai` (로컬 FastAPI)를 호출하는데, Vercel에는 Python 백엔드 없음 → 404. 웹 버튼 → GitHub Actions 경로는 토큰 보호를 위해 Vercel 서버리스 함수를 경유해야 함
  - **작업 1** (`backend/run_backfill_ai.py` 신규): 기존 리포트 전체 AI 강제 재분석 스크립트 (force 모드, market_summary 덮어씀)
  - **작업 2** (`.github/workflows/backfill-ai.yml` 신규): `workflow_dispatch` 트리거 → `run_backfill_ai.py` 실행 → reports/ 커밋·푸시
  - **작업 3** (`api/trigger-ai-update.js` 신규): `api/trigger-collect.js`와 동일 구조, 워크플로우 파일명만 `backfill-ai.yml`로 변경. `GITHUB_TOKEN` Vercel 환경변수 사용 (TASK-011과 공유)
  - **작업 4** (`frontend/index.html` 버튼 핸들러): `/api/backfill-ai` → `/api/trigger-ai-update` 호출로 변경. 성공 시 "GitHub Actions 실행 시작됨, 수 분 후 반영" 메시지 표시
  - **의존**: TASK-011 완료 후 진행 권장 (Vercel `GITHUB_TOKEN` 환경변수 공유)
