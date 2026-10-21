# 팩: Python MCP 서버 (FastMCP & stdio 통신 핵심 노하우)

> **이 문서는 Python 기반 Model Context Protocol(MCP) 서버를 개발할 때 마주치는 치명적인 함정들과 해결 기법을 집대성한 핵심 지침서이다.**
> 프로젝트 착수 전, 그리고 통신 문제나 클라이언트 연동 에러가 발생했을 때 가장 먼저 열어본다.

---

## 1. stdout 오염의 저주 (Zero stdout Pollution)

### 1.1 증상과 치명도
- **증상**: 서버가 잘 뜨는 것처럼 보이다가 클라이언트(Claude Desktop, Cursor 등)에서 연결이 즉시 끊어지거나(`Connection closed`), `Unexpected token in JSON` 등의 파싱 오류가 발생함.
- **원인**: `stdio` 전송 모드에서 `stdout`은 순수한 JSON-RPC 2.0 프로토콜 메시지(1줄 1프레임) 전용 채널이다. 여기에 `print("debug")`나 서드파티 라이브러리의 배너 출력이 단 한 줄이라도 섞이면 JSON 파서가 깨져 즉각 프로세스 통신이 파괴된다.

### 1.2 해결 규칙
1. **코드 내 `print()` 사용 전면 금지**:
   - 디버깅용 print문도 절대 허용되지 않는다.
2. **모든 로깅은 `sys.stderr`로 강제**:
   ```python
   import sys
   import logging

   # server.py 또는 common/logger.py 최상단에 구성
   logging.basicConfig(
       level=logging.INFO,
       format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
       stream=sys.stderr,  # 반드시 stderr로 지정!
   )
   logger = logging.getLogger("mcp_server")
   ```
3. **서드파티 라이브러리의 stdout 출력 납치(Hijack) 방지**:
   - 일부 라이브러리(임포트 시 환영 문구를 stdout으로 출력하는 패키지 등)를 사용할 때는 임포트 또는 호출부를 stderr로 리디렉션한다.
   ```python
   import contextlib
   import sys

   # 불필요한 stdout 출력을 stderr로 우회
   with contextlib.redirect_stdout(sys.stderr):
       import noisy_package
   ```

---

## 2. Windows stdio 인코딩 함정 (CP949 vs UTF-8)

### 2.1 증상
- Windows 환경에서 한글 텍스트를 인자로 받거나 반환할 때 `UnicodeEncodeError: 'cp949' codec can't encode character` 에러가 발생하며 서버가 크래시됨.
- MCP Inspector에서는 정상 동작하는데 Claude Desktop(Windows)에서만 한글이 깨지거나 통신이 두절됨.

### 2.2 해결책

#### ① 서버 진입점 코드 레벨 강제 (필수)
`src/server.py`의 최상단(어떤 임포트보다 앞서서)에 표준 스트림을 UTF-8로 재구성한다.
```python
import sys

if sys.platform == "win32":
    try:
        sys.stdin.reconfigure(encoding="utf-8")
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        # Python 3.7 이전 호환 대비 (3.8 이상은 reconfigure 지원)
        pass
```

#### ② 클라이언트 실행 환경변수 주입
`claude_desktop_config.json` 등록 시 `env` 블록에 아래 두 환경변수를 명시적으로 전달한다.
```json
{
  "mcpServers": {
    "my-server": {
      "command": "c:\\path\\to\\venv\\Scripts\\python.exe",
      "args": ["-u", "c:\\path\\to\\src\\server.py"],
      "env": {
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1"
      }
    }
  }
}
```

---

## 3. FastMCP 임포트 규약 및 데코레이터 사용법

### 3.1 공식 패키지 구조와 임포트
공식 MCP Python SDK(`mcp`)는 고수준 인터페이스로 `FastMCP`를 내장하고 있다.
```python
# 공식 SDK 표준 임포트
from mcp.server.fastmcp import FastMCP, Context
from pydantic import Field
```

### 3.2 서버 인스턴스 초기화
```python
mcp = FastMCP(
    name="MyCustomServer",
    instructions="이 서버는 파일 및 데이터 조작 도구를 제공합니다.",
    # log_level 설정
)
```

### 3.3 핵심 데코레이터 사용 패턴
- **도구 등록 (`@mcp.tool()`)**:
  ```python
  @mcp.tool()
  async def calculate_summary(items: list[str], ctx: Context = None) -> str:
      """
      Calculate summary statistics for given items.
      
      Args:
          items: List of item names to summarize.
      """
      if ctx:
          await ctx.info("Calculating summary in progress...")
      return f"Total items: {len(items)}"
  ```
- **리소스 등록 (`@mcp.resource()`)**:
  ```python
  @mcp.resource("config://app/settings")
  def get_settings() -> str:
      """Return current application settings in JSON."""
      return '{"mode": "production", "version": "1.0.0"}'
  ```
- **프롬프트 등록 (`@mcp.prompt()`)**:
  ```python
  @mcp.prompt()
  def review_request(topic: str) -> str:
      """Generate review prompt template."""
      return f"Please conduct a thorough review regarding: {topic}"
  ```

---

## 4. Pydantic 스키마와 Type Hint 변환 규칙

FastMCP는 파이썬의 **타입 힌트(Type Annotation)**와 **함수 Docstring**을 분석하여 LLM에게 제공할 OpenAPI/JSON Schema를 자동으로 빌드한다.

### 4.1 스키마 생성 매핑 규칙
1. **기본 타입 매핑**:
   - `str` ➔ `{"type": "string"}`
   - `int` ➔ `{"type": "integer"}`
   - `float` ➔ `{"type": "number"}`
   - `bool` ➔ `{"type": "boolean"}`
   - `list[str]` ➔ `{"type": "array", "items": {"type": "string"}}`
2. **필수(Required) vs 선택(Optional)**:
   - 기본값이 없는 인자(`query: str`) ➔ `required` 목록에 포함.
   - 기본값이 있는 인자(`limit: int = 10`) ➔ 선택 인자로 처리.
   - `Optional[str] = None` ➔ 선택 인자, Nullable.
3. **Pydantic `Field` 활용 (정밀 제약 조건 부여)**:
   ```python
   from pydantic import Field

   @mcp.tool()
   def search_logs(
       keyword: str = Field(..., description="검색할 로그 키워드", min_length=2),
       max_results: int = Field(default=20, ge=1, le=100, description="최대 반환 건수")
   ) -> str:
       """Search system logs."""
       ...
   ```
4. **Docstring 매핑 원칙**:
   - Docstring 본문 ➔ 도구 전체의 `description`.
   - `Args:` 아래의 파라미터별 설명 ➔ 각 파라미터의 `description`.

---

## 5. MCP Inspector 활용 노하우

`@modelcontextprotocol/inspector`는 서버의 JSON-RPC 통신과 도구 스키마를 브라우저에서 시각적으로 테스트할 수 있는 필수 도구다.

### 5.1 실행 방법
```bash
# 로컬 venv 환경에서 실행 (Windows PowerShell 기준)
npx @modelcontextprotocol/inspector .venv\Scripts\python.exe src\server.py
```

### 5.2 검증 체크포인트
1. **Tools 탭**:
   - 정의된 모든 도구가 누락 없이 등록되어 있는가?
   - 각 도구의 Description과 Parameter 이름/타입이 명확히 표시되는가?
2. **도구 수동 호출 (Run Tool)**:
   - 정상 입력값을 넣고 실행했을 때 기대한 반환값(Text/JSON)이 표시되는가?
   - 빈 값이나 잘못된 타입을 넣었을 때 프로세스가 죽지 않고 유효성 검사 에러가 깔끔하게 반환되는가?
3. **Notifications / Logs 탭**:
   - `ctx.info()`나 `logger.info()`(stderr)로 발생한 로그가 메시지 스트림으로 잘 들어오는가?
4. **주의점**:
   - 코드를 수정해도 이미 띄워진 Inspector 프로세스는 자동 핫 리로드(Hot-reload)를 지원하지 않는다. 코드를 고쳤으면 Inspector를 `Ctrl+C`로 종료하고 다시 기동해야 한다.

---

## 6. 장기 실행 및 비동기(Async) 주의점

- **단일 스트림 블로킹의 위험**:
  - `stdio`는 단일 양방향 파이프다. 도구 함수 내에서 동기식 `time.sleep(10)`이나 동기식 네트워크 I/O(`requests.get()`)를 실행하면, 해당 작업이 끝날 때까지 서버 전체의 이벤트 루프가 멈춰 클라이언트의 핑(Ping)이나 다른 요청을 처리하지 못한다.
- **모든 I/O는 `async def` 기반으로 작성**:
  - HTTP 요청: `httpx.AsyncClient` 사용.
  - 파일 I/O: `aiofiles` 또는 빠른 비동기 처리.
  - 비동기 대기: `asyncio.sleep()`.
- **CPU 바운드 무거운 연산**:
  - `async def` 안에서 대량 연산이나 무거운 로컬 처리를 할 때는 이벤트 루프를 넘겨주도록 스레드 풀로 위임한다:
  ```python
  import asyncio

  @mcp.tool()
  async def heavy_computation_tool(data: str) -> str:
      """Process large data without blocking stdio loop."""
      result = await asyncio.to_thread(cpu_heavy_task, data)
      return result
  ```
