# incar_stock

인카금융서비스(211050) 주가 수집 · 대시보드

**배포 URL**: https://incar-stock.vercel.app/

## 주요 기능

- **주가 자동 수집**: pykrx로 KRX 공식 데이터 수집 (OHLCV · 펀더멘털 · 투자자별 동향)
- **4탭 대시보드**: 시세 현황 / 종목 정보 / 투자자 동향 / 주가 차트
- **GitHub Actions 자동화**: 매 거래일 KST 16:10 자동 수집 후 Vercel 자동 재배포
- **DART 연동**: DART OpenAPI로 분기 재무제표 수집, TTM 당기순이익 계산
- **정적 배포**: 백엔드 서버 없이 Vercel에서 정적 파일로 서빙

## 아키텍처

```
[GitHub Actions - 평일 16:10 KST]
        │
        ▼
 run_collect.py
        │
        ├─ collector.py ──pykrx──→ KRX (OHLCV · 펀더멘털 · 투자자 · 지수)
        │               dart-fss→ DART (분기 재무제표)
        │
        └─ reporter.py ──→ reports/YYYY-MM-DD.json
                       ──→ reports/index.json
        │
        ▼ (git push)
[Vercel 자동 재배포] ──→ https://incar-stock.vercel.app/
```

## 기술 스택

| 구분 | 기술 |
|------|------|
| 주가 데이터 | pykrx (KRX 공식) |
| 재무 데이터 | dart-fss (DART OpenAPI) |
| 자동화 | GitHub Actions (cron) |
| 배포 | Vercel (정적 호스팅) |
| 저장소 | JSON 파일 (`reports/YYYY-MM-DD.json`) |
| 프론트엔드 | Vanilla JS + Chart.js |

## 로컬 실행 (개발용)

```bash
pip install -r requirements.txt
# .env에 DART_API_KEY, KRX_ID, KRX_PW 설정
python backend/run_collect.py
```

## 환경 변수

| 변수명 | 설명 | 필수 여부 |
|--------|------|-----------|
| `DART_API_KEY` | DART OpenAPI 인증 키 | 선택 (TTM 당기순이익 활성화) |
| `KRX_ID` | KRX 데이터마켓 계정 ID | 선택 (투자자·외국인 데이터 수집) |
| `KRX_PW` | KRX 데이터마켓 계정 PW | 선택 (투자자·외국인 데이터 수집) |
