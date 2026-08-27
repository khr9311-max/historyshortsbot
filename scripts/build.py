"""
역사 인과 쇼츠 조립 파이프라인

    python scripts/build.py EP001
    (래퍼: ./build.sh EP001  /  .\\scripts\\build.ps1 EP001)

입력   episodes/<EP>/timing.json  (없으면 scenes.tsv)
출력   render/<EP>_final.mp4

--------------------------------------------------------------------
이전 판에서 고친 것
--------------------------------------------------------------------
1) 타임라인 드리프트
   컷을 -t 로 '자르기만' 하고 모자랄 때 늘리지 않았다. Manim 렌더가
   선언 길이보다 짧으면 그만큼 뒤가 당겨졌고, EP001 은 1.2초가 밀려
   자막이 어긋나고 -shortest 가 마지막 문장 0.76초를 잘라냈다.
   → 이제 모든 컷을 '정확한 프레임 수'로 맞춘다 (모자라면 마지막
     프레임 유지, 넘치면 절단). 프레임 경계는 timing.json 의 누적
     시각에서 뽑으므로 반올림 오차가 쌓이지 않는다.

2) 루프 이음매
   쇼츠는 자동 반복된다. 마지막 컷(S09)이 배경색으로 수렴하고,
   여기서 첫 프레임을 같은 배경색에서 열어 준다. 이음매가 BG→BG 가
   되어 반복 재생이 끊겨 보이지 않는다. 오디오도 같이 여닫는다.

3) 오디오
   환경음·BGM 이 영상보다 짧으면 뒤가 무음이 됐다 → aloop.
   맺음/시작이 툭 끊겼다 → afade. 편별 음량 편차 → loudnorm(-14 LUFS).
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

W, H, FPS = 1080, 1920, 25
CLIP_SEC = 8.0  # t2v 클립 · 배경 플레이트 공통 길이 (규칙 §2)

# --- 스타일 바이블 §6 후처리 3종 (예외 없음) ---
GRAIN = "noise=alls=8:allf=t+u"
VIGNETTE = "vignette=PI/5"
SATURATION = "eq=saturation=0.90"
DUST_OPACITY = 0.15

# --- 루프 이음매 ---
# 마지막 컷(도해, LOOP_TAIL)이 알파 0으로 수렴하면 그 자리에 도해 배경색이
# 그대로 드러난다 — 그러니 이 값은 composite_diagram() 의 PAPER_HEX 와
# 반드시 같아야 이음매가 진짜로 안 보인다. (2026-08-27 이전에는 여기가
# 딥네이비였는데, 도해 배경이 종이색이라 실제로는 이음매가 어긋나 있었다.)
BG_HEX = "0xEAE6DD"   # 바이블 §1 BG. composite_diagram.PAPER_HEX 와 동기화
LOOP_FADE_IN = 0.35   # 첫 컷을 BG 에서 연다 (마지막 컷은 BG 로 닫힌다)
AUDIO_FADE_IN = 0.25
AUDIO_FADE_OUT = 0.90

# --- 훅 카드 (0~2초) ---
# 스크롤을 멈추게 하는 큰 헤드라인 한 줄. scenes.json 의 hook_text 가 원천이다.
# 첫 자막 줄("인쇄술은" 같은 4~5글자 파편)은 0.3초에야 뜨고 그마저 짧다 —
# 스와이프 판정은 그보다 먼저 끝난다. 0초부터 화면에 정보가 있어야 한다.
HOOK_INK_HEX = "0xE8E4DC"     # 바이블 §1 INK
# 훅 카드는 첫 컷(veo, 딥네이비 AI 영상) 위에 얹힌다 — 도해의 종이 배경과는
# 다른 화면이다. 그 위에서 밝은 글자가 읽히도록 어둡게 다크닝하는 박스다.
HOOK_BOX_HEX = "0x0E1420"
HOOK_FONTSIZE = 92
HOOK_Y = 210
HOOK_DURATION = 2.0
HOOK_FADE = 0.30

# --- 오디오 레벨 (바이블 §5) ---
# 바이블의 -14dB / -20dB 는 '나레이션 대비 상대값'이다.
# 이전 판은 소스 파일에 그 값을 그냥 곱했다. 그런데 EP001 의 소스는
# 환경음 -40.5dB, BGM -45.7dB 로 나레이션(-23.4dB)보다 이미 한참 작아서
# 실제로는 -31dB, -42dB 까지 내려갔다 — 분위기 레이어가 사실상 없었다.
# 그래서 각 레이어를 먼저 측정해 목표 LUFS 로 맞춘 뒤 상대차를 적용한다.
LUFS_VO = -16.0
REL_AMB = -14.0   # 나레이션 대비
REL_BGM = -20.0
MAX_GAIN_DB = 24.0
LOUDNORM = "loudnorm=I=-14:TP=-1.5:LRA=11"


# ============================================================
def find_exe(name: str) -> str:
    p = shutil.which(name)
    if p:
        return p
    for c in (
        Path(os.environ.get("LOCALAPPDATA", "")) / f"Microsoft/WinGet/Links/{name}.exe",
        Path(f"C:/ffmpeg/bin/{name}.exe"),
        Path(os.environ.get("USERPROFILE", "")) / f"scoop/shims/{name}.exe",
    ):
        if c.is_file():
            return str(c)
    sys.exit(f"오류: {name} 을(를) 찾을 수 없습니다. PATH 에 추가하세요.")


FFMPEG = find_exe("ffmpeg")
FFPROBE = find_exe("ffprobe")


def find_font_file() -> str | None:
    """Pretendard Bold 폰트 파일 경로. drawtext 는 fontconfig 없이 파일 경로가
    필요하다(libass 의 sub.ass 와 달리). 없으면 맑은 고딕 볼드로 대체한다
    (바이블 §2 폰트 대체 규칙과 동일)."""
    for c in (
        Path("C:/Windows/Fonts/Pretendard-Bold.otf"),
        Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/Windows/Fonts/Pretendard-Bold.otf",
        Path("C:/Windows/Fonts/malgunbd.ttf"),
    ):
        if c.is_file():
            return str(c)
    return None


def _ffmpeg_path_escape(p: str) -> str:
    """filtergraph 안에서 ':' 는 key=value 구분자라 드라이브 콜론을 이스케이프한다."""
    return p.replace("\\", "/").replace(":", r"\:")


def run(args: list[str], **kw):
    kw.setdefault("cwd", ROOT)
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", **kw)
    if r.returncode != 0:
        sys.exit(f"오류: 명령 실패\n  {' '.join(args[:6])} ...\n{(r.stderr or '')[-1800:]}")
    return r


def probe(path: Path) -> float:
    r = run([FFPROBE, "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(path)])
    return float(r.stdout.strip())


def measure_lufs(path: Path) -> float | None:
    """통합 라우드니스(LUFS). 측정 불가면 None."""
    import re
    r = subprocess.run(
        [FFMPEG, "-hide_banner", "-nostats", "-i", str(path),
         "-af", "ebur128=framelog=quiet", "-f", "null", "-"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=ROOT,
    )
    hits = re.findall(r"^\s*I:\s*(-?\d+(?:\.\d+)?)\s*LUFS", r.stderr or "", re.M)
    if not hits:
        return None
    val = float(hits[-1])
    return None if val < -70 else val


def gain_to(path: Path, target_lufs: float, label: str) -> float:
    """목표 LUFS 에 맞추기 위한 고정 게인(dB). 동적 압축이 아니라 정적 게인이라
    앰비언트가 펌핑되지 않는다."""
    lufs = measure_lufs(path)
    if lufs is None:
        say(f"    [경고] {label} 라우드니스 측정 실패 — 게인 0dB")
        return 0.0
    g = max(min(target_lufs - lufs, MAX_GAIN_DB), -MAX_GAIN_DB)
    say(f"    {label:<4} {lufs:7.1f} LUFS → 목표 {target_lufs:6.1f}  게인 {g:+.1f}dB")
    return g


def say(msg: str):
    print(msg, flush=True)


# ============================================================
# 씬 목록 · 프레임 경계
# ============================================================
def load_scenes(ep_dir: Path) -> tuple[list[dict], float | None]:
    """
    timing.json 이 있으면 그쪽의 누적 시각을 쓴다 (오디오와 샘플 단위로 일치).
    없으면 scenes.tsv 의 dur 을 누적한다.
    """
    tj = ep_dir / "timing.json"
    if tj.is_file():
        data = json.loads(tj.read_text(encoding="utf-8"))
        return data["scenes"], float(data["total"])

    tsv = ep_dir / "scenes.tsv"
    if not tsv.is_file():
        sys.exit(f"오류: {tsv} 가 없습니다.")
    scenes, t = [], 0.0
    with tsv.open(encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            if not (row.get("scene") or "").strip():
                continue
            d = float(row.get("dur") or 5)
            scenes.append(dict(scene=row["scene"], kind=row["kind"],
                               move=row.get("move") or "-", start=t, end=t + d))
            t += d
    return scenes, None


def frame_plan(scenes: list[dict]) -> list[int]:
    """누적 시각을 프레임으로 환산해 컷별 프레임 수를 낸다 (오차가 쌓이지 않는다)."""
    plan, prev = [], 0
    for s in scenes:
        edge = int(round(float(s["end"]) * FPS))
        plan.append(max(edge - prev, 1))
        prev = edge
    return plan


# ============================================================
# 컷 만들기
# ============================================================
def zoompan(move: str, frames: int) -> str:
    """정지 이미지 슬로우 줌 — 바이블 §4 카메라 무브 3종."""
    if move == "crane_up":
        z, x = "1.12", "iw/2-(iw/zoom/2)"
        y = f"ih-(ih/zoom)-(on/{frames})*(ih-ih/zoom)"
    elif move == "orbit":
        z = "min(zoom+0.0006,1.08)"
        x = f"iw/2-(iw/zoom/2)+sin(on/{frames}*PI)*40"
        y = "ih/2-(ih/zoom/2)"
    else:  # dolly_in (기본)
        z, x, y = "min(zoom+0.00096,1.12)", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    return (
        f"scale={W*3}:{H*3}:force_original_aspect_ratio=increase,crop={W*3}:{H*3},"
        f"zoompan=z='{z}':d={frames}:x='{x}':y='{y}':s={W}x{H}:fps={FPS},setsar=1"
    )


def make_still(src: Path, dst: Path, move: str, frames: int):
    run([FFMPEG, "-y", "-loglevel", "error", "-loop", "1", "-i", str(src),
         "-vf", zoompan(move, frames), "-frames:v", str(frames),
         "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", str(dst)])


def make_clip(src: Path, dst: Path, frames: int, offset: float = 0.0):
    """
    t2v 결과 / Manim 렌더 공통 정규화.
    tpad 로 마지막 프레임을 복제해 늘린 뒤 정확히 frames 장만 취한다.
    → 소스가 짧아도 길어도 결과는 항상 frames 장. 드리프트가 생길 수 없다.

    offset: 8초 2비트 클립에서 비트 B 가 시작하는 지점(초).
            fps 정규화 뒤에 프레임 번호로 잘라내 반올림 오차가 남지 않는다.
    """
    chain = (f"scale={W}:{H}:force_original_aspect_ratio=increase,"
             f"crop={W}:{H},fps={FPS},setsar=1")
    if offset > 0:
        chain += f",trim=start_frame={int(round(offset * FPS))},setpts=PTS-STARTPTS"
    chain += ",tpad=stop_mode=clone:stop_duration=5"
    run([FFMPEG, "-y", "-loglevel", "error", "-i", str(src),
         "-vf", chain, "-frames:v", str(frames), "-an",
         "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", str(dst)])


def render_diagram(ep_dir: Path, scene: str, out: Path):
    """알파 채널 렌더 (qtrle/.mov). 배경은 build.py 가 플레이트와 합성한다."""
    say(f"    Manim 렌더: {scene} (투명)")
    run([sys.executable, "-m", "manim", "-qh", "-t",
         "--resolution", f"{W},{H}",
         str(ep_dir / "diagrams" / f"{scene}.py"), "-o", scene])
    hits = sorted(ROOT.glob(f"media/videos/{scene}/**/{scene}.mov"))
    if not hits:
        sys.exit(f"오류: {scene} Manim 출력물을 찾지 못했습니다.")
    shutil.copyfile(hits[-1], out)


# ============================================================
# 배경 합성 — 도해(알파) 를 종이 배경 위에 얹는다
# ============================================================
# 2026-08-27 이전에는 이 자리에서 assets_global/plates/ 의 딥네이비 루프를
# 눌러 깐 뒤 그 위에 도해를 얹었다 — AI 컷과 톤을 맞추려는 시도였다.
#
# 그런데 lib_style.py 는 애초에 그 가정을 따라간 적이 없다. DiagramScene 은
# 항상 `camera.background_color = BG`(#EAE6DD, 오래된 종이) 로 시작하고,
# backdrop() 의 모눈종이 격자는 MUTE, card() 는 #F9F8F6 백지를 칠한다 —
# 전부 밝은 종이 위에서 읽히도록 설계돼 있었다. 배경만 딥네이비로 눌러
# 놨더니 화면의 8할이 죽은 암흑이 되고 모눈 격자는 거의 안 보였다.
#
# 바이블 §0 원안대로 돌린다: "딥네이비 AI 컷과 확연히 대비되는 밝은 종이".
# 정지 톤 방지는 플레이트가 아니라 DiagramScene 의 DRIFT(느린 줌인)와
# 단계별 reveal 애니메이션이 이미 맡고 있다 — 모든 도해 씬이 DRIFT 를
# 0이 아닌 값으로 쓴다. 그래서 여기서는 순수 배경색이면 충분하다.
PAPER_HEX = "0xEAE6DD"   # lib_style.BG 와 반드시 같은 값


def composite_diagram(alpha_src: Path, dst: Path, frames: int):
    """투명 도해 위에 종이색 배경을 깔아 합성한다."""
    dur = frames / FPS + 0.5
    diagram_chain = f"fps={FPS},format=yuva420p,tpad=stop_mode=clone:stop_duration=5"
    fc = (f"color=c={PAPER_HEX}:s={W}x{H}:r={FPS}:d={dur},format=rgba[bg];"
          f"[0:v]{diagram_chain}[fg];"
          f"[bg][fg]overlay=0:0:format=auto[v]")
    run([FFMPEG, "-y", "-loglevel", "error",
         "-i", str(alpha_src),
         "-filter_complex", fc, "-map", "[v]",
         "-frames:v", str(frames),
         "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", str(dst)])


# ============================================================
def hook_overlay_filter(text: str, work: Path) -> str | None:
    """0~2초 훅 카드 drawtext 필터 문자열. 폰트가 없으면 None (건너뛴다)."""
    font = find_font_file()
    if font is None:
        say("  [경고] Pretendard/맑은 고딕 폰트를 찾지 못해 훅 카드를 건너뜁니다.")
        return None
    txt_file = work / "hook.txt"
    txt_file.write_text(text, encoding="utf-8")
    fontfile = _ffmpeg_path_escape(font)
    textfile = _ffmpeg_path_escape(str(txt_file))
    # 필터 값은 작은따옴표로 감싸 filtergraph 파서(콤마=필터 구분자)로부터
    # 보호한다 — 따옴표 안의 콤마는 표현식 파서(if/lt/gt 인자 구분)에 그대로
    # 넘어가야 하므로 여기서 추가로 이스케이프하지 않는다.
    fade = (f"if(lt(t,{HOOK_FADE}),t/{HOOK_FADE},"
            f"if(gt(t,{HOOK_DURATION - HOOK_FADE}),max(0,({HOOK_DURATION}-t)/{HOOK_FADE}),1))")
    return (
        f"drawtext=fontfile='{fontfile}':textfile='{textfile}':"
        f"fontsize={HOOK_FONTSIZE}:fontcolor={HOOK_INK_HEX}:"
        f"x=(w-text_w)/2:y={HOOK_Y}:"
        f"box=1:boxcolor={HOOK_BOX_HEX}@0.72:boxborderw=22:"
        f"enable='lt(t,{HOOK_DURATION})':alpha='{fade}'"
    )


def source_gate(ep_dir: Path):
    """sources.md 가 비어 있으면 발행 금지 (바이블 §8)."""
    src = ep_dir / "sources.md"
    if not src.is_file():
        sys.exit("오류: sources.md 가 없습니다. 발행 금지 상태입니다.")
    text = src.read_text(encoding="utf-8")
    import re
    if re.search(r"^\|\s*\|\s*\|\s*\|\s*\|", text, re.M):
        if os.environ.get("SKIP_SOURCE_CHECK") != "1":
            sys.exit("오류: sources.md 에 빈 항목이 있습니다. 발행 금지 상태입니다.\n"
                     "      그래도 렌더하려면 SKIP_SOURCE_CHECK=1 을 지정하세요.")
        say("  [경고] sources.md 빈 항목 — 검사를 건너뜁니다.")


# ============================================================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode")
    ap.add_argument("--keep-work", action="store_true")
    ap.add_argument(
        "--allow-still-fallback", action="store_true",
        help="veo 클립이 없을 때 정지 이미지로 대체하고 계속 진행한다 "
             "(기본은 중단). 확인용 가조립에만 쓰고 발행본에는 쓰지 말 것.")
    args = ap.parse_args()

    ep = args.episode
    ep_dir = ROOT / "episodes" / ep
    assets = ep_dir / "assets"
    if not ep_dir.is_dir():
        sys.exit(f"오류: {ep_dir} 가 없습니다.")

    source_gate(ep_dir)

    scenes_json = ep_dir / "scenes.json"
    hook_text = ""
    if scenes_json.is_file():
        hook_text = (json.loads(scenes_json.read_text(encoding="utf-8"))
                     .get("hook_text", "") or "").strip()

    scenes, total = load_scenes(ep_dir)
    plan = frame_plan(scenes)
    total_frames = sum(plan)
    say(f"[{ep}] {len(scenes)} 컷 / {total_frames} 프레임 "
        f"({total_frames / FPS:.2f}s @ {FPS}fps)")

    work = Path(tempfile.mkdtemp(prefix=f"{ep}_"))
    try:
        # ---------- 1. 컷 ----------
        concat = []
        for s, frames in zip(scenes, plan):
            name, kind = s["scene"], s["kind"]
            # veo/still 원본은 씬이 아니라 **샷** 이름을 쓴다 (8초 클립 하나가 씬 둘을 채운다).
            # 샷 표기가 없는 옛 에피소드는 씬 이름이 곧 샷 이름이다.
            shot = s.get("shot") or name
            offset = float(s.get("clip_offset") or 0.0)
            dst = work / f"{name}.mp4"
            tag = f"{shot}" + (f" @{offset:.2f}s" if offset else "")
            say(f"  {name}  {kind:<8} {frames:4d}f  {frames / FPS:5.2f}s  ← {tag}")

            if kind == "diagram":
                clip = assets / "clips" / f"{name}.mov"
                py = ep_dir / "diagrams" / f"{name}.py"
                if not py.is_file():
                    sys.exit(f"오류: {py} 가 없습니다.")
                # 소스가 더 새로우면 다시 렌더한다 (수정하고 반영을 잊는 사고 방지)
                if not clip.is_file() or py.stat().st_mtime > clip.stat().st_mtime:
                    render_diagram(ep_dir, name, clip)
                composite_diagram(clip, dst, frames)

            elif kind == "ai_still":
                img = assets / "images" / f"{shot}.png"
                if not img.is_file():
                    sys.exit(f"오류: {img} 가 없습니다.")
                make_still(img, dst, s.get("move") or "dolly_in", frames)

            elif kind == "ai_hero":
                clip = assets / "clips" / f"{shot}.mp4"
                if clip.is_file():
                    src_len = probe(clip)
                    need = offset + frames / FPS
                    if src_len + 0.05 < need:
                        say(f"    [경고] {shot} 이 {src_len:.2f}s 인데 "
                            f"{need:.2f}s 지점까지 필요합니다 → 끝 프레임을 복제합니다.")
                    make_clip(clip, dst, frames, offset)
                else:
                    # veo 샷인데 클립이 없다. 예전에는 조용히 정지 이미지로 대체하고
                    # 빌드를 통과시켰는데, 그러면 유료 생성을 건너뛴 게 '렌더 성공'
                    # 으로 보인다. EP010 이 그렇게 전편 정지 화면으로 나갔다 —
                    # veo 6컷이 전부 zoompan 스틸이었고 아무도 몰랐다.
                    img = assets / "images" / f"{shot}.png"
                    if not img.is_file():
                        sys.exit(f"오류: {shot} 의 클립도 이미지도 없습니다.")
                    if not args.allow_still_fallback:
                        sys.exit(
                            f"오류: {shot} 은 veo 샷인데 "
                            f"{assets / 'clips' / f'{shot}.mp4'} 가 없습니다.\n"
                            "      정지 이미지로 대체하면 그 컷은 움직이지 않습니다 — "
                            "첫 3초가 정지면 배포가 열리지 않습니다.\n"
                            "      pipeline.py 의 video 단계로 클립을 생성하거나, "
                            "확인용 가조립이면 --allow-still-fallback 을 붙이세요.\n"
                            "      정말 정지 컷으로 갈 거면 scenes.json 에서 "
                            f"{shot} 의 kind 를 still 로 바꾸세요.")
                    say(f"    [경고] {shot} t2v 클립 없음 → 정지 컷으로 대체 "
                        "(--allow-still-fallback). 발행본으로 쓰지 마세요.")
                    make_still(img, dst, s.get("move") or "dolly_in", frames)
            else:
                sys.exit(f"오류: 알 수 없는 kind '{kind}' ({name})")
            concat.append(dst)

        # ---------- 2. 이어붙이기 (하드컷) ----------
        lst = work / "concat.txt"
        lst.write_text(
            "".join(f"file '{p.as_posix()}'\n" for p in concat), encoding="utf-8"
        )
        joined = work / "joined.mp4"
        run([FFMPEG, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
             "-i", str(lst), "-c", "copy", str(joined)])

        # ---------- 3. 후처리 + 자막 + 루프 이음매 ----------
        dust = ROOT / "assets_global" / "dust_overlay.mp4"
        sub = ep_dir / "sub.ass"
        # 필터에서 콜론을 피하려고 리포지토리 루트 기준 상대경로를 쓴다
        sub_rel = sub.relative_to(ROOT).as_posix()

        chain = f"[bl]{SATURATION},{GRAIN},{VIGNETTE}"
        if hook_text:
            hook_filter = hook_overlay_filter(hook_text, work)
            if hook_filter:
                chain += f",{hook_filter}"
                say(f"  훅 카드: \"{hook_text}\" (0~{HOOK_DURATION:.1f}s)")
        if sub.is_file() and sub.stat().st_size > 0:
            chain += f",ass={sub_rel}"
        # 마지막 컷은 BG 로 수렴한다. 첫 프레임도 BG 에서 열어 루프를 잇는다.
        chain += f",fade=t=in:st=0:d={LOOP_FADE_IN}:color={BG_HEX}[v]"

        video = work / "video.mp4"
        if dust.is_file():
            # 먼지 오버레이 합성 — 두 입력의 픽셀 포맷을 '둘 다' 명시해야 한다.
            #
            # 이전 판은 먼지 쪽만 gbrp 로 바꾸고 베이스는 yuv420p 로 뒀다.
            # blend 의 포맷 협상이 YUV 평면을 GBR 로 잘못 읽어 영상 전체가
            # 자홍색으로 물들었다 (평균색 #0E181D → #862E9B). 화면이 어두워
            # 눈에 잘 안 띄었을 뿐 모든 컷에 걸려 있던 문제다.
            #
            # 투명도도 colorchannelmixer=aa 로 줬는데 gbrp 에는 알파 평면이
            # 없어 그냥 무시됐다. blend 자체의 all_opacity 를 쓴다.
            fc = (f"[1:v]scale={W}:{H},setsar=1,format=gbrp[dust];"
                  f"[0:v]format=gbrp[base];"
                  f"[base][dust]blend=all_mode=screen:"
                  f"all_opacity={DUST_OPACITY}:shortest=1[bl];" + chain)
            inputs = ["-i", str(joined), "-stream_loop", "-1", "-i", str(dust)]
        else:
            say("  [경고] dust_overlay.mp4 없음 — 먼지 레이어를 건너뜁니다.")
            fc = "[0:v]null[bl];" + chain
            inputs = ["-i", str(joined)]

        run([FFMPEG, "-y", "-loglevel", "error", *inputs,
             "-filter_complex", fc, "-map", "[v]",
             "-frames:v", str(total_frames),
             "-c:v", "libx264", "-crf", "19", "-preset", "slow",
             "-pix_fmt", "yuv420p", str(video)])

        # ---------- 4. 오디오 3레이어 ----------
        dur = total_frames / FPS
        vo = assets / "vo" / "vo.wav"
        amb = assets / "bgm" / "amb.wav"
        bgm = assets / "bgm" / "bgm.mp3"
        if not vo.is_file():
            sys.exit(f"오류: {vo} 가 없습니다. generate_audio_and_subs.py 를 먼저 실행하세요.")

        say("  오디오 레벨 정렬:")
        g_vo = gain_to(vo, LUFS_VO, "VO")

        # 입력 0 은 무음 영상이므로 오디오 입력은 1번부터 시작한다
        a_in, parts, mix = ["-i", str(vo)], [], []
        parts.append(f"[1:a]aformat=sample_fmts=fltp:sample_rates=48000:"
                     f"channel_layouts=stereo,volume={g_vo:.2f}dB,"
                     f"apad,atrim=0:{dur:.3f},asetpts=N/SR/TB[vo]")
        parts.append("[vo]asplit=2[vo1][key]")
        mix.append("[vo1]")
        idx = 2

        if amb.is_file():
            g = gain_to(amb, LUFS_VO + REL_AMB, "환경음")
            parts.append(f"[{idx}:a]aformat=sample_fmts=fltp:sample_rates=48000:"
                         f"channel_layouts=stereo,aloop=loop=-1:size=2000000000,"
                         f"atrim=0:{dur:.3f},asetpts=N/SR/TB,volume={g:.2f}dB[amb]")
            a_in += ["-i", str(amb)]
            mix.append("[amb]")
            idx += 1
        if bgm.is_file():
            g = gain_to(bgm, LUFS_VO + REL_BGM, "BGM")
            parts.append(f"[{idx}:a]aformat=sample_fmts=fltp:sample_rates=48000:"
                         f"channel_layouts=stereo,aloop=loop=-1:size=2000000000,"
                         f"atrim=0:{dur:.3f},asetpts=N/SR/TB,volume={g:.2f}dB[bgraw]")
            # 나레이션이 나올 때 BGM 을 눌러 준다 (바이블 §5 자동 더킹)
            parts.append("[bgraw][key]sidechaincompress="
                         "threshold=0.05:ratio=8:attack=20:release=400[bgd]")
            a_in += ["-i", str(bgm)]
            mix.append("[bgd]")
            idx += 1
        else:
            parts.append("[key]anullsink")

        fo = max(dur - AUDIO_FADE_OUT, 0.0)
        parts.append(
            f"{''.join(mix)}amix=inputs={len(mix)}:duration=longest:normalize=0,"
            f"afade=t=in:st=0:d={AUDIO_FADE_IN},"
            f"afade=t=out:st={fo:.3f}:d={AUDIO_FADE_OUT},"
            f"{LOUDNORM},atrim=0:{dur:.3f},asetpts=N/SR/TB[a]"
        )

        out = ROOT / "render" / f"{ep}_final.mp4"
        out.parent.mkdir(exist_ok=True)
        run([FFMPEG, "-y", "-loglevel", "error", "-i", str(video), *a_in,
             "-filter_complex", ";".join(parts),
             "-map", "0:v", "-map", "[a]",
             "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
             "-movflags", "+faststart", str(out)])

        # ---------- 5. 검증 ----------
        got = probe(out)
        vo_len = probe(vo)
        say(f"\n완료: {out.relative_to(ROOT)}")
        say(f"  길이     {got:.2f}s   (계획 {dur:.2f}s / 나레이션 {vo_len:.2f}s)")
        if abs(got - dur) > 0.12:
            say(f"  [경고] 계획 길이와 {abs(got - dur):.2f}s 차이가 납니다.")
        if vo_len - got > 0.05:
            say(f"  [경고] 나레이션이 {vo_len - got:.2f}s 잘렸습니다.")
        if total is not None and abs(dur - total) > 0.12:
            say(f"  [경고] timing.json 총 길이({total:.2f}s)와 어긋납니다.")
    finally:
        if args.keep_work:
            say(f"  작업 폴더 유지: {work}")
        else:
            shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
