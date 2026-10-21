# MCP 도구 및 스펙 대장 (단일 원본)

> **이 문서는 MCP Server가 외부에 제공하는 Tools, Resources, Prompts 시그니처의 단일 원본(Single Source of Truth)이다.**
> DB의 `SCHEMA.md`와 동일한 위상을 가지며, 클라이언트(LLM)와의 계약(Contract)을 정의한다.
> **AI는 사용자 승인 없이 새 도구를 임의로 추가하거나 기존 도구의 파라미터 시그니처를 수정하지 않는다.**

---

## 1. Tools 정의 대장 (도구 목록)

### 1.1 도구 요약 표

| 식별자 (Tool Name) | 설명 (LLM용 Description) | 필수 인자 (Parameters) | 선택 인자 (Optional) | 반환 형식 | 부작용 / 보안 수준 |
|---|---|---|---|---|---|
| `find_cursive` | 한자의 초서 이미지를 전체 수집/캐시 조회하고 통계, 격자 합성 이미지, HTML 갤러리 경로 반환 | `char: str` | `refresh: bool = False` | `str` | 로컬 쓰기 / 외부 호출 |
| `get_cursive_image` | 수집된 초서 이미지 중 특정 순번(1부터 시작)의 원본 파일 경로 및 상세 정보 반환 | `char: str`, `index: int` | 없음 | `str` | 읽기 전용 / 온디맨드 수집 |

---

### 1.2 도구 상세 명세 (Detail Specifications)

#### T-001: `find_cursive`
- **식별자 (Tool Name)**: `find_cursive`
- **설명 (LLM Description / Docstring)**:
  ```text
  Find and retrieve all cursive script (草書) calligraphy images for a given Chinese character from sf.zdic.net, saving them to local storage and returning statistics, a visual grid summary image path, and an HTML gallery path.

  WHEN TO USE:
  - Use this tool when the user asks to look up or show cursive script images for a Chinese character (e.g., '書 글자 초서 찾아줘', 'show cursive for 永').
  - Caches results locally so repeated queries are instant without re-downloading.

  Args:
      char: A single Chinese character (e.g. '書', '永', '龍'). Must be exactly 1 character.
      refresh: If True, bypasses local cache and re-downloads fresh images from sf.zdic.net (default: False).

  Returns:
      A markdown summary containing total image count, calligrapher list with counts, local storage path, grid image path, and HTML gallery path.
  ```
- **파라미터 (Parameters)**:
  - `char` (`str`, 필수): 검색할 한자 1글자.
  - `refresh` (`bool`, 선택, 기본값 `False`): 캐시를 무시하고 새로 수집할지 여부.
- **반환 형식 (Return Format)**:
  - 성공 시: 마크다운 텍스트(총 장수, 서예가별 장수, 저장 폴더, `grid.png` 경로, `index.html` 경로) + **ImageContent (격자 합성 이미지 base64 직접 반환)**
  - 실패 시: `isError=True` 또는 명확한 오류 안내 텍스트.
- **부작용 및 보안 수준 (Side Effect & Security)**:
  - 보안 수준: **Local File Write & External Network GET/POST**
  - 안전성: 허용된 `storage/` 내부 경로만 접근, 외부 쉘 실행 없음.

---

#### T-002: `get_cursive_image`
- **식별자 (Tool Name)**: `get_cursive_image`
- **설명 (LLM Description / Docstring)**:
  ```text
  Get information and the local file path of a specific cursive script image by index (1-based) for a Chinese character.

  WHEN TO USE:
  - Use this tool when the user wants to inspect or view a specific single image among the collected cursive scripts.

  Args:
      char: A single Chinese character (e.g. '書').
      index: 1-based index of the image to retrieve (e.g. 1 for the first image).

  Returns:
      A markdown summary with calligrapher name, source URL, local file path, and image metadata.
  ```
- **파라미터 (Parameters)**:
  - `char` (`str`, 필수): 한자 1글자.
  - `index` (`int`, 필수): 1-based 순번.
- **반환 형식 (Return Format)**:
  - 서예가 이름, 로컬 이미지 절대 파일 경로, 원본 URL 등 마크다운 안내 + **ImageContent (해당 원본 이미지 base64 직접 반환)**

---

## 2. Resources 정의 대장 (자원 목록)

### 2.1 리소스 요약 표

| URI 패턴 (URI Scheme) | 리소스 명칭 | 설명 | MIME 타입 | 캐싱 / 갱신 주기 |
|---|---|---|---|---|
| `cursive://list` | `cached_characters` | 현재 로컬에 캐시된 수집 완료 한자 목록 및 장수 | `application/json` | 실시간 (로컬 스토리지 기준) |
| `cursive://char/{char}` | `char_index` | 특정 한자의 index.json 메타데이터 원본 | `application/json` | 실시간 |

---

## 3. Prompts 정의 대장

현재 단계에서는 프롬프트 템플릿(Prompts)은 등록하지 않음 (YAGNI 원칙). 필요 시 추가.
