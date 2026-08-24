#!/usr/bin/env bash
# ============================================================
#  역사 인과 쇼츠 조립 파이프라인
#  사용법: ./scripts/build.sh EP007
#  입력:   episodes/EP007/scenes.tsv
#  출력:   render/EP007_final.mp4
# ============================================================
set -euo pipefail

EP="${1:?사용법: ./scripts/build.sh EP007}"
DIR="episodes/${EP}"
A="${DIR}/assets"
WORK="$(mktemp -d)"
OUT="render/${EP}_final.mp4"

W=1080; H=1920; FPS=25
GRAIN="noise=alls=8:allf=t+u"
VIGN="vignette=PI/5"
SAT="eq=saturation=0.90"
DUST="assets_global/dust_overlay.mp4"

mkdir -p render

# --- 발행 게이트: 출처 확인 --------------------------------
if grep -qE '^\|\s*\|\s*\|\s*\|\s*\|' "${DIR}/sources.md" 2>/dev/null; then
  echo "경고: sources.md에 빈 항목이 있습니다. 발행 금지 상태입니다." >&2
  echo "그래도 렌더하려면 SKIP_SOURCE_CHECK=1 을 지정하세요." >&2
  [ "${SKIP_SOURCE_CHECK:-0}" = "1" ] || exit 1
fi

# --- 정지컷: 슬로우 줌 -------------------------------------
make_still () {
  local src="$1" dst="$2" mode="$3" dur="$4"
  local frames=$(( FPS * dur ))
  local z x y
  case "$mode" in
    dolly_in) z="min(zoom+0.00096,1.12)"; x="iw/2-(iw/zoom/2)"; y="ih/2-(ih/zoom/2)" ;;
    crane_up) z="1.12"; x="iw/2-(iw/zoom/2)"; y="ih-(ih/zoom)-(on/${frames})*(ih-ih/zoom)" ;;
    orbit)    z="min(zoom+0.0006,1.08)";  x="iw/2-(iw/zoom/2)+sin(on/${frames}*PI)*40"; y="ih/2-(ih/zoom/2)" ;;
    *)        z="min(zoom+0.00096,1.12)"; x="iw/2-(iw/zoom/2)"; y="ih/2-(ih/zoom/2)" ;;
  esac
  ffmpeg -y -loglevel error -loop 1 -i "$src" \
    -vf "scale=${W}*3:${H}*3:force_original_aspect_ratio=increase,crop=${W}*3:${H}*3,\
zoompan=z='${z}':d=${frames}:x='${x}':y='${y}':s=${W}x${H}:fps=${FPS},setsar=1" \
    -t "$dur" -c:v libx264 -crf 18 -pix_fmt yuv420p "$dst"
}

# --- 영상컷 정규화 (i2v 결과 / Manim 렌더 공통) ------------
norm_clip () {
  ffmpeg -y -loglevel error -i "$1" \
    -vf "scale=${W}:${H}:force_original_aspect_ratio=increase,crop=${W}:${H},fps=${FPS},setsar=1" \
    -t "$3" -an -c:v libx264 -crf 18 -pix_fmt yuv420p "$2"
}

# --- 씬 순회 -----------------------------------------------
: > "$WORK/concat.txt"
tail -n +2 "${DIR}/scenes.tsv" | while IFS=$'\t' read -r scene kind move dur note; do
  [ -z "${scene:-}" ] && continue
  dur="${dur:-5}"
  dst="$WORK/${scene}.mp4"

  case "$kind" in
    ai_hero)
      norm_clip "${A}/clips/${scene}.mp4" "$dst" "$dur" ;;
    ai_still)
      make_still "${A}/images/${scene}.png" "$dst" "${move:-dolly_in}" "$dur" ;;
    diagram)
      # Manim 결과가 없으면 그 자리에서 렌더
      if [ ! -f "${A}/clips/${scene}.mp4" ]; then
        echo "Manim 렌더: ${scene}"
        manim -qh --format=mp4 --resolution ${W},${H} \
          "${DIR}/diagrams/${scene}.py" -o "${scene}" >/dev/null
        find media -name "${scene}.mp4" -exec cp {} "${A}/clips/${scene}.mp4" \;
      fi
      norm_clip "${A}/clips/${scene}.mp4" "$dst" "$dur" ;;
    *)
      echo "알 수 없는 kind: $kind (${scene})" >&2; exit 1 ;;
  esac

  echo "file '$dst'" >> "$WORK/concat.txt"
done

# --- 이어붙이기 --------------------------------------------
ffmpeg -y -loglevel error -f concat -safe 0 -i "$WORK/concat.txt" -c copy "$WORK/joined.mp4"

# --- 후처리 3종 + 자막 -------------------------------------
SUBFILTER=""
[ -s "${DIR}/sub.ass" ] && SUBFILTER=",ass=${DIR}/sub.ass"

ffmpeg -y -loglevel error \
  -i "$WORK/joined.mp4" -stream_loop -1 -i "$DUST" \
  -filter_complex "\
[1:v]scale=${W}:${H},format=gbrp,colorchannelmixer=aa=0.15[dust];\
[0:v][dust]blend=all_mode=screen:shortest=1[bl];\
[bl]${SAT},${GRAIN},${VIGN}${SUBFILTER}[v]" \
  -map "[v]" -c:v libx264 -crf 19 -pix_fmt yuv420p "$WORK/video.mp4"

# --- 오디오 3레이어 + 더킹 ---------------------------------
ffmpeg -y -loglevel error \
  -i "$WORK/video.mp4" \
  -i "${A}/vo/vo.wav" \
  -i "${A}/bgm/amb.wav" \
  -i "${A}/bgm/bgm.mp3" \
  -filter_complex "\
[1:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,volume=1.0[vo];\
[2:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,volume=0.20[amb];\
[3:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,volume=0.10[bg];\
[vo]asplit=2[vo1][key];\
[bg][key]sidechaincompress=threshold=0.05:ratio=8:attack=20:release=400[bgd];\
[vo1][amb][bgd]amix=inputs=3:duration=first:normalize=0[a]" \
  -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -shortest "$OUT"

rm -rf "$WORK"
echo "완료: $OUT"
