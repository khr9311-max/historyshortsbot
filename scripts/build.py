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

# --- 스타일 바이블 §6 후처리 3종 (예외 없음) ---
GRAIN = "noise=alls=8:allf=t+u"
VIGNETTE = "vignette=PI/5"
SATURATION = "eq=saturation=0.90"
DUST_OPACITY = 0.15

# --- 루프 이음매 ---
BG_HEX = "0x0E1420"   # 바이블 §1 BG
LOOP_FADE_IN = 0.35   # 첫 컷을 BG 에서 연다 (마지막 컷은 BG 로 닫힌다)
AUDIO_FADE_IN = 0.25
AUDIO_FADE_OUT = 0.90

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


def make_clip(src: Path, dst: Path, frames: int):
    """
    i2v 결과 / Manim 렌더 공통 정규화.
    tpad 로 마지막 프레임을 복제해 늘린 뒤 정확히 frames 장만 취한다.
    → 소스가 짧아도 길어도 결과는 항상 frames 장. 드리프트가 생길 수 없다.
    """
    run([FFMPEG, "-y", "-loglevel", "error", "-i", str(src),
         "-vf", (f"scale={W}:{H}:force_original_aspect_ratio=increase,"
                 f"crop={W}:{H},fps={FPS},setsar=1,"
                 f"tpad=stop_mode=clone:stop_duration=5"),
         "-frames:v", str(frames), "-an",
         "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", str(dst)])


def render_diagram(ep_dir: Path, scene: str, out: Path):
    say(f"    Manim 렌더: {scene}")
    run([sys.executable, "-m", "manim", "-qh", "--format=mp4",
         "--resolution", f"{W},{H}",
         str(ep_dir / "diagrams" / f"{scene}.py"), "-o", scene])
    hits = sorted(ROOT.glob(f"media/videos/{scene}/**/{scene}.mp4"))
    if not hits:
        sys.exit(f"오류: {scene} Manim 출력물을 찾지 못했습니다.")
    shutil.copyfile(hits[-1], out)


# ============================================================
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
    args = ap.parse_args()

    ep = args.episode
    ep_dir = ROOT / "episodes" / ep
    assets = ep_dir / "assets"
    if not ep_dir.is_dir():
        sys.exit(f"오류: {ep_dir} 가 없습니다.")

    source_gate(ep_dir)

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
            dst = work / f"{name}.mp4"
            say(f"  {name}  {kind:<8} {frames:4d}f  {frames / FPS:5.2f}s")

            if kind == "diagram":
                clip = assets / "clips" / f"{name}.mp4"
                py = ep_dir / "diagrams" / f"{name}.py"
                if not py.is_file():
                    sys.exit(f"오류: {py} 가 없습니다.")
                # 소스가 더 새로우면 다시 렌더한다 (수정하고 반영을 잊는 사고 방지)
                if not clip.is_file() or py.stat().st_mtime > clip.stat().st_mtime:
                    render_diagram(ep_dir, name, clip)
                make_clip(clip, dst, frames)

            elif kind == "ai_still":
                img = assets / "images" / f"{name}.png"
                if not img.is_file():
                    sys.exit(f"오류: {img} 가 없습니다.")
                make_still(img, dst, s.get("move") or "dolly_in", frames)

            elif kind == "ai_hero":
                clip = assets / "clips" / f"{name}.mp4"
                if clip.is_file():
                    make_clip(clip, dst, frames)
                else:  # i2v 결과가 아직 없으면 정지 이미지로 대체
                    img = assets / "images" / f"{name}.png"
                    if not img.is_file():
                        sys.exit(f"오류: {name} 의 클립도 이미지도 없습니다.")
                    say(f"    [경고] {name} i2v 클립 없음 → 정지 컷으로 대체")
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
