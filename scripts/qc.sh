#!/usr/bin/env bash
# ============================================================
#  발행 전 자동 검사
#  사용법: ./scripts/qc.sh EP001
#
#  Windows 에서는 scripts/qc.ps1 이 더 많은 항목을 본다
#  (루프 이음매 색 비교, 라우드니스, 폰트 설치 여부).
# ============================================================
set -euo pipefail

EP="${1:?사용법: ./scripts/qc.sh EP001}"
cd "$(dirname "$0")/.."
DIR="episodes/${EP}"
[ -d "$DIR" ] || { echo "에러: 디렉토리 없음: $DIR" >&2; exit 1; }

ERRORS=0
WARNINGS=0
fail() { echo "FAIL  $*"; ERRORS=$((ERRORS + 1)); }
warn() { echo "WARN  $*"; WARNINGS=$((WARNINGS + 1)); }
pass() { echo "PASS  $*"; }

# dur 은 소수다. 셸의 -lt/-gt 는 정수 전용이라 awk 로 비교한다.
# (이전 판은 총 길이 54.17 을 정수로 비교하려다 검사가 통째로 죽었다.)
fgt() { awk -v a="$1" -v b="$2" 'BEGIN{exit !(a>b)}'; }
flt() { awk -v a="$1" -v b="$2" 'BEGIN{exit !(a<b)}'; }
fabs_gt() { awk -v a="$1" -v b="$2" -v t="$3" 'BEGIN{d=a-b; if(d<0)d=-d; exit !(d>t)}'; }

vdur() { ffprobe -v error -show_entries format=duration -of csv=p=0 "$1" 2>/dev/null || echo ""; }

echo "=== QC: ${EP} ==="

# ---------- 1. 출처 ----------
echo; echo "[1] 출처"
if [ ! -f "${DIR}/sources.md" ]; then
  fail "sources.md 없음 — 발행 금지"
elif grep -qE '^\|\s*\|\s*\|\s*\|\s*\|' "${DIR}/sources.md"; then
  fail "sources.md 에 빈 항목 — 발행 금지"
else
  pass "sources.md 채워짐"
fi

# ---------- 1b. scenes.json 구조 ----------
echo; echo "[1b] scenes.json"
OUT=$(python scripts/check_scenes.py "$EP" 2>&1); RC=$?
if [ "$RC" -eq 2 ]; then
  warn "scenes.json 없음 — 구 방식 에피소드 (EP001~003)"
elif [ -z "$OUT" ]; then
  pass "구조·비트 길이 검증 통과"
else
  while IFS= read -r line; do
    case "$line" in
      FAIL*) fail "${line#FAIL }" ;;
      WARN*) warn "${line#WARN }" ;;
      *)     echo "      $line" ;;
    esac
  done <<< "$OUT"
fi

# ---------- 2. 씬 매니페스트 ----------
echo; echo "[2] 씬 매니페스트"
TSV="${DIR}/scenes.tsv"
DIAG_COUNT=0
if [ ! -f "$TSV" ]; then
  fail "scenes.tsv 없음"
else
  FIRST_KIND=$(awk -F'\t' 'NR==2{print $2}' "$TSV")
  LAST_KIND=$(awk -F'\t' 'END{print $2}' "$TSV")
  [ "$FIRST_KIND" = "ai_hero" ] || fail "1번 씬은 ai_hero 여야 함 (현재 $FIRST_KIND)"
  [ "$LAST_KIND" = "diagram" ] || fail "마지막 씬은 diagram 이어야 함 (현재 $LAST_KIND)"

  HERO=$(awk -F'\t' 'NR>1 && $2=="ai_hero"' "$TSV" | wc -l)
  STILL=$(awk -F'\t' 'NR>1 && $2=="ai_still"' "$TSV" | wc -l)
  DIAG_COUNT=$(awk -F'\t' 'NR>1 && $2=="diagram"' "$TSV" | wc -l)
  TOTAL=$(awk -F'\t' 'NR>1{s+=$4} END{printf "%.2f", s}' "$TSV")
  pass "$(awk -F'\t' 'NR>1' "$TSV" | wc -l) 컷 / ${TOTAL}s  (hero ${HERO} · still ${STILL} · diagram ${DIAG_COUNT})"

  if flt "$TOTAL" 45 || fgt "$TOTAL" 55; then
    warn "총 길이 ${TOTAL}s 가 목표 45~55s 밖"
  fi

  # diagram 3연속 금지 (바이블 §7)
  if awk -F'\t' 'NR>1{ if($2=="diagram"){r++; if(r>=3){found=1}} else r=0 } END{exit !found}' "$TSV"; then
    fail "diagram 컷 3개 연속 — 도표 피로"
  fi
fi

# ---------- 3. 도해 코드 ↔ 렌더 길이 ----------
echo; echo "[3] 도해"
DIAG_OK=1
if [ -f "$TSV" ]; then
  while IFS=$'\t' read -r scene kind move dur note; do
    [ "$kind" = "diagram" ] || continue
    PY="${DIR}/diagrams/${scene}.py"
    CLIP="${DIR}/assets/clips/${scene}.mp4"
    if [ ! -f "$PY" ]; then fail "${scene}: ${PY} 없음"; DIAG_OK=0; continue; fi
    if [ ! -f "$CLIP" ]; then warn "${scene}: 렌더 결과 없음 (build 시 자동 렌더)"; continue; fi
    [ "$PY" -nt "$CLIP" ] && warn "${scene}: .py 가 렌더보다 새로움 (build 시 자동 재렌더)"
    D=$(vdur "$CLIP")
    if [ -n "$D" ] && fabs_gt "$D" "$dur" 0.05; then
      fail "${scene}: 렌더 ${D}s vs 선언 ${dur}s — 타임라인이 밀림"
      DIAG_OK=0
    fi
  done < <(tail -n +2 "$TSV")
  [ "$DIAG_OK" = 1 ] && pass "도해 코드·렌더 길이 정합"
fi

# ---------- 4. 에셋 ----------
echo; echo "[4] 에셋"
ASSET_OK=1
for f in assets/vo/vo.wav sub.ass timing.json; do
  [ -f "${DIR}/${f}" ] || { fail "${f} 없음"; ASSET_OK=0; }
done
for f in assets/bgm/bgm.mp3 assets/bgm/amb.wav; do
  [ -f "${DIR}/${f}" ] || warn "${f} 없음 — 분위기 레이어가 빠짐"
done
[ "$ASSET_OK" = 1 ] && pass "필수 에셋 확인"

# ---------- 5. 자막 ----------
echo; echo "[5] 자막"
ASS="${DIR}/sub.ass"
if [ -f "$ASS" ]; then
  # 이전 판은 튜플 언패킹 실수로 2단 자막의 앞 절반이 항상 0초였다 (화면에 안 나옴)
  ZERO=$(awk -F',' '/^Dialogue:/ && $2==$3' "$ASS" | wc -l)
  LINES=$(grep -c '^Dialogue:' "$ASS" || true)
  if [ "$ZERO" -gt 0 ]; then fail "길이 0초인 자막 ${ZERO} 줄 — 화면에 안 나옴"
  else pass "${LINES} 줄 · 0초 자막 없음"; fi
fi

# ---------- 6. 최종 결과물 ----------
echo; echo "[6] 최종 결과물"
FINAL="render/${EP}_final.mp4"
if [ ! -f "$FINAL" ]; then
  warn "${FINAL} 없음 — build 를 먼저 실행하세요"
else
  VD=$(vdur "$FINAL")
  VO=$(vdur "${DIR}/assets/vo/vo.wav")
  pass "길이 ${VD}s"
  if [ -n "$VO" ] && awk -v a="$VO" -v b="$VD" 'BEGIN{exit !(a-b>0.05)}'; then
    fail "나레이션이 잘림 (영상 ${VD}s < 음성 ${VO}s)"
  fi
  RES=$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height \
        -of csv=p=0:s=x "$FINAL" 2>/dev/null || echo "?")
  [ "$RES" = "1080x1920" ] && pass "해상도 1080x1920" || fail "해상도 ${RES} (1080x1920 이어야 함)"
fi

echo; echo "=== 결과: 오류 ${ERRORS} · 경고 ${WARNINGS} ==="
[ "$ERRORS" -eq 0 ]
