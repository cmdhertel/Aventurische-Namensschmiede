#!/usr/bin/env bash
# Test nginx rate limiting for /generate (60/min, burst 20) and /pdf (10/min, burst 3).
# Usage: ./scripts/test_ratelimit.sh https://your-domain.com
#        ./scripts/test_ratelimit.sh http://localhost:8000   # without nginx (no limiting expected)
set -euo pipefail

BASE_URL="${1:-https://aventurische-namensschmiede.de}"
GENERATE_TOTAL=90 # expect 429s after burst of 20
PDF_TOTAL=18      # expect 429s after burst of 3

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m'

ok=0
limited=0
other=0

run_generate() {
  local total=$1
  ok=0
  limited=0
  other=0
  for i in $(seq 1 "$total"); do
    code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/generate" \
      -d "region=human&gender=any&mode=simple&count=1&profession_category=alle")
    case "$code" in
    200) ok=$((ok + 1)) ;;
    429) limited=$((limited + 1)) ;;
    *)   other=$((other + 1)) ;;
    esac
    printf "\r  Request %3d/%d  — 200: %d  429: %d  other: %d" \
      "$i" "$total" "$ok" "$limited" "$other"
  done
  echo
}

run_pdf() {
  local total=$1
  ok=0
  limited=0
  other=0
  local payload='[{"first_name":"Test","last_name":"User","full_name":"Test User","gender":"male","region":"human","mode":"simple"}]'
  for i in $(seq 1 "$total"); do
    code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/pdf" \
      -F "names=$payload" -F "kind=name")
    case "$code" in
    200) ok=$((ok + 1)) ;;
    429) limited=$((limited + 1)) ;;
    *)   other=$((other + 1)) ;;
    esac
    printf "\r  Request %3d/%d  — 200: %d  429: %d  other: %d" \
      "$i" "$total" "$ok" "$limited" "$other"
  done
  echo
}

echo
echo "Target: $BASE_URL"
echo "========================================"

echo -e "\n${YELLOW}[1/2] /generate  (limit: 60/min, burst: 20, sending: $GENERATE_TOTAL)${NC}"
run_generate "$GENERATE_TOTAL"

if [[ $limited -gt 0 ]]; then
  echo -e "  ${GREEN}✓ Rate limiting active — $limited requests were throttled (429)${NC}"
else
  echo -e "  ${RED}✗ No 429s seen — rate limiting not active (direct app access or misconfigured)${NC}"
fi

echo -e "\n${YELLOW}[2/2] /pdf  (limit: 10/min, burst: 3, sending: $PDF_TOTAL)${NC}"
run_pdf "$PDF_TOTAL"

if [[ $limited -gt 0 ]]; then
  echo -e "  ${GREEN}✓ Rate limiting active — $limited requests were throttled (429)${NC}"
else
  echo -e "  ${RED}✗ No 429s seen — rate limiting not active (direct app access or misconfigured)${NC}"
fi

echo
