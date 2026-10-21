# 팩: Windows / PowerShell (Windows에서 개발할 때)

> 선택형 팩 — 이 프로젝트에 해당 없으면 이 파일을 삭제한다.
> Antigravity 환경의 대상 OS가 Windows일 때 적용된다.

---

## 1. 인코딩 및 콘솔 (Encoding & Console)

- **임시 `.ps1` 스크립트는 주석까지 가급적 ASCII로 작성한다.** AI 도구가 파일을 쓸 때 UTF-8(BOM 없음)을 사용하지만, Windows 기본 PowerShell 5.1이 이를 ANSI(CP949)로 해석하여 구문 오류를 낼 수 있다.
- **콘솔 기본 코덱(CP949) 충돌 방지**:
  - Python 프로세스 실행 시 `PYTHONIOENCODING=utf-8` 및 `PYTHONUTF8=1` 환경변수를 필수로 설정한다.
  - MCP 서버 stdio 스트림은 반드시 `sys.stdout.reconfigure(encoding='utf-8')`로 UTF-8을 보장해야 한글 파라미터/응답이 깨지지 않는다.

---

## 2. PowerShell 함정 (Gotchas)

- **여러 줄 문자열을 네이티브 exe(git 등)에 인라인/here-string으로 넘기면 인용부호(`"`)가 깨진다.** 커밋 메시지는 파일에 쓰고 `git commit -F <파일>`로 전달한다.
- **PowerShell로 여러 줄 텍스트 치환(`(Get-Content ...) -replace ...`)을 하지 않는다.** Antigravity의 파일 편집 도구(`replace_file_content` 등)를 직접 사용하라.
- **빈 문자열 인자를 삼키는 문제**: PowerShell은 `""`를 빈 인자가 아닌 인자 생략으로 처리하는 경우가 있으므로 주의한다.
- **`pkill`이나 `kill -9`는 동작하지 않는다.** 백그라운드 프로세스 정리는 `Stop-Process -Name <프로세스명>` 또는 `taskkill /F /PID <PID>`를 사용한다.
- **경로 구분자 표기**: Windows에서는 역슬래시(`\`)가 이스케이프 문자로 동작할 수 있으므로, JSON 설정 파일이나 코드 내에서는 슬래시(`/`)를 쓰거나 이중 역슬래시(`\\`)를 사용한다.

---

## 3. Windows 및 Python 일반

- **네이티브 Windows Python 빌드를 사용한다.** MSYS2, Cygwin, WSL 환경의 파이썬 인터프리터와 혼용 시 절대 경로 해석 차이로 MCP 서버 프로세스가 기동되지 않을 수 있다.
- **열려 있는 파일은 덮어쓸 수 없다 (`WinError 32: 다른 프로세스가 파일을 사용 중이기 때문에 프로세스가 액세스할 수 없습니다`).** 실행 중인 서버 프로세스나 열려 있는 로그/DB 파일은 반드시 프로세스나 핸들을 해제한 뒤 수정해야 한다.
- **가상환경 실행 경로**: Windows에서는 `.venv/bin/python` 대신 `.venv\Scripts\python.exe` 경로를 명시해야 한다.

---

## 4. Antigravity 환경 유의점

자세한 내용은 `노하우_승인_최소화.md` 참고.
- 명령 실행 전 항상 `run_command` 호출 시 사용자 승인이 필요함을 염두에 두고 불필요한 호출을 자제한다.
- 현재 실행 셸이 PowerShell인지 확인하고 문법에 맞는 명령을 내린다.
