#!/usr/bin/env bash
# LetterCollector를 Cloud Run 서울(asia-northeast3)에 배포한다 — findchem-mcp와 같은 GCP 프로젝트, 별도 서비스.
#
#   (gcloud 로그인이 먼저 되어 있어야 한다 — findchem 클라우드 세션이면 `bash scripts/gcp_auth.sh`)
#   bash scripts/deploy_cloudrun.sh
#
# 설정 이유:
# - --allow-unauthenticated: claude.ai 커스텀 커넥터는 공개 주소에만 붙는다(findchem-mcp와 같다, 2026-10-21 사용자 확인).
# - --max-instances 1: MCP 도구에 인증이 없다. 남이 주소를 알아 마구 불러도 서버 수와 zdic 호출이 1대 분으로 묶인다.
# - --min-instances 0: 안 쓰면 꺼져서 요금이 없다(대신 첫 호출이 몇 초 늦다).
# - --memory 512Mi: Pillow 격자 합성 + 메모리 위 저장소(storage/)가 메모리를 함께 쓴다.
# - --timeout 300: 처음 보는 글자는 zdic에서 수십 장을 받아 오느라 오래 걸릴 수 있다.
# - LETTER_PUBLIC_BASE_URL: 도구 답에 서버 내부 경로 대신 웹 주소를 넣기 위해 서비스 자기 주소를 넣는다.
#
# CLOUDSDK_AUTH_ACCESS_TOKEN: 클라우드 세션 환경이 넣는 토큰이 서비스 계정 로그인을 덮어써
# 인증이 실패한다(findchem 2026-10-02 실측) — gcloud 호출에서만 뺀다.
set -euo pipefail

service="${SERVICE:-letter-collector}"
region="${REGION:-asia-northeast3}"
cd "$(dirname "$0")/.."

gc() { env -u CLOUDSDK_AUTH_ACCESS_TOKEN gcloud "$@"; }
describe_url() { gc run services describe "$service" --region "$region" --format='value(status.url)'; }

# 이미 있는 서비스면 주소를 미리 안다 — 첫 배포면 비어 있고, 배포 뒤에 채운다.
url="$(describe_url 2>/dev/null || true)"
env_vars="MCP_TRANSPORT=http"
if [ -n "$url" ]; then
  env_vars="$env_vars,LETTER_PUBLIC_BASE_URL=$url"
fi

gc run deploy "$service" \
  --source . \
  --region "$region" \
  --allow-unauthenticated \
  --min-instances 0 \
  --max-instances 1 \
  --memory 512Mi \
  --cpu 1 \
  --concurrency 10 \
  --timeout 300 \
  --update-env-vars "$env_vars" \
  --quiet

if [ -z "$url" ]; then
  url="$(describe_url)"
  echo "첫 배포 — 서비스 주소를 LETTER_PUBLIC_BASE_URL로 넣는다: $url"
  gc run services update "$service" --region "$region" \
    --update-env-vars "LETTER_PUBLIC_BASE_URL=$url" --quiet
fi

echo "MCP 주소:  $url/mcp"
echo "상태 확인: $url/health"
echo "갤러리 예: $url/gallery/永"
