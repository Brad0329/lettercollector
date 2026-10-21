# LetterCollector 요구사항 (단일 원본)

> 기능 요구사항 + 수용 기준의 단일 원본. **요구사항이 바뀌면 대화로 합의만 하지 말고 이 파일을 즉시 갱신.**
> 완료 판정은 항상 이 문서를 기준으로 한다.
> **요구사항 ID 대장**: Tool: T-001~, Resource: R-001~, Prompt: P-001~. 번호 재사용 금지.

---

## 1. 시스템 개요 및 목표

- **시스템 명칭**: LetterCollector (초서 수집기)
- **한 줄 설명**: 汉典书法(`sf.zdic.net`) 기반 한자 초서(草書) 이미지 온디맨드 검색·수집, 로컬 캐싱 및 다채로운 시각화(격자 이미지, HTML 갤러리)를 제공하는 MCP 서버.
- **시스템 유형**: Model Context Protocol (MCP) Server (Python, FastMCP 기반)
- **전송 계층 (Transport)**: `stdio` (로컬 클라이언트 기본)
- **대상 클라이언트 (Client Target)**: Claude Desktop, Antigravity, Cursor 등 MCP 호환 호스트
- **핵심 목표**:
  1. 사용자가 "書 글자 초서 찾아줘"라고 요청하면 도구가 동작하여 초서 이미지를 수집하고 보여준다.
  2. 출처는 `sf.zdic.net` 단일 소스이며, 해당 글자의 초서를 있는 대로 전부 수집한다.
  3. 수집된 이미지는 로컬에 저장(`storage/<글자>/`)하고, 이후 동일 글자 요청 시 캐시를 우선 사용한다.
  4. 사전 전체 대량 크롤링은 하지 않으며 사용자 온디맨드 요청 시에만 수집한다.

---

## 2. 핵심 제공 기능 (Capabilities)

1. **Tools (함수 실행)**:
   - `find_cursive`: 특정 한자의 초서 이미지를 전체 수집/조회하고 통계와 격자/갤러리 정보 반환.
   - `get_cursive_image`: 특정 글자의 N번째 원본 초서 이미지 정보 및 파일 경로 반환.
2. **Resources (데이터 읽기)**:
   - `cursive://list`: 로컬에 캐시된 수집 완료 한자 목록 반환.
   - `cursive://char/{char}`: 특정 한자의 수집 메타데이터(`index.json`) 반환.

---

## 3. 클라이언트 설치 및 등록 요구사항 (Client Configuration)

### 3.1 Claude Desktop 연동 설정 (`claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "letter-collector": {
      "command": "C:\\Users\\user\\Documents\\LetterCollector\\.venv\\Scripts\\python.exe",
      "args": ["-u", "-m", "src.server"],
      "env": {
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

---

## 4. 기능 요구사항

### 4.1 Tools (도구 대장)

#### T-001: `find_cursive`
- **설명**: 한자 한 글자를 입력받아 `sf.zdic.net`에서 모든 초서 이미지를 수집하고(또는 로컬 캐시 조회), 결과 통계, HTML 갤러리 경로, 격자 미리보기 이미지 정보를 반환한다.
- **입력 인자**:
  - `char` (`str`, 필수): 검색할 한자 1글자. (예: "書", "永", "龍")
  - `refresh` (`bool`, 선택, 기본값: `False`): 로컬 캐시를 무시하고 웹에서 새로 수집할지 여부.
- **수용 기준**:
  - [ ] 입력 `char`의 길이가 1이 아니거나 한자가 아닌 경우 명확한 유효성 검사 에러를 반환한다.
  - [ ] 로컬 캐시(`storage/<글자>/index.json`)가 존재하고 `refresh=False`인 경우 네트워크 요청 없이 캐시된 결과를 반환한다.
  - [ ] 캐시가 없거나 `refresh=True`인 경우 zdic 검색 파이프라인(POST → 302 리다이렉트 추적 → 조각 HTML 파싱 → GIF 다운로드)을 실행한다.
  - [ ] 번체/간체(예: 書 / 书) 검색 시 동일한 대상 페이지로 귀결되는 경우 동일 캐시 폴더를 참조/저장하여 중복 다운로드를 방지한다.
  - [ ] 검색 결과가 0건(`没有搜索到相关的内容`)인 경우 오류가 아닌 "초서 없음(0건)"을 정상 반환한다.
  - [ ] 수집된 모든 이미지에 대해 흰색 배경 처리 및 격자 합성 이미지(`grid.png`)와 HTML 갤러리(`index.html`)를 자동 생성한다.
  - [ ] 총 이미지 장수, 서예가 목록 및 서예가별 장수, 저장 디렉터리 경로, HTML 갤러리 경로를 마크다운 형식으로 요약 반환한다.
- **엣지케이스 / 에러 응답**:
  - 네트워크 단절/타임아웃(30초 초과): 명확한 네트워크 실패 에러 반환 (캐시 오염 방지).
  - zdic HTML 구조 변경: 파싱 에러를 명시적으로 반환.
  - 다운로드된 이미지 바이트가 유효한 이미지 헤더(GIF8 등)가 아닌 경우 에러 처리.

#### T-002: `get_cursive_image`
- **설명**: 특정 한자의 N번째(1-based) 초서 원본 이미지 파일 경로 및 메타데이터를 반환한다.
- **입력 인자**:
  - `char` (`str`, 필수): 대상 한자 1글자.
  - `index` (`int`, 필수): 가져올 이미지 번호 (1부터 시작).
- **수용 기준**:
  - [ ] `char`에 해당하는 캐시가 없으면 먼저 수집을 시도하거나 없음을 알린다.
  - [ ] `index`가 1 미만이거나 총 장수를 초과할 경우 범위 초과 에러 메시지를 반환한다.
  - [ ] 유효한 `index`인 경우 해당 서예가 이름, 원본 파일 경로, URL 정보를 반환한다.

---

### 4.2 Resources (자원 대장)

#### R-001: `cached_characters`
- **URI 패턴**: `cursive://list`
- **MIME 타입**: `application/json`
- **설명**: 현재 로컬 `storage/`에 캐싱된 모든 한자 목록과 글자별 수집 장수 정보를 JSON으로 제공.

#### R-002: `char_index`
- **URI 패턴**: `cursive://char/{char}`
- **MIME 타입**: `application/json`
- **설명**: 특정 한자의 `index.json` 메타데이터(전체 장수, 서예가별 이미지 목록, 수집 일시 등)를 JSON으로 제공.

---

## 5. 비기능 요구사항

1. **stdio 프로토콜 안전성 (Zero stdout Pollution)**:
   - `stdio` 통신은 stdout을 순수한 JSON-RPC 2.0 메시지 전용으로 사용.
   - 모든 내부 로깅은 `sys.stderr` 또는 파일 로거만 사용하며 `print()` 금지.
2. **네트워크 안전성 및 타임아웃**:
   - `httpx.AsyncClient`의 timeout은 30초로 강제.
   - zdic 검색 POST 시 `Content-Length` 명시(청크 전송 방지).
   - 302 리다이렉트 안전 추적.
3. **이미지 무결성 및 시각화**:
   - 투명 GIF 특성을 보정하여 격자 합성 시 흰색 배경 적용.
   - GIF 매직넘버(`GIF8`) 등 헤더 검증.
4. **결과 없음 vs 오류 엄격 분리**:
   - `没有搜索到相关的内容`는 정상 빈 결과, 파싱 실패는 에러로 보고하여 캐시 오염 원천 차단.
5. **금지 사항 준수**:
   - `shufazidian.com` 호출 금지.
   - 사전 전체 대량 크롤링 금지.
6. **Windows UTF-8 인코딩 보장**:
   - `sys.stdout.reconfigure(encoding='utf-8')` 초기화 적용.

---

## 6. 하지 않는 것 (Out of Scope)

- shufazidian.com 크롤링 (zdic 단일 소스 원칙 준수)
- 사전 전체 글자 배치 다운로드
- 다중 사용자 웹 서비스/원격 인증 기능
