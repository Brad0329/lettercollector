# LetterCollector — 구글 클라우드(GCP) 배포 및 연동 가이드

구글 클라우드에 `LetterCollector`를 올려두면 **웹 브라우저, 모바일 앱(hanjadic 등), AI 에이전트(Claude Code, Claude Desktop 등)** 어디서든 24시간 초서 수집 및 조회를 사용할 수 있습니다.

---

## 1. Compute Engine (VM) 배포 (추천: 기존 VM 보유 시)

이미 생성해 두신 GCP VM 인스턴스가 있다면, **로컬 `storage/` 폴더에 이미지가 영구 보존**되므로 별도의 버킷 설정 없이 가장 빠르고 안정적입니다.

### 1.1 VM에 접속하여 설치 (SSH 터미널)

1. **프로젝트 코드 가져오기**:
   ```bash
   git clone <깃저장소URL> LetterCollector
   # 또는 로컬 PC에서 scp로 폴더 복사
   cd LetterCollector
   ```

2. **자동 환경 셋업 스크립트 실행**:
   ```bash
   bash scripts/setup_vm.sh
   ```
   *(파이썬 가상환경, 필수 패키지, 중국어 간체/한글 깨짐 방지용 CJK 폰트 `fonts-noto-cjk`가 자동 설치됩니다)*

3. **자동 재시작 백그라운드 서비스(systemd) 등록**:
   ```bash
   bash scripts/install_service.sh
   ```
   *(VM이 재부팅되더라도 자동으로 8080 포트에서 서버가 켜집니다)*

### 1.2 GCP 방화벽 규칙 확인 (포트 8080 허용)

GCP 콘솔 > **VPC 네트워크 > 방화벽**에서 8080 포트가 열려 있는지 확인합니다:
- 대상: 네트워크의 모든 인스턴스 (또는 해당 VM 태그)
- 소스 IP 범위: `0.0.0.0/0`
- 프로토콜 및 포트: `tcp:8080`

---

## 2. Cloud Run 배포 (서버리스 대안)

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
*(`LETTER_API_KEY`는 REST `/api/cursive`만 보호한다 — `/mcp`에는 헤더가 필요 없다)*

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
| `MCP_TRANSPORT` | `http` | 전송 모드. `http` = Streamable HTTP(`/mcp`, stateless) / `sse` = 구식 SSE(`/sse`, 옛 클라이언트용) / 미설정·PORT 없음 = stdio |
| `LETTER_PUBLIC_BASE_URL` | *(미설정 시 로컬 경로)* | 서버 공개 주소. 설정하면 도구 답에 서버 내부 경로 대신 `https://…/images/…`·`/gallery/…` 웹 주소를 넣는다 |
| `LETTER_API_KEY` | *(미설정 시 무인증)* | `/api/cursive` REST만 보호한다 — MCP(`/mcp`)는 인증 없음 |
| `LETTER_STORAGE_DIR` | `/app/storage` | 초서 이미지 및 메타데이터 저장 경로. **Cloud Run에서는 메모리 위라 콜드 스타트마다 비워진다** — 다음 호출 때 zdic에서 다시 받는다(사용량이 적어 감수) |
