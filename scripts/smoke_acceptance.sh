#!/bin/bash
# AI Photo Template Miniapp - 本轮验收脚本
# 用法: bash scripts/smoke_acceptance.sh

set -e

HOST="http://127.0.0.1:3000"
PASS=0
FAIL=0

function check() {
  local name="$1"
  local cmd="$2"
  local expect="$3"
  echo -n "[TEST] $name ... "
  if echo "$cmd" | grep -q "$expect"; then
    echo "✅ PASS"
    ((PASS++))
  else
    echo "❌ FAIL (expected: $expect)"
    ((FAIL++))
  fi
}

echo "=== Step 1: Type Check ==="
npm run check && echo "✅ Type check passed" || { echo "❌ Type check failed"; exit 1; }

echo ""
echo "=== Step 2: Start API Server ==="
npm run api &
API_PID=$!
sleep 3

echo ""
echo "=== Step 3: Endpoint Smoke Tests ==="

# Health
check "Health endpoint" "$(curl -s $HOST/health)" '"ok": true'

# Templates list
check "Templates count=54" "$(curl -s $HOST/templates | grep -o '"template_id"' | wc -l)" "54"

# Fantasy category exists
check "Fantasy template exists" "$(curl -s $HOST/templates | grep fantasy_01)" "fantasy_01"

# Ancient category exists
check "Ancient template exists" "$(curl -s $HOST/templates | grep ancient_song_elegant)" "ancient_song_elegant"

# Images recent mock route
check "Images recent route" "$(curl -s $HOST/images/recent)" '"items": \[\]'

# COS credentials mock route
check "COS credentials route" "$(curl -s $HOST/cos/credentials)" '"error"'

echo ""
echo "=== Step 4: Git Status ==="
git log --oneline -2

echo ""
echo "=== Summary ==="
echo "Passed: $PASS"
echo "Failed: $FAIL"

# Cleanup
kill $API_PID 2>/dev/null || true

if [ $FAIL -eq 0 ]; then
  echo ""
  echo "🎉 全部验收通过！本轮收工。"
  exit 0
else
  echo ""
  echo "⚠️ 有 $FAIL 项未通过，请检查。"
  exit 1
fi
