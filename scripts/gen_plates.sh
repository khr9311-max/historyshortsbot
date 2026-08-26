#!/usr/bin/env bash
# gen_plates.sh — 도해 배경 플레이트 3종을 절차적으로 생성한다 (CLAUDE.md §"배경 플레이트").
#
# 한 번만 실행하면 된다. 결과물은 assets_global/plates/ 에 커밋되고
# 전 에피소드가 재사용한다. 재생성비가 없으므로 pipeline.py 예산 견적에도
# 잡히지 않는다.
#
#     ./scripts/gen_plates.sh
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT/assets_global/plates"
mkdir -p "$OUT"

W=1080 H=1920 FPS=25 DUR=8
BG="0x0E1420"   # lib_style.py BG — 바이블 배경색과 동일해야 대비를 안 먹는다

# --- P_fog.mp4 — 느린 안개 흐름. 인과 다이어그램 · 통념 부정 ---
ffmpeg -y -loglevel error -f lavfi \
  -i "color=c=${BG}:s=${W}x${H}:d=${DUR}:r=${FPS},format=yuv420p,\
noise=alls=22:allf=t,gblur=sigma=48,eq=brightness=0.01:contrast=1.03" \
  -c:v libx264 -crf 18 -pix_fmt yuv420p "$OUT/P_fog.mp4"

# --- P_dust.mp4 — 빛줄기 속 먼지 입자. 타임라인 · 연표 ---
# 풀해상도에 노이즈를 얹으면 프레임마다 픽셀이 거의 독립이라 h264가
# 압축하지 못한다 (첫 시도 40MB, allf=t 만 써도 110MB). 저해상도에서
# 노이즈를 만들고 업스케일해 인접 픽셀 상관성을 만든 뒤 압축한다.
ffmpeg -y -loglevel error -f lavfi \
  -i "color=c=${BG}:s=135x240:d=${DUR}:r=${FPS},format=yuv420p,\
noise=alls=45:allf=t,gblur=sigma=2.2,scale=${W}:${H}:flags=bicubic,\
eq=brightness=-0.02:contrast=1.25" \
  -c:v libx264 -crf 26 -preset slow -pix_fmt yuv420p "$OUT/P_dust.mp4"

# --- P_grid.mp4 — 아주 느린 격자 드리프트. 그래프 · 수치 컷 ---
ffmpeg -y -loglevel error -f lavfi \
  -i "color=c=${BG}:s=$((W*11/10))x$((H*11/10)):d=${DUR}:r=${FPS},format=yuv420p,\
drawgrid=w=90:h=90:t=1:c=0x2A3442@0.35,\
zoompan=z='min(zoom+0.00035,1.03)':d=$((DUR*FPS)):x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=${W}x${H}:fps=${FPS},setsar=1" \
  -frames:v $((DUR*FPS)) \
  -c:v libx264 -crf 18 -pix_fmt yuv420p "$OUT/P_grid.mp4"

echo "OK: $OUT"
ls -la "$OUT"
