# incar_stock

## 프로젝트 한줄 요약
인카금융서비스(211050) 주가를 pykrx로 수집 → JSON 저장 → Vercel 정적 배포 → HTML 대시보드.

## 지금 할 일
→ [TASK.md](TASK.md) 참조

## 아키텍처
→ [ARCHITECTURE.md](ARCHITECTURE.md) 참조

## 코딩 규칙
- 언어: Python 3.10+
- 커밋: feat / fix / docs / refactor / chore 타입 prefix
- 등락 색상 컨벤션: 상승=빨강, 하락=파랑 (한국 증시 기준)
- 장중/장마감 기준: KST 16:00 (is_fallback 플래그로 구분)
- 투자자 데이터: 장 마감 후에만 확정 제공됨
- reports/ 보관: 최신 5개 파일만 유지 (prune)

## 배포 URL
https://incar-stock.vercel.app/
