# LetterCollector — 한자 초서(草書) 이미지 수집 및 제공 MCP 서버

Model Context Protocol (MCP) 기반 Python 서버입니다.
사용자 요청에 따라 汉典书法(`sf.zdic.net`)에서 한자 초서 이미지를 온디맨드로 검색·수집하고, 로컬 디렉터리에 캐싱하여 LLM(Antigravity, Claude Desktop 등)에 도구(Tools) 및 리소스(Resources) 형태로 제공합니다.

## 주요 기능

1. **온디맨드 초서 이미지 수집**:
   - `find_cursive(char, refresh=False)`: 단일 한자의 초서 이미지를 전체 수집하여 목록 요약, 서예가 통계, 격자 합성 이미지 및 로컬 HTML 갤러리 경로 반환.
2. **로컬 캐싱 & 빠른 조회**:
   - 동일 글자는 로컬 `storage/<글자>/` 폴더에 원본 GIF 및 `index.json`으로 저장되어 반복 요청 시 네트워크 통신 없이 즉시 반환.
   - 번체/간체(예: 書 / 书) 동일 페이지 자동 매핑으로 중복 저장 방지.
3. **단일 원본 이미지 조회**:
   - `get_cursive_image(char, index)`: 특정 서예가나 번호의 원본 이미지를 조회.
4. **시각화 지원**:
   - 투명 GIF 특성을 고려한 흰색 바탕 렌더링.
   - 전체 초서를 한눈에 볼 수 있는 격자(Grid) 합성 이미지 및 탐색용 HTML 갤러리 생성.

## 설치 및 실행

```bash
# 가상환경 생성 및 의존성 설치
uv venv
uv pip install -e ".[dev]"

# FastMCP 서버 실행 (stdio 모드)
.venv/Scripts/python -m src.server
```

## 클라이언트 연동 (Claude Desktop)

`%APPDATA%\Claude\claude_desktop_config.json`에 다음 설정을 추가합니다:

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
