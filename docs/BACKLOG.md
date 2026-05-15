# Backlog

> 포맷: `- [ ] [BACK-NNN] 태스크 이름 — 배경/이유`
> TASK.md로 이동할 때 번호를 TASK-NNN으로 재부여

---

## High Priority

_(없음)_

---

## Medium Priority

- [ ] [BACK-001] 종가 배너 + AI 종합 의견 레이아웃 통합 — 현재 price-banner(종목명 좌·종가 우)가 `justify-content: space-between`으로 너무 벌어져 가독성이 나쁘고, ai-opinion-strip이 별도 줄로 분리돼 있어 정보 밀도가 낮음. price-banner 좌측에 [종목명+날짜+종가+등락]을 컴팩트하게 묶고, 우측에 AI 종합 의견 텍스트를 같은 행(flex row)에 배치해 한눈에 파악할 수 있도록 개선.
  - 작업 목록
    - price-banner 내부 레이아웃: 좌측 블록에 종목명·날짜·종가·등락을 모아 컴팩트하게 (space-between 제거)
    - ai-opinion-strip을 price-banner와 같은 flex 컨테이너로 합치거나, 우측 영역으로 이동
    - 반응형: 모바일에서는 세로 배치 유지
    - 인쇄(print) CSS 호환 확인

---

## Low Priority / 아이디어

_(없음)_
