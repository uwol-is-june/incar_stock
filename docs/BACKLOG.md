# Backlog

> 포맷: `- [ ] [BACK-NNN] 태스크 이름 — 배경/이유`
> TASK.md로 이동할 때 번호를 TASK-NNN으로 재부여

---

## High Priority

_(없음)_

---

## Medium Priority

_(없음)_

---

## Low Priority / 아이디어

- [ ] [BACK-010] Vercel에서 AI 분석 업데이트 버튼 동작 — 현재 Vercel 정적 배포에서 Python API 없어 버튼 실패. GitHub Actions workflow_dispatch로 대체
  - **배경**: 관리자 탭 "AI 분석 업데이트" 버튼이 `/api/backfill-ai`(로컬 FastAPI)를 호출하는데, Vercel에는 Python 백엔드 없음 → 404 → "업데이트 실패"
  - **작업 1** (`backend/run_backfill_ai.py` 신규): 기존 리포트 전체 AI 강제 재분석 스크립트 (force 모드, market_summary 덮어씀)
  - **작업 2** (`.github/workflows/backfill-ai.yml` 신규): `workflow_dispatch` 트리거 → `run_backfill_ai.py` 실행 → reports/ 커밋·푸시. `secrets.GEMINI_API_KEY` 사용 (이미 daily-collect에서 사용 중)
  - **작업 3** (`api/trigger-ai-update.js` 신규): Vercel 서버리스 함수. GitHub API 호출해 `backfill-ai.yml` 워크플로우 dispatch. `GITHUB_PAT`, `GITHUB_OWNER`, `GITHUB_REPO` Vercel 환경변수에서 읽음
  - **작업 4** (`frontend/index.html` 버튼 핸들러): `/api/backfill-ai` → `/api/trigger-ai-update` 호출로 변경. 성공 시 "GitHub Actions 실행 시작됨, 수 분 후 반영" 메시지
  - **사전 조건**: Vercel 대시보드에 환경변수 3개 추가 필요 (`GITHUB_PAT`: Actions Read/Write 권한 Fine-grained PAT, `GITHUB_OWNER`, `GITHUB_REPO`)

- [ ] [BACK-007] incar_logo 헤더 적용 — `img/incar_logo.png` 준비 완료, 헤더 `.header-left`에 `<img>` 태그로 삽입 (상대경로 `../img/incar_logo.png`), CSS height 조정 및 다크 배경 대응
