# LetterCollector — 한자 초서(草書) 이미지 검색/수집/캐싱 MCP 서버

Model Context Protocol (MCP) 기반 Python 서버.
LLM(Antigravity, Claude Desktop, Cursor 등)에 Tools · Resources를 제공하여
汉典书法(sf.zdic.net)의 한자 초서 이미지를 온디맨드로 수집, 로컬 캐싱 및 조회할 수 있게 함.

## 현재 단계
- 전체 Phase 체크리스트/도구 구조의 **단일 원본 = `work_log/plan.md`** (중복 기재 금지)
- 현재: **Phase 006 완료 — 모든 구현 및 검증 완료** (2026-10-21)

## 새 세션 시작 시
1. **이 파일(AGENTS.md)을 읽는다** — 매 세션의 규칙 기준.
2. `work_log/plan.md` — 전체 현황, 구현된 Tool 목록, 현재 Phase
3. 진행 중 Phase의 `work_log/Phase_XXX.md`(있으면) — 이전 결정과 실패 경험
4. 필요하면 서브에이전트를 재정의한다 — `agents/*.md`의 prompt로 `define_subagent` 호출.

## 요구사항 정책 ★"도구 스펙"이 명확해야 LLM이 올바르게 쓴다
- 기능 요구사항 + 수용 기준의 **단일 원본 = `docs/REQUIREMENTS.md`**
- **구현 전**: 도구(Tool) 입력 인자, 출력 형식, 에러 처리 기준이 먼저 정해져야 한다.
- **수용 기준은 검증 가능한 문장으로** — 그대로 pytest 테스트 케이스가 된다.
- **YAGNI**: 스펙에 없는 과도한 옵션/파라미터 추상화 금지.
- **요구사항 ID 대장**: `T-001`(Tool), `R-001`(Resource), `P-001`(Prompt) 단위로 관리.

## 도구(Tool) 스펙 및 스키마 변경 게이트 ★시그니처 변경은 LLM을 혼란시킨다
- 도구 목록 및 파라미터 시그니처의 **단일 원본 = `docs/TOOLS.md`**.
- **AI는 임의로 새 도구를 추가하거나 기존 도구의 인자명/타입을 변경하지 않는다.**
  ① 변경안을 `docs/TOOLS.md`에 먼저 기록 → ② 사용자 확인 → ③ 코드 반영.
- **Docstring은 곧 LLM의 프롬프트다**: FastMCP는 docstring을 LLM 도구 설명(description)으로 변환한다.
  애매한 설명 금지: "무엇을 하는지", "어떤 형식으로 넘겨야 하는지"를 명확히 쓴다.

## 보안 — LLM이 호출하는 로컬 도구의 책임
- **① 명령 실행/쉘 인젝션 차단**:
  사용자 입력을 `shell=True`나 `eval()`에 절대 넣지 않는다. 파라미터 분리 실행(`subprocess.run([...])`).
- **② 파일시스템 접근 제한 (Path Traversal 방지)**:
  도구가 파일을 다룰 때는 지정된 허용 디렉토리 내부인지 반드시 `Path.resolve()`로 검증.
- **③ 비밀정보/API 키 보호**:
  토큰/비밀키는 소스코드에 하드코딩하지 않고 환경변수(`os.environ`)로만 주입.
  로그에 API 키나 민감 데이터가 출력되지 않도록 마스킹.

## 구조
- **디렉토리 뼈대 (Phase 002 세팅에서 확정)**:
  ```
  src/
    server.py          ← FastMCP 서버 인스턴스 및 엔트리포인트
    tools/             ← 개별 도구 핸들러 모듈
    resources/         ← MCP 리소스 모듈 (선택)
    prompts/           ← 프롬프트 템플릿 모듈 (선택)
    common/            ← 로깅(stderr 전용), 환경설정, 예외 클래스
  tests/               ← pytest 테스트 (도구별 유닛 테스트)
  docs/                ← REQUIREMENTS.md, TOOLS.md, playbooks/
  work_log/            ← plan.md, Phase_XXX.md
  agents/              ← 서브에이전트 정의
  scripts/             ← 규칙 카운터 등
  pyproject.toml       ← 의존성 및 프로젝트 설정
  ```
  **이 트리 밖에 임의로 최상위 디렉토리를 만들지 말 것.**

## 불변 규칙 (MCP 특화)
- **★ stdout 오염 절대 금지 (stdio 파괴 방지)**:
  `stdio` 전송 모드에서 `print()`를 쓰면 JSON-RPC 프레임이 깨져 클라이언트 연결이 즉시 끊어진다.
  모든 로깅은 반드시 `sys.stderr` 또는 파일 로거(`logging.StreamHandler(sys.stderr)`)만 사용한다.
- **Windows UTF-8 인코딩 강제**: Windows 환경에서 stdio 한글 깨짐 방지 (`PYTHONIOENCODING=utf-8`).
- **Silent Failure 금지**: 도구 내부 예외를 조용히 삼키지 말고, 의미 있는 에러 메시지로 클라이언트에 반환.
- **Strict Type Hinting**: FastMCP 스키마 생성을 위해 모든 함수 인자와 반환값에 타입 힌트(`str`, `int`, `BaseModel` 등) 필수.
- **비동기 블로킹 방지**: 오래 걸리는 I/O 도구는 `async def`를 사용하거나 쓰레드 풀로 격리.

## Anti-Rationalization ★AI의 합리화를 차단한다

| AI가 하려는 합리화 | 대응 |
|---|---|
| "간단한 디버깅이니 print() 한 번만 찍자" | **stdout 오염 즉시 연결 종료.** 무조건 stderr 로깅 사용 |
| "클라이언트가 알아서 올바른 인자를 줄 것이다" | LLM은 잘못된 인자(None, 오타)를 빈번히 넘김. Pydantic 검증 필수 |
| "도구 설명은 짧게 써도 LLM이 알아챌 것" | Description이 부실하면 LLM이 도구를 엉뚱하게 호출하거나 외면함 |
| "단위 테스트가 통과했으니 Inspector는 생략" | 실제 JSON-RPC 전송 및 직렬화는 Inspector에서만 확인 가능 |
| "에러 시 exception을 그대로 던지면 됨" | 원시 스택트레이스는 LLM 컨텍스트를 오염시킴. 깔끔한 에러 응답 반환 |
| "테스트 작성을 위한 mock 생성이 귀찮으니 생략" | 외부 API나 무거운 자원은 mock 테스트가 필수 |
| "환경변수 대신 코드에 키 임시 입력" | 깃 커밋 유출 위험 1순위. 무조건 .env 관리 |
| "리소스를 도구로 만들어도 상관없음" | 정적/읽기전용 데이터는 Resource, 실행 동작은 Tool로 분리 |
| "Windows 인코딩은 나중에 확인" | 한글 입출력 깨짐은 초기에 잡지 않으면 원인 파악 어려움 |
| "FastMCP가 다 해주니 에러 처리는 불필요" | FastMCP 위에서도 도구 비즈니스 로직 에러는 명시적 핸들링 필요 |

## Evidence Gate ★증거 없이 완료 선언 금지

- **도구 구현 완료 시**:
  - `pytest` 통과 로그 (정상 입력, 비정상 인자 입력, 경계값)
  - 실제 JSON-RPC 도구 호출 요청/응답 샘플 로그 (ToolResult)
  - **MCP Inspector 실행 확인 로그** (`npx @modelcontextprotocol/inspector`)
- **Phase 완료 시**: 전체 테스트 통과 로그 + `docs/TOOLS.md` 스펙 일치 확인.

## 검증 강도 ★"무엇을 바꿨나"로 정한다

| 변경 종류 | 검증 |
|---|---|
| 문서·주석·문구 (동작 불변) | diff 확인. 테스트 0 |
| **도구 Docstring 변경 (설명 수정)** | LLM 호출 유도 프롬프트 확인 + Inspector에서 스키마 확인 |
| 도구 내부 비즈니스 로직 변경 | 관련 pytest 유닛 테스트 통과 |
| **도구 시그니처 (인자 추가/변경/삭제)** | `docs/TOOLS.md` 승인 갱신 + pytest + Inspector 스키마 검증 |
| 신규 도구 추가 | `docs/TOOLS.md` 갱신 + pytest 신규 작성 + Inspector 호출 실측 |
| 서버 전송 계층/미들웨어 변경 | stdio/SSE 연결 테스트 + 전체 pytest 통과 |

## 검증 게이트

| 게이트 | 서브에이전트 | 시점 |
|---|---|---|
| 조사 | `researcher` | 도구 라이브러리/외부 API 스펙 조사 |
| 스펙화 | `requirements-analyst` | 도구 시그니처 및 스키마 설계 (`TOOLS.md`) |
| 스펙 대조 | `spec-checker` | 코드 구현 후 `TOOLS.md` 시그니처 일치 여부 판정 |
| 통합 테스트 | `qa-tester` | pytest 및 Inspector 실행 검증 |

- 서브에이전트 정의: `agents/*.md`. Antigravity `define_subagent`로 호출.

## 작업 속도 규칙
- 불필요한 쉘 명령 남발 방지 (단위 테스트 묶어서 실행).
- MCP 서버를 백그라운드로 띄워두고 포트가 물려 테스트가 실패하는 상황 방지.
- 커밋은 작업 단위마다. 검증 결과(테스트 로그)를 커밋 메시지에 기록.

## AGENTS.md 비대화 방지 ★상한 100개
- `python scripts/count_rules.py`로 센다. Phase 종료 시 확인. 넘으면 플레이북으로 이관.

## 테스트 및 배포 체크리스트

### 로컬 검증 (개발 단계)
1. `python -m pytest tests/` — 유닛 테스트 100% 통과
2. `npx @modelcontextprotocol/inspector python src/server.py` — Inspector 웹 UI에서 도구 수동 호출 확인
3. stdout 오염 여부 최종 점검 (서버 실행 시 stdout으로 나가는 출력 없는지)

### 클라이언트 연동 설정 (Claude Desktop / Antigravity)
- [ ] `claude_desktop_config.json` 또는 Antigravity `mcp_servers` 설정 추가
- [ ] 절대 경로 파이썬 가상환경 인터프리터 경로 명시
- [ ] 환경변수(API Keys) 전달 설정 확인
- [ ] 클라이언트 재시작 후 도구 목록(`tools/list`) 정상 노출 확인

## 알려진 함정
- **`print()`로 인한 stdio 프로토콜 파괴**: 디버깅 로그는 반드시 `logging.getLogger().info()` (stderr) 사용.
- **Windows 한글 깨짐**: `sys.stdout.reconfigure(encoding='utf-8')` 초기화 코드 필수.
- **Pydantic v2 호환성**: `Field(description="...")`를 정확히 써야 LLM에게 파라미터 설명이 전달됨.
- **비동기 타임아웃**: 외부 API 호출 시 `httpx.AsyncClient`의 타임아웃(30초)을 명시하지 않으면 영구 행(hang) 발생.
- **zdic POST 청크 전송 방지**: 검색 POST 요청 시 `Content-Length` 명시 필수.
- **zdic 302 리다이렉트 추적**: POST 후 302 리다이렉트가 2회 연속 발생하므로 수동 또는 확실한 추적 로직 필요.
- **초서 투명 GIF 흰 배경**: 원본 GIF는 투명 배경이므로 격자 합성/표시 시 어두운 UI에서 글자가 묻히지 않도록 흰색 바탕 처리.
- **이미지 바이트 매직넘버 검증**: 200 OK여도 HTML 안내가 올 수 있으므로 `GIF8`, `JPEG`, `PNG`, `WEBP` 헤더 검증.
- **결과 없음 vs 오류 엄격 분리**: `没有搜索到相关的内容`인 경우만 결과 0건으로 처리하고, 파싱 실패는 에러로 즉시 드러냄(캐시 오염 방지).
- **shufazidian.com 사용 금지**: 오직 `sf.zdic.net`만 사용하며, 사전 전체 일괄 스크래핑 금지.

