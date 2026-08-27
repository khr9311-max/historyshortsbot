#!/usr/bin/env python3
"""
make_thumbnail.py — 쇼츠 전용 썸네일 제작기

최종 영상에서 프레임을 뽑으면 번인 자막과 훅 카드가 같이 딸려 온다.
썸네일은 원본 클립(assets/clips, assets/images)에서 깨끗한 프레임을 뽑아
전용 레이아웃을 새로 얹는다.

권원은 scenes.json 의 package.thumbnail 이다:

    "package": {
      "thumbnail": {
        "source": "V01",             # 샷 id. 없으면 thumbnail_scene 이 쓰는 샷
        "t": 5.5,                    # 클립 내 초. 없으면 thumbnail_time
        "lines": ["60만 대군이", "겨울 전에 사라졌다"],   # 최대 2줄
        "accent": "겨울 전에",        # lines 안의 부분 문자열 하나만 빨강
        "kicker": "보급선의 수학"     # 상단 작은 라벨. 생략 가능
      }
    }

사용:
    python scripts/make_thumbnail.py EP011
    python scripts/make_thumbnail.py EP011 --contact          # 후보 프레임 9장
    python scripts/make_thumbnail.py EP011 --t 6.2 --lines "60만 대군이" "겨울 전에 사라졌다"
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]

W, H = 1080, 1920

# 바이블 §1. 어두운 사진 위에 얹히므로 ACCENT 는 한 단계 밝은 값을 쓴다.
INK_LIGHT = (240, 237, 230)
ACCENT_HI = (232, 68, 52)
KICKER_INK = (196, 188, 174)
SHADOW = (6, 9, 15)

# 쇼츠 그리드·검색 카드에서 하단 26% 는 제목/조회수 오버레이가 덮는다.
# 읽혀야 하는 것은 전부 그 위에 둔다.
TEXT_TOP = 250
TEXT_MAX_W = 940
DEAD_BOTTOM = int(H * 0.26)

_FONT_DIRS = [
    Path.home() / "AppData/Local/Microsoft/Windows/Fonts",
    Path("C:/Windows/Fonts"),
]
_FONT_NAMES = [
    "Pretendard-Black.otf",
    "Pretendard-ExtraBold.otf",
    "NanumGothicExtraBold.otf",
    "malgunbd.ttf",
]


def find_font() -> Path:
    for name in _FONT_NAMES:
        for d in _FONT_DIRS:
            p = d / name
            if p.is_file():
                return p
    sys.exit("오류: 한글 볼드 폰트를 찾지 못했습니다 (Pretendard-Black 권장).")


def find_ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if not exe:
        sys.exit("오류: ffmpeg 이 PATH 에 없습니다.")
    return exe


# ------------------------------------------------------------------
# 소스 프레임
# ------------------------------------------------------------------
def resolve_source(ep_dir: Path, doc: dict, shot_id: str | None) -> tuple[Path, bool]:
    """(경로, 동영상인가). 도해 씬은 썸네일 소스로 쓰지 않는다."""
    if not shot_id:
        pkg = doc.get("package") or {}
        want = pkg.get("thumbnail_scene") or "S01"
        by_id = {s["id"]: s for s in doc["scenes"]}
        shot_id = (by_id.get(want) or {}).get("shot")
        if not shot_id:
            sys.exit(
                f"오류: {want} 는 도해 씬이라 썸네일 소스로 쓸 수 없습니다. "
                "package.thumbnail.source 에 veo/still 샷 id 를 지정하세요."
            )

    clip = ep_dir / "assets" / "clips" / f"{shot_id}.mp4"
    if clip.is_file():
        return clip, True
    img = ep_dir / "assets" / "images" / f"{shot_id}.png"
    if img.is_file():
        return img, False
    sys.exit(f"오류: {shot_id} 의 원본 자산이 없습니다 ({clip} / {img}).")


def grab(src: Path, is_video: bool, t: float, out: Path) -> None:
    if not is_video:
        Image.open(src).convert("RGB").resize((W, H), Image.LANCZOS).save(out, quality=95)
        return
    subprocess.run(
        [find_ffmpeg(), "-y", "-loglevel", "error", "-ss", f"{t:.3f}", "-i", str(src),
         "-frames:v", "1",
         "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}",
         "-q:v", "2", str(out)],
        check=True,
    )


# ------------------------------------------------------------------
# 이미지 처리
# ------------------------------------------------------------------
def _paste_mask(base: Image.Image, color: tuple[int, int, int],
                mask: Image.Image) -> Image.Image:
    out = base.copy()
    out.paste(Image.new("RGB", base.size, color), (0, 0), mask)
    return out


def _vgrad(stops) -> Image.Image:
    """[(y, alpha), ...] 를 선형 보간한 세로 그라데이션 마스크."""
    m = Image.new("L", (1, H))
    px = m.load()
    for y in range(H):
        a = stops[0][1]
        for (y0, a0), (y1, a1) in zip(stops, stops[1:]):
            if y0 <= y <= y1:
                f = 0 if y1 == y0 else (y - y0) / (y1 - y0)
                a = a0 + (a1 - a0) * f
                break
            if y > y1:
                a = a1
        px[0, y] = int(a)
    return m.resize((W, H))


def grade(im: Image.Image) -> Image.Image:
    """피드에서 형태가 보이도록 대비·채도를 올린다.

    본편은 딥 네이비 저채도가 규칙이지만 썸네일은 200px 폭 그리드에서
    경쟁한다. 원본 그대로 두면 회색 사각형으로 뭉갠다.
    """
    im = ImageEnhance.Contrast(im).enhance(1.22)
    im = ImageEnhance.Color(im).enhance(1.30)
    im = ImageEnhance.Brightness(im).enhance(1.10)
    # 약한 언샵 — 축소됐을 때 실루엣 윤곽을 살린다
    return im.filter(ImageFilter.UnsharpMask(radius=3, percent=55, threshold=3))


def scrim(im: Image.Image, block_bottom: int) -> Image.Image:
    """텍스트 블록 뒤 세로 다크닝. 어떤 프레임을 써도 글자가 읽히게 한다."""
    return _paste_mask(im, SHADOW, _vgrad([
        (0, 210), (block_bottom, 200), (block_bottom + 340, 0), (H, 0),
    ]))


def vignette(im: Image.Image) -> Image.Image:
    """하단을 눌러 쇼츠 UI 영역과 자연스럽게 이어지게 한다."""
    start = H - DEAD_BOTTOM - 240
    return _paste_mask(im, SHADOW, _vgrad([(0, 0), (start, 0), (H, 160)]))


# ------------------------------------------------------------------
# 텍스트
# ------------------------------------------------------------------
def _w(font: ImageFont.FreeTypeFont, s: str) -> int:
    b = font.getbbox(s)
    return b[2] - b[0]


def fit_font(font_path: Path, text: str, max_w: int, start: int = 170) -> ImageFont.FreeTypeFont:
    size = start
    while size > 62:
        f = ImageFont.truetype(str(font_path), size)
        if _w(f, text) <= max_w:
            return f
        size -= 4
    return ImageFont.truetype(str(font_path), 62)


def draw_line(dr: ImageDraw.ImageDraw, x: int, y: int, text: str,
              font: ImageFont.FreeTypeFont, accent: str | None) -> None:
    """accent 부분 문자열만 빨강. 나머지는 밝은 잉크. 바이블 §1 — 강조는 한 곳만."""
    if accent and accent in text:
        i = text.index(accent)
        parts = [(text[:i], INK_LIGHT), (accent, ACCENT_HI),
                 (text[i + len(accent):], INK_LIGHT)]
    else:
        parts = [(text, INK_LIGHT)]
    for s, color in parts:
        if not s:
            continue
        dr.text((x, y), s, font=font, fill=color, stroke_width=7, stroke_fill=SHADOW)
        x += _w(font, s)


def compose(frame: Path, lines: list[str], accent: str | None,
            kicker: str | None, ep: str, out: Path) -> None:
    im = grade(Image.open(frame).convert("RGB"))
    font_path = find_font()

    fonts = [fit_font(font_path, ln, TEXT_MAX_W) for ln in lines]
    # 두 줄은 같은 크기로 — 줄마다 크기가 다르면 급조한 티가 난다
    smallest = min(f.size for f in fonts)
    fonts = [ImageFont.truetype(str(font_path), smallest) for _ in lines]

    line_h = int(smallest * 1.06)
    gap = 24
    kick_h = 92 if kicker else 0
    block_h = kick_h + line_h * len(lines) + gap * (len(lines) - 1)

    im = scrim(im, TEXT_TOP + block_h)
    im = vignette(im)
    dr = ImageDraw.Draw(im)

    y = TEXT_TOP
    if kicker:
        kf = ImageFont.truetype(str(font_path), 42)
        dr.rectangle([70, y + 4, 79, y + 54], fill=ACCENT_HI)
        dr.text((104, y), kicker, font=kf, fill=KICKER_INK,
                stroke_width=5, stroke_fill=SHADOW)
        y += kick_h

    for ln, f in zip(lines, fonts):
        draw_line(dr, (W - _w(f, ln)) // 2, y, ln, f, accent)
        y += line_h + gap

    # 채널 인장 — 그리드에서 한 시리즈로 묶여 보이게 한다
    sf = ImageFont.truetype(str(font_path), 36)
    tag = "인과 #" + (ep.replace("EP", "").lstrip("0") or "0")
    dr.text((70, H - DEAD_BOTTOM - 78), tag, font=sf, fill=KICKER_INK,
            stroke_width=5, stroke_fill=SHADOW)

    im.save(out, quality=93, subsampling=0)


# ------------------------------------------------------------------
def auto_lines(doc: dict) -> list[str]:
    """hook_text 를 2줄로 쪼갠다. package.thumbnail 이 없을 때의 폴백."""
    hook = (doc.get("hook_text") or doc.get("title") or "").strip()
    words = hook.split()
    if len(words) < 3:
        return [hook]
    half, acc, cut = (len(hook) + 1) // 2, 0, len(words) // 2
    for i, w in enumerate(words):
        acc += len(w) + 1
        if acc >= half:
            cut = i + 1
            break
    return [" ".join(words[:cut]), " ".join(words[cut:])]


def contact_sheet(src: Path, is_video: bool, out: Path) -> None:
    """후보 프레임 9장. 어느 초를 쓸지 눈으로 고르라고 만든다."""
    if not is_video:
        print("  (정지 이미지 소스 — 후보 프레임이 하나뿐이라 시트를 건너뜁니다)")
        return
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(src)], capture_output=True, text=True)
    dur = float(probe.stdout.strip() or 8.0)
    font = ImageFont.truetype(str(find_font()), 34)
    with tempfile.TemporaryDirectory() as td:
        sheet = Image.new("RGB", (300 * 3, 533 * 3))
        for i in range(9):
            t = dur * (i + 0.5) / 9
            p = Path(td) / f"{i}.jpg"
            grab(src, True, t, p)
            im = Image.open(p).convert("RGB").resize((300, 533), Image.LANCZOS)
            ImageDraw.Draw(im).text((12, 12), f"{t:.1f}s", font=font,
                                    fill=(255, 255, 255), stroke_width=4,
                                    stroke_fill=SHADOW)
            sheet.paste(im, (300 * (i % 3), 533 * (i // 3)))
        sheet.save(out, quality=88)


def build(ep: str, source: str | None = None, t: float | None = None,
          lines: list[str] | None = None, accent: str | None = None,
          kicker: str | None = None, out: Path | None = None) -> Path:
    """pipeline.py 에서 직접 부르는 진입점."""
    ep_dir = ROOT / "episodes" / ep
    doc = json.loads((ep_dir / "scenes.json").read_text(encoding="utf-8"))
    pkg = doc.get("package") or {}
    cfg = pkg.get("thumbnail") or {}

    src, is_video = resolve_source(ep_dir, doc, source or cfg.get("source"))
    t = t if t is not None else float(cfg.get("t", pkg.get("thumbnail_time", 1.0)))
    lines = [l for l in (lines or cfg.get("lines") or auto_lines(doc)) if l.strip()][:2]
    accent = accent or cfg.get("accent")
    kicker = kicker if kicker is not None else cfg.get("kicker")
    out = out or ep_dir / "thumbnail.jpg"

    with tempfile.TemporaryDirectory() as td:
        frame = Path(td) / "f.jpg"
        grab(src, is_video, t, frame)
        compose(frame, lines, accent, kicker, ep, out)

    print(f"  썸네일: {out}")
    print(f"    소스 {src.name} @ {t:.2f}s · 문구 {' / '.join(lines)}"
          + (f" · 강조 '{accent}'" if accent else ""))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("episode")
    ap.add_argument("--source", help="샷 id (V01/I01). 생략하면 package 설정")
    ap.add_argument("--t", type=float, help="클립 내 초")
    ap.add_argument("--lines", nargs="*", help="썸네일 문구 (최대 2줄)")
    ap.add_argument("--accent", help="빨강으로 강조할 부분 문자열")
    ap.add_argument("--kicker", help="상단 라벨")
    ap.add_argument("--out", help="출력 경로 (기본 episodes/<EP>/thumbnail.jpg)")
    ap.add_argument("--contact", action="store_true", help="후보 프레임 시트만 만든다")
    a = ap.parse_args()

    if a.contact:
        ep_dir = ROOT / "episodes" / a.episode
        doc = json.loads((ep_dir / "scenes.json").read_text(encoding="utf-8"))
        cfg = (doc.get("package") or {}).get("thumbnail") or {}
        src, is_video = resolve_source(ep_dir, doc, a.source or cfg.get("source"))
        out = ep_dir / "thumbnail_contact.jpg"
        contact_sheet(src, is_video, out)
        print(f"  후보 시트: {out}")
        return

    build(a.episode, a.source, a.t, a.lines, a.accent, a.kicker,
          Path(a.out) if a.out else None)


if __name__ == "__main__":
    main()
