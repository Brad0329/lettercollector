# LetterCollector — 구글 클라우드(GCP) 배포 및 연동 가이드

구글 클라우드에 `LetterCollector`를 올려두면 **웹 브라우저, 모바일 앱(hanjadic 등), AI 에이전트(Claude Code, Claude Desktop 등)** 어디서든 24시간 초서 수집 및 조회를 사용할 수 있습니다.

---

## 1. Cloud Run 배포 (가장 추천 — 서버리스, 월 0원)

GCP의 **Cloud Run**은 요청이 있을 때만 컨테이너가 켜지는 서버리스 환경으로, 개인 사용량 수준에서는 **완전 무료(Free Tier)**로 운영할 수 있습니다.

### 배포 순서 (터미널에서 1줄 실행)

`gcloud` CLI가 설치된 터미널에서 이 프로젝트 폴더로 이동한 뒤 아래 명령어를 실행합니다:

```bash
gcloud run deploy letter-collector \
  --source . \
  --region asia-northeast3 \
  --allow-unauthenticated \
  --port 8080 \
  --set-env-vars "MCP_TRANSPORT=sse,LETTER_API_KEY=your_secret_key"
```

- `--region asia-northeast3`: 서울 리전으로 배포합니다.
- `--allow-unauthenticated`: 웹/앱/AI가 URL로 바로 접근할 수 있도록 허용합니다 (인증은 `LETTER_API_KEY`로 제어).
- 배포가 완료되면 `https://letter-collector-xxxxx-du.a.run.app` 형태의 HTTPS 주소가 발급됩니다.

---

## 2. Compute Engine (VM) 배포

저장된 이미지 파일들을 로컬 폴더처럼 영구히 보관하고 싶다면 작은 VM(무료 티어 e2-micro)에 올릴 수 있습니다.

```bash
# VM 내부에서 실행
git clone <저장소URL> LetterCollector
cd LetterCollector
uv venv
uv pip install -e .

# 백그라운드 HTTP 실행
export PORT=8080
export MCP_TRANSPORT=sse
python -m src.server
```

---

## 3. 웹, 앱, AI 연동 방법

### 3.1 웹 브라우저에서 보기
- **갤러리 전체 보기**: `https://<서버URL>/gallery/永`
- **단일 이미지/격자 보기**: `https://<서버URL>/images/永/grid.png`
- **서버 상태 확인**: `https://<서버URL>/health`

### 3.2 모바일 앱 (Flutter `hanjadic` 등) 연동
앱에서 HTTP GET 요청으로 초서 데이터 JSON을 바로 수신할 수 있습니다:

- **요청**:
  ```http
  GET https://<서버URL>/api/cursive/永
  Header: X-API-Key: your_secret_key
  ```
- **응답 (JSON)**:
  ```json
  {
    "char": "永",
    "canonical_char": "永",
    "total_count": 26,
    "calligrapher_counts": {
      "智永": 3,
      "怀素": 3,
      "王羲之": 2, ...
    },
    "grid_url": "/images/永/grid.png",
    "gallery_url": "/gallery/永",
    "items": [
      {
        "index": 1,
        "calligrapher": "高闲",
        "calligrapher_ko": "고한",
        "image_url": "/images/永/001_高闲.gif",
        "source_url": "https://sf.zdic.net/..."
      }, ...
    ]
  }
  ```

### 3.3 클로드 코드 (Claude Code) 원격 연동
로컬 파이썬을 실행하지 않고, 클라우드 서버 URL로 직접 연결합니다:

```bash
claude mcp add --transport http --scope global letter-collector https://<서버URL>/mcp
```
*(API Key 설정 시 `--header "X-API-Key: your_secret_key"` 추가)*

### 3.4 클로드 데스크톱 (Claude Desktop) 원격 연동
`claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "letter-collector": {
      "url": "https://<서버URL>/mcp"
    }
  }
}
```

---

## 4. 환경 변수 요약

| 환경 변수 | 기본값 | 설명 |
|---|---|---|
| `PORT` | `8080` | HTTP 서버 포트 (GCP Cloud Run 자동 주입) |
| `HOST` | `0.0.0.0` | 바인딩 호스트 |
| `MCP_TRANSPORT` | `sse` | 전송 모드 (`sse` 또는 `stdio`) |
| `LETTER_API_KEY` | *(미설정 시 무인증)* | 외부 무단 호출 방지용 비밀 키 |
| `LETTER_STORAGE_DIR` | `/app/storage` | 초서 이미지 및 메타데이터 저장 경로 |
