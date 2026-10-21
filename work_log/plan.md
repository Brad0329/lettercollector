# LetterCollector 전체 계획 (단일 원본)

> PLAN MODE에서 최초 작성/주요 변경 시 갱신. Phase 완료 시 메인 agent가 체크박스 `[x]` + 완료일.
> `Phase_XXX.md`는 실패한 접근·버린 대안이 있을 때만 만든다.

## 시스템 개요
- 汉典书法(`sf.zdic.net`)에서 한자 초서(草書) 이미지를 온디맨드로 검색·수집하여 로컬에 캐싱하고, LLM에 통계 및 시각화(격자 이미지, HTML 갤러리)를 제공하는 MCP 서버.
- 상세 스펙은 `docs/REQUIREMENTS.md` 및 `docs/TOOLS.md`.

## 아키텍처
- **프레임워크**: FastMCP (Official MCP Python SDK 기반)
- **전송 계층(Transport)**: `stdio` (로컬 클라이언트 기본)
- **핵심 구성**:
  - `src/server.py`: FastMCP 서버 초기화 및 엔트리포인트 (stdio 인코딩 강제, stderr 로깅)
  - `src/common/`:
    - `config.py`: 스토리지 경로(`storage/`), 타임아웃, zdic URL 설정
    - `logging.py`: sys.stderr 전용 로거
    - `exceptions.py`: CursiveException 및 CursiveErrorKind (network, badResponse, noResults 등)
    - `aliases.py`: 서예가 한글/간체 매핑 및 zdic 자(字) 별칭 (`赵子昂` -> `赵孟頫` 등)
  - `src/collector/`:
    - `zdic_client.py`: zdic 검색 POST(Content-Length 명시), 302 리다이렉트 추적, 조각 HTML 파싱, GIF 다운로드 및 헤더 검증
    - `storage.py`: 로컬 디렉터리 저장(`storage/<글자>/index.json`, 원본 GIF), 번체/간체 매핑 캐시 조회
    - `visualizer.py`: Pillow 기반 흰색 배경 격자 합성(`grid.png`) 및 브라우저 탐색용 HTML 갤러리(`index.html`) 생성
  - `src/tools/`:
    - `cursive_tools.py`: `find_cursive`, `get_cursive_image` 도구 핸들러
  - `src/resources/`:
    - `cursive_resources.py`: `cursive://list`, `cursive://char/{char}` 리소스 핸들러
  - `tests/`:
    - `test_zdic_parser.py`: zdic HTML 파싱 및 에러 케이스 단위 테스트 (Dart 실측 기반 fixture 활용)
    - `test_storage.py`: 저장 및 캐시 읽기/쓰기 테스트
    - `test_visualizer.py`: 격자 이미지 및 HTML 갤러리 생성 테스트
    - `test_tools.py`: MCP 도구 실행 테스트

## Phase 체크리스트

- [x] Phase 001: 요구사항 정의 및 TOOLS.md 스펙 확정 (2026-10-21)
- [x] Phase 002: Python 환경 셋업 및 공통 모듈 구현 (2026-10-21)
- [x] Phase 003: zdic 수집기 및 로컬 저장소 구현 (2026-10-21)
- [x] Phase 004: 시각화 모듈 및 Core Tools 구현 (2026-10-21)
- [x] Phase 005: Resources 구현 및 MCP 통합 검증 (2026-10-21)
- [x] Phase 006: 문서화 및 최종 패키징 점검 (2026-10-21)

## 결정된 것 / 미정인 것

**확정**
- 출처: `sf.zdic.net` 단일 소스 (`shufazidian.com` 절대 사용 금지)
- 수집 범위: 한 글자의 초서 전부 (단일 페이지 1회 요청)
- 번체/간체 동일 키 매핑 (書와 书 동일 저장소 공유)
- 투명 GIF 특성 보정: 어두운 배경 대비 흰색 바탕 렌더링
- 로깅: stdout 오염 금지 (오직 `sys.stderr`만 사용)
- 에러 처리: `没有搜索到相关的内容`만 0건 결과로 처리, 그 외 파싱 실패는 예외로 드러내어 캐시 오염 원천 차단

**미정**
- 추가 서예가 한글 대응표 확장 (필요 시 점진적 추가)

## 사용자 매뉴얼 및 실테스트 대기
- 실제 zdic 네트워크 1자(예: '永' 또는 '書') 엔드투엔드 수집 및 격자 이미지/갤러리 생성 확인: [x] ('永' 26장 실측 및 grid.png, index.html 확인 완료, 2026-10-21)

