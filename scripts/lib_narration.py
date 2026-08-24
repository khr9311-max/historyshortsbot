"""
lib_narration.py — 나레이션 · 자막 · 컷 길이 생성기 (공용)

에피소드 쪽 `generate_audio_and_subs.py` 는 대본(BEATS)만 들고 있고
실제 처리는 전부 여기서 한다.

    from lib_narration import Beat, generate
    generate("EP001", BEATS)

이 모듈이 타임라인의 '단일 권원'이다.
문장 단위로 TTS 를 따로 뽑고 문장 사이 정지 구간을 직접 삽입해
샘플 단위로 정확한 시각을 계산한 뒤 넷을 동시에 출력한다.

    assets/vo/vo.wav   나레이션 (48kHz / stereo / 16bit)
    sub.ass            번인 자막 (실측 시각)
    scenes.tsv         씬 매니페스트 (실측 길이)
    timing.json        build/qc 용 검증 데이터

이렇게 해야 오디오·자막·컷 길이가 어긋날 수 없다.
(초기 판은 SentenceBoundary 이벤트에 의존하고 컷 길이를 손으로 적어
 1.2초 드리프트가 누적됐고, 마지막 문장이 잘려나갔다.)
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import wave
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# ============================================================
# 스타일 바이블 상수 (docs/02_스타일_바이블.md)
# ============================================================
INK = "#E8E4DC"
ACCENT = "#E4483A"
SUB = "#F2A73B"

FONT = "Pretendard"          # 바이블 §2
SUB_FONTSIZE = 80            # 한글 글자높이 ≈ 64px ≈ 화면 폭 5.9%
SUB_OUTLINE = 3.5            # 검정 스트로크
SUB_MARGIN_V = 300           # 쇼츠 하단 UI 회피
SUB_MARGIN_H = 70

# 바이블 §5: 남성 저음, 차분한 분석가, 속도 0.95배. 음성 변경 금지.
VOICE = "ko-KR-InJoonNeural"
RATE = "-5%"
PITCH = "-2Hz"

SR, CHANNELS, SAMPWIDTH = 48000, 2, 2

LEAD_IN = 0.30   # 도입부 정적 — 바이블 §5
TAIL = 1.25      # 마지막 여운 + 루프 수렴 구간 (바이블 §11)

TARGET_MIN, TARGET_MAX = 45.0, 55.0


# ============================================================
@dataclass
class Beat:
    """대본 한 덩어리 = 컷 하나.

    scene : "S01"
    kind  : ai_hero | ai_still | diagram
    move  : dolly_in | orbit | crane_up  (diagram 이면 "-")
    vo    : 나레이션 원문
    subs  : 화면 자막. *별표* 로 감싼 구간이 ACCENT 색. 한 컷 최대 2줄.
    pause : 이 문장 뒤 정지 길이(초). 컷 전환은 이 정지 구간에서 일어난다.
    """
    scene: str
    kind: str
    vo: str
    subs: list[str] = field(default_factory=list)
    move: str = "-"
    pause: float = 0.40
    note: str = ""

    def __post_init__(self):
        if not self.subs:
            self.subs = [self.vo]


# ============================================================
def find_ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    for c in (
        Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/WinGet/Links/ffmpeg.exe",
        Path("C:/ffmpeg/bin/ffmpeg.exe"),
        Path(os.environ.get("USERPROFILE", "")) / "scoop/shims/ffmpeg.exe",
    ):
        if c.is_file():
            return str(c)
    sys.exit("ffmpeg 를 찾을 수 없습니다. PATH 에 추가하세요.")


def hex_to_ass(h: str) -> str:
    """#RRGGBB -> ASS 의 BBGGRR (BGR 순서)"""
    h = h.lstrip("#")
    return f"{h[4:6]}{h[2:4]}{h[0:2]}".upper()


ASS_INK, ASS_ACCENT, ASS_SUB = hex_to_ass(INK), hex_to_ass(ACCENT), hex_to_ass(SUB)


def markup(s: str) -> str:
    """*강조* -> ASS 색 태그. 강조가 끝나면 기본색으로 복귀."""
    return re.sub(r"\*(.+?)\*", rf"{{\\c&H{ASS_ACCENT}&}}\1{{\\c&H{ASS_INK}&}}", s)


def plain(s: str) -> str:
    return s.replace("*", "")


def ass_time(t: float) -> str:
    t = max(t, 0.0)
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    cs = int(round((s - int(s)) * 100))
    s = int(s)
    if cs >= 100:
        cs, s = 0, s + 1
    return f"{int(h)}:{int(m):02d}:{s:02d}.{cs:02d}"


def silence(seconds: float) -> bytes:
    return b"\x00" * (int(round(seconds * SR)) * CHANNELS * SAMPWIDTH)


def _sec(pcm: bytearray) -> float:
    return len(pcm) // (CHANNELS * SAMPWIDTH) / float(SR)


# ============================================================
async def _synth(text: str, out_mp3: Path):
    import edge_tts
    comm = edge_tts.Communicate(text, voice=VOICE, rate=RATE, pitch=PITCH)
    with open(out_mp3, "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])


def _decode(ffmpeg: str, mp3: Path, wav: Path):
    """문장 앞뒤의 무음을 잘라내 정지 길이를 우리가 통제한다."""
    trim = ("silenceremove=start_periods=1:start_silence=0.02:"
            "start_threshold=-50dB:detection=peak")
    subprocess.run(
        [ffmpeg, "-y", "-loglevel", "error", "-i", str(mp3),
         "-ar", str(SR), "-ac", str(CHANNELS), "-c:a", "pcm_s16le",
         "-af", f"{trim},areverse,{trim},areverse", str(wav)],
        check=True,
    )


async def _run(ep: str, beats: list[Beat]):
    ffmpeg = find_ffmpeg()
    ep_dir = ROOT / "episodes" / ep
    (ep_dir / "assets" / "vo").mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="vo_"))

    pcm = bytearray(silence(LEAD_IN))
    timeline = []
    print(f"음성: {VOICE}  속도 {RATE}  피치 {PITCH}\n")

    for i, b in enumerate(beats):
        mp3, wav = tmp / f"{b.scene}.mp3", tmp / f"{b.scene}.wav"
        await _synth(plain(b.vo), mp3)
        _decode(ffmpeg, mp3, wav)

        with wave.open(str(wav), "rb") as w:
            assert w.getframerate() == SR and w.getnchannels() == CHANNELS
            data = w.readframes(w.getnframes())

        speech_start = _sec(pcm)
        pcm += data
        speech_end = _sec(pcm)

        pause = b.pause if i < len(beats) - 1 else TAIL
        pcm += silence(pause)
        beat_end = _sec(pcm)

        timeline.append(dict(scene=b.scene, kind=b.kind, move=b.move, note=b.note,
                             speech_start=speech_start, speech_end=speech_end,
                             beat_end=beat_end, subs=b.subs, vo=plain(b.vo)))
        print(f"  {b.scene}  발화 {speech_end - speech_start:5.2f}s  "
              f"+정지 {pause:4.2f}s  → 누적 {beat_end:6.2f}s")

    total = _sec(pcm)

    # --- vo.wav ---
    with wave.open(str(ep_dir / "assets" / "vo" / "vo.wav"), "wb") as w:
        w.setnchannels(CHANNELS)
        w.setsampwidth(SAMPWIDTH)
        w.setframerate(SR)
        w.writeframes(bytes(pcm))

    # --- 씬 경계 = 비트 경계 (컷은 항상 정지 구간에서 일어난다) ---
    scenes, prev = [], 0.0
    for i, t in enumerate(timeline):
        end = total if i == len(timeline) - 1 else t["beat_end"]
        scenes.append(dict(t, start=prev, end=end, dur=round(end - prev, 3)))
        prev = end

    # --- scenes.tsv ---
    rows = ["scene\tkind\tmove\tdur\tnote"]
    rows += [f"{s['scene']}\t{s['kind']}\t{s['move']}\t{s['dur']:.2f}\t{s['note']}"
             for s in scenes]
    (ep_dir / "scenes.tsv").write_text("\n".join(rows) + "\n", encoding="utf-8")

    # --- sub.ass ---
    header = f"""[Script Info]
Title: {ep} Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.601
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{FONT},{SUB_FONTSIZE},&H00{ASS_INK},&H000000FF,&H00000000,&HA0000000,-1,0,0,0,100,100,0,0,1,{SUB_OUTLINE},0,2,{SUB_MARGIN_H},{SUB_MARGIN_H},{SUB_MARGIN_V},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    HOLD = 0.14   # 발화가 끝나도 잠깐 남겨 읽을 시간을 준다
    dialogues = []
    for s in scenes:
        a, b_ = s["speech_start"], s["speech_end"]
        span = b_ - a
        subs = s["subs"]
        # 한 문장 안에서 자막을 나눌 때는 글자 수 비율로 구간을 쪼갠다
        weights = [max(len(plain(x)), 1) for x in subs]
        acc, total_w = 0.0, sum(weights)
        for j, (line, w) in enumerate(zip(subs, weights)):
            st = a + span * (acc / total_w)
            acc += w
            en = b_ + HOLD if j == len(subs) - 1 else a + span * (acc / total_w)
            # \fad: 딱딱한 on/off 대신 아주 짧은 페이드
            dialogues.append(
                f"Dialogue: 0,{ass_time(st)},{ass_time(en)},Default,,0,0,0,,"
                f"{{\\fad(130,90)}}{markup(line)}"
            )
    (ep_dir / "sub.ass").write_text(header + "\n".join(dialogues) + "\n", encoding="utf-8")

    # --- timing.json ---
    (ep_dir / "timing.json").write_text(
        json.dumps(dict(
            episode=ep, voice=VOICE, rate=RATE, total=round(total, 3),
            lead_in=LEAD_IN, tail=TAIL,
            scenes=[{k: s[k] for k in ("scene", "kind", "move", "start", "end",
                                       "dur", "speech_start", "speech_end", "vo")}
                    for s in scenes],
        ), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    shutil.rmtree(tmp, ignore_errors=True)

    print(f"\n  vo.wav      {total:.2f}s")
    print(f"  scenes.tsv  {len(scenes)} 컷 / 합계 {sum(s['dur'] for s in scenes):.2f}s")
    print(f"  sub.ass     {len(dialogues)} 줄")
    print(f"  timing.json 기록 완료")
    if not (TARGET_MIN <= total <= TARGET_MAX):
        print(f"\n  [경고] 총 길이 {total:.1f}s 가 목표 "
              f"{TARGET_MIN:.0f}~{TARGET_MAX:.0f}s 를 벗어납니다.")

    # 도해 씬의 DURATION 선언과 비교해 준다
    for s in scenes:
        if s["kind"] != "diagram":
            continue
        py = ep_dir / "diagrams" / f"{s['scene']}.py"
        if not py.is_file():
            print(f"  [알림] {s['scene']}: diagrams/{s['scene']}.py 없음 "
                  f"(DURATION = {s['dur']:.2f})")
            continue
        m = re.search(r"^\s*DURATION\s*=\s*([\d.]+)", py.read_text(encoding="utf-8"), re.M)
        if not m:
            print(f"  [경고] {s['scene']}: DURATION 선언이 없습니다 → {s['dur']:.2f}")
        elif abs(float(m.group(1)) - s["dur"]) > 0.02:
            print(f"  [경고] {s['scene']}: DURATION {m.group(1)} → "
                  f"{s['dur']:.2f} 로 고쳐야 합니다.")


def generate(ep: str, beats: list[Beat]):
    asyncio.run(_run(ep, beats))
