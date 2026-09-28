# LG전자 DART Financial Analysis

[![🔗 대시보드 바로가기](https://img.shields.io/badge/대시보드-바로가기-8CCFFF?style=for-the-badge)](https://YOUR_GITHUB_USERNAME.github.io/YOUR_REPOSITORY/)

LG전자(066570)의 DART 사업보고서·반기보고서·분기보고서 및 연결 재무제표를 2010년부터 수집하고 주요 수치와 재무비율을 분석합니다.

## 설치 및 실행
1. https://opendart.fss.or.kr/ 에서 Open DART 인증키 발급
2. GitHub 저장소 Settings → Secrets and variables → Actions → New repository secret
3. Name `DART_API_KEY`, Value에 발급받은 API 키 저장 (코드에 직접 입력하지 마세요)
4. Actions → Monthly DART update → Run workflow로 최초 실행
5. Settings → Pages → Deploy from a branch → `main` / `/docs` 선택
6. README 배지 URL의 `YOUR_GITHUB_USERNAME`과 `YOUR_REPOSITORY`를 실제 저장소에 맞게 변경
7. 저장소 우측 About의 톱니바퀴 → Website에 GitHub Pages 주소 입력

## 자동 업데이트
매월 1일 00:17 UTC (한국시간 09:17)에 GitHub Actions가 실행됩니다. GitHub 예약 실행은 시스템 사정으로 지연될 수 있습니다.

## 생성 파일
- `data/raw/reports/`: DART 문서 ZIP (API 제공 성공 시)
- `data/raw/<접수번호>.json`: 원본 재무제표 API 응답
- `data/processed/filings.csv`: 수집 공시 목록
- `data/processed/financial_facts.csv`: 계정별 원자료
- `data/processed/dashboard_metrics.csv`: 주요 수치 및 계산 비율
- `docs/index.html`: GitHub Pages 대시보드

## 주요 지표
매출액, 매출원가, 매출총이익, 영업이익, 당기순이익, 자산·부채·자본, 유동자산·유동부채, 영업활동현금흐름, 매출총이익률, 영업이익률, 순이익률, 유동비율, 부채비율, 자기자본비율.

## 국내 Peer Firms (참고)
| 기업 | 종목코드 | 비교 범위 |
|---|---:|---|
| 삼성전자 | 005930 | 가전·전자 종합기업 |
| 삼성전기 | 009150 | 전자부품 |
| 위닉스 | 044340 | 생활가전 일부 제품군 |

현재 자동 수집 대상은 LG전자입니다. Peer 기업 수치는 별도 수집 로직을 추가해야 합니다.

## 데이터 주의사항
- DART 전체 재무제표 API의 연도별 제공 범위·계정 체계에 차이가 있어 2010~2014년 데이터는 원문 보고서 보완이 필요할 수 있습니다. OpenDART의 재무제표 API 설명은 2015년 이후 제공으로 안내합니다.
- 분기/반기 손익 항목은 누적 금액일 수 있어 분기 단독 비교 시 기간 차분 검증이 필요합니다.
- GitHub Actions workflow 파일은 숨김 경로 `.github/workflows`에 있어야 자동 실행됩니다. ZIP에는 필요한 숨김 파일을 포함했고 `.DS_Store`, `__MACOSX`는 포함하지 않았습니다.
