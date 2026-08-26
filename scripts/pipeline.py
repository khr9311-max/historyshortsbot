#!/usr/bin/env python3
"""
pipeline.py — 역사 인과 쇼츠 파이프라인 오케스트레이터

한 편을 끝까지 끌고 가는 단일 진입점이다.

`video` 단계는 **veo 샷을 Gemini API(Veo 3.1 Lite)로 직접 생성한다.**
GEMINI_API_KEY 가 필요하다 (Google AI Studio 발급).
레포 루트에 .env 파일을 만들고 GEMINI_API_KEY=... 한 줄을 적으면 된다
(.env 는 .gitignore 대상 — setx 환경변수와 달리 터미널 재시작이 필요 없다).
이미 파일이 있는 샷은 절대 다시 부르지 않는다 — 재실행으로 과금이
중복되는 사고를 막는 유일한 장치이므로, 다시 뽑고 싶으면 해당
`assets/clips/<샷ID>.mp4` 를 직접 지우고 재실행한다.
still(이미지) 생성은 여전히 사람이 한다.

    python scripts/pipeline.py EP007                  # 되는 데까지 진행
    python scripts/pipeline.py EP007 --status         # 어디까지 됐나
    python scripts/pipeline.py EP007 --from prompt    # 중간부터
    python scripts/pipeline.py EP007 --only V02       # 특정 샷만 다시
    python scripts/pipeline.py EP007 --force          # 완료 표시 무시하고 재실행

단계
    script    scenes.json 구조 검증          (컷 배분·비트·프롬프트 규칙)
    sources   [GATE1] 출처 검증              — 비어 있으면 여기서 멈춘다
    narration TTS·자막·컷 길이 생성          → vo.wav sub.ass scenes.tsv timing.json
    prompt    실측 비트 경계 확정            → prompts/*.txt + 비용 견적
    video     veo 생성(API) · still 확인     — veo 는 자동 생성, still 은 사람이 넣는다
    diagram   Manim 도해 렌더
    assemble  조립                           → render/<EP>_final.mp4
    review    [GATE2] 최종 검수              — 사람이 보고 승인
    publish   업로드 체크리스트 출력

상태는 episodes/<EP>/.state.json 에 남는다.
scenes.json 이 바뀌면 이후 단계의 완료 표시는 자동으로 무효가 된다.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import lib_scenes  # noqa: E402

# ============================================================
# 설정 — 단가는 실제 청구서를 보고 채운다
# ============================================================
CFG = {
    "veo_won_per_clip": 900,    # Veo 3.1 Lite 1080p, 8초 = $0.08/s × 8 (SOP §4 모델 선택 근거)
    "still_won_per_image": 83,  # 이미지 1장 단가(원). 1,000원/12장
    "monthly_budget": 100000,   # 월 예산 (SOP §4)
    "eps_per_month": 12,

    "veo_model": "veo-3.1-lite-generate-preview",
    "veo_resolution": "1080p",
    "veo_aspect_ratio": "9:16",
    "veo_retries": 2,           # 실패 시 재시도 횟수 (SOP §4 1.5배 견적의 근거)
    "veo_poll_sec": 10,         # 생성 완료 폴링 간격(초)
}

# docs/05 §4 네거티브 블록 — API negative_prompt 로 그대로 전달한다
VEO_NEGATIVE_PROMPT = (
    "korean text, hangul, garbled letters, close-up faces, hands, "
    "modern logos, watermark, oversaturated, cartoon, cluttered"
)

STAGES = ["script", "sources", "narration", "prompt",
          "video", "diagram", "assemble", "review", "publish"]

ONLY: set[str] | None = None


# ============================================================
def say(msg: str = ""):
    print(msg, flush=True)


def die(msg: str):
    print(f"\n[중단] {msg}\n", file=sys.stderr)
    sys.exit(1)


def report(err: list[str], warn: list[str], label: str):
    for w in warn:
        say(f"  [경고] {w}")
    if err:
        say(f"\n  {label} 오류:")
        for e in err:
            say(f"    - {e}")
        die(f"{label} 를 통과하지 못했습니다.")


def picked(shot_id: str) -> bool:
    return ONLY is None or shot_id in ONLY


# ============================================================
class State:
    """단계별 완료 기록. scenes.json 이 바뀌면 전부 무효로 돌린다."""

    def __init__(self, ep: str):
        self.dir = ROOT / "episodes" / ep
        self.path = self.dir / ".state.json"
        self.data = (json.loads(self.path.read_text(encoding="utf-8"))
                     if self.path.exists() else {"done": [], "script_hash": ""})

    def sync(self):
        p = lib_scenes.path_for(self.dir.name)
        h = hashlib.sha256(p.read_bytes()).hexdigest()[:16] if p.is_file() else ""
        if h and h != self.data.get("script_hash"):
            if self.data["done"]:
                say("  [알림] scenes.json 이 바뀌었습니다 → 이전 진행 기록을 비웁니다.")
            self.data = {"done": [], "script_hash": h}
            self._write()

    def done(self, stage: str) -> bool:
        return stage in self.data["done"]

    def mark(self, stage: str):
        if stage not in self.data["done"]:
            self.data["done"].append(stage)
        self.data["updated"] = time.strftime("%Y-%m-%d %H:%M")
        self._write()

    def _write(self):
        self.path.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_timing(ep_dir: Path) -> dict:
    p = ep_dir / "timing.json"
    if not p.is_file():
        die("timing.json 이 없습니다. narration 단계를 먼저 돌리세요.")
    return json.loads(p.read_text(encoding="utf-8"))


# ============================================================
# 단계
# ============================================================
def stage_script(ep: str):
    """scenes.json 구조 검증. 나레이션을 뽑기 전에 걸러낸다."""
    doc = lib_scenes.load(ep)
    err, warn = lib_scenes.validate(doc)
    report(err, warn, "구조 검증")

    kinds = [s.kind for s in doc.scenes]
    veo = [x for x in doc.shots.values() if x.kind == "veo"]
    say(f"  씬 {len(doc.scenes)}개 "
        f"(veo {kinds.count('veo')} / still {kinds.count('still')} / "
        f"diagram {kinds.count('diagram')})")
    say(f"  샷 {len(doc.shots)}개 — 유료 생성 {len(doc.shots)}회 "
        f"(veo 클립 {len(veo)}개)")
    for sh in doc.shots.values():
        if sh.risk == "mid":
            say(f"  [주의] {sh.id}: risk=mid — 실패하면 비트 하나로 줄이세요.")


def stage_sources(ep_dir: Path):
    """GATE1 — 출처가 비어 있으면 진행 불가 (바이블 §8)."""
    src = ep_dir / "sources.md"
    if not src.is_file():
        die("sources.md 가 없습니다.")
    empty = [ln for ln in src.read_text(encoding="utf-8").splitlines()
             if ln.strip().startswith("|") and ln.count("|") >= 4
             and all(c.strip() == "" for c in ln.split("|")[1:-1])]
    if empty:
        die(f"sources.md 에 빈 항목이 {len(empty)}개 있습니다. 채운 뒤 다시 실행하세요.")
    say("  GATE1 통과 — 출처 확인됨")


def stage_narration(ep: str):
    """대본 → 음성·자막·컷 길이. 타임라인은 여기서만 정해진다."""
    import lib_narration
    lib_narration.generate_from_scenes(ep)


def stage_prompt(ep: str, ep_dir: Path):
    """실측 비트 경계를 프롬프트에 박아 prompts/ 에 떨군다.

    대본이 컷 길이를 정하고, 그 길이가 곧 비트 경계가 된다.
    S01 이 4.2초면 프롬프트도 [0-4.2s] / [4.2-8s] 로 갈린다.
    """
    doc = lib_scenes.load(ep)
    timing = load_timing(ep_dir)
    report(*lib_scenes.validate_timing(doc, timing), label="실측 길이 검증")

    out = ep_dir / "prompts"
    out.mkdir(exist_ok=True)
    dur = lib_scenes.durations(timing)

    for sh in doc.shots.values():
        if not picked(sh.id):
            continue
        if sh.kind == "veo":
            boundary = lib_scenes.beat_boundary(doc, sh, timing)
            text = lib_scenes.stamp_prompt(sh.prompt, boundary)
            spent = sum(dur.get(x, 0.0) for x in sh.scenes)
            head = (f"# {sh.id}  ({', '.join(sh.scenes)})  "
                    f"비트 경계 {boundary:.2f}s / 사용 {spent:.2f}s of 8s  "
                    f"risk={sh.risk}  ref={sh.golden_ref}  {len(text)}자")
        else:
            text = sh.prompt
            head = (f"# {sh.id}  ({sh.scenes[0]})  still  "
                    f"risk={sh.risk}  ref={sh.golden_ref}  {len(text)}자")
        (out / f"{sh.id}.txt").write_text(head + "\n\n" + text + "\n",
                                          encoding="utf-8")
        say(f"  {head[2:]}")

    estimate(doc)
    say(f"\n  prompts/ 에 {len(doc.shots)}개. 생성 서비스에 그대로 붙여 넣으세요.")


def estimate(doc: lib_scenes.Doc):
    """편당·월간 비용 견적. 단가가 0 이면 조용히 접는다."""
    v, i = CFG["veo_won_per_clip"], CFG["still_won_per_image"]
    if not (v or i):
        say("\n  [알림] CFG 의 단가가 비어 있어 비용 견적을 건너뜁니다.")
        return
    n_v = sum(1 for x in doc.shots.values() if x.kind == "veo")
    n_i = sum(1 for x in doc.shots.values() if x.kind == "still")
    per = n_v * v + n_i * i
    month = per * CFG["eps_per_month"]
    say(f"\n  견적: 편당 {per:,}원 (veo {n_v}×{v:,} + still {n_i}×{i:,})")
    say(f"        월 {CFG['eps_per_month']}편 → {month:,}원 "
        f"/ 예산 {CFG['monthly_budget']:,}원")
    if month > CFG["monthly_budget"]:
        say(f"  [경고] 예산을 {month - CFG['monthly_budget']:,}원 넘깁니다. "
            "veo 샷을 줄이거나 발행 편수를 조정하세요.")


def _load_dotenv():
    """레포 루트의 .env 를 읽어 os.environ 에 없는 키만 채운다.

    setx 로 등록한 환경변수는 이미 떠 있는 프로세스(열려 있던 터미널·
    VSCode 등)엔 적용되지 않는다 — 그 프로세스가 완전히 재시작돼야
    레지스트리 값을 다시 읽는다. .env 는 실행할 때마다 파일에서 직접
    읽으므로 이 문제가 아예 생기지 않는다. 이미 셸에 설정된 값이 있으면
    그쪽을 우선한다(.env 가 덮어쓰지 않는다).
    """
    import os
    p = ROOT / ".env"
    if not p.is_file():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def _gemini_client():
    """Gemini API 클라이언트. GEMINI_API_KEY 가 없으면 여기서 바로 죽는다."""
    import os
    _load_dotenv()
    if not os.environ.get("GEMINI_API_KEY"):
        die("GEMINI_API_KEY 가 없습니다. 레포 루트에 .env 파일을 만들고 "
            "GEMINI_API_KEY=발급받은키 한 줄을 적으세요 (.env 는 .gitignore 에 "
            "있어 커밋되지 않습니다). 발급: "
            "https://ai.google.dev/gemini-api/docs/api-key")
    try:
        from google import genai
    except ImportError:
        die("google-genai 가 설치돼 있지 않습니다. pip install google-genai")
    return genai.Client()


def generate_veo_clip(prompt: str, dst: Path, label: str):
    """Veo 3.1 Lite 로 8초 클립 하나를 생성해 dst 에 저장한다.

    실패하면 CFG['veo_retries']만큼 다시 시도한다 (SOP §4 재시도 계수 1.5배의 근거).
    """
    from google.genai import types

    client = _gemini_client()
    # negative_prompt 필드는 Gemini Developer API(AI Studio 키)의 이 모델에서
    # 지원하지 않는다 (Vertex/Enterprise 전용) — 400 INVALID_ARGUMENT.
    # docs/05 §4 네거티브 블록을 프롬프트 본문에 "Avoid:" 절로 직접 접어 넣는다.
    full_prompt = f"{prompt} Avoid: {VEO_NEGATIVE_PROMPT}."
    last_err = None
    for attempt in range(1, CFG["veo_retries"] + 2):
        try:
            say(f"    [{label}] 생성 요청 (시도 {attempt})")
            op = client.models.generate_videos(
                model=CFG["veo_model"],
                source=types.GenerateVideosSource(prompt=full_prompt),
                config=types.GenerateVideosConfig(
                    aspect_ratio=CFG["veo_aspect_ratio"],
                    resolution=CFG["veo_resolution"],
                    duration_seconds=8,
                    # generate_audio 도 같은 이유로 지원 안 함. 기본값(오디오 포함)으로
                    # 생성되고, 오디오는 build.py 의 make_clip 이 -an 으로 버린다.
                ),
            )
            while not op.done:
                time.sleep(CFG["veo_poll_sec"])
                op = client.operations.get(op)
            if op.error:
                raise RuntimeError(op.error)
            videos = op.response.generated_videos
            if not videos:
                raise RuntimeError("생성 결과가 비어 있습니다 (안전 필터 차단 가능성).")
            data = client.files.download(file=videos[0].video)
            dst.write_bytes(data)
            say(f"    [{label}] 완료 → {dst.relative_to(ROOT)}")
            return
        except Exception as e:  # noqa: BLE001 — 재시도 루프이므로 넓게 잡는다
            last_err = e
            say(f"    [{label}] 실패: {e}")
    die(f"{label} 생성이 {CFG['veo_retries'] + 1}회 모두 실패했습니다: {last_err}")


def stage_video(ep: str, ep_dir: Path):
    """veo 는 Gemini API 로 직접 생성한다. still 은 사람이 넣었는지만 본다.

    이미 파일이 있는 샷은 절대 다시 부르지 않는다 — 재실행 과금 사고 방지책이다.
    다시 뽑고 싶으면 assets/clips/<샷ID>.mp4 를 직접 지우고 재실행한다.
    """
    doc = lib_scenes.load(ep)
    timing = load_timing(ep_dir)
    assets = ep_dir / "assets"
    (assets / "clips").mkdir(parents=True, exist_ok=True)
    (assets / "images").mkdir(parents=True, exist_ok=True)

    to_generate = []
    missing_still = []
    for sh in doc.shots.values():
        if not picked(sh.id):
            continue
        if sh.kind == "veo":
            dst = assets / "clips" / f"{sh.id}.mp4"
            if dst.is_file():
                say(f"  있음 {sh.id}  {dst.relative_to(ep_dir)}")
            else:
                to_generate.append((sh, dst))
        else:
            dst = assets / "images" / f"{sh.id}.png"
            if dst.is_file():
                say(f"  있음 {sh.id}  {dst.relative_to(ep_dir)}")
            else:
                missing_still.append((sh, dst))

    if to_generate:
        v = CFG["veo_won_per_clip"]
        say(f"\n  veo 클립 {len(to_generate)}개 생성 — 약 {len(to_generate) * v:,}원 "
            f"({v:,}원 × {len(to_generate)}, 실패 재시도는 별도)")
        for sh, dst in to_generate:
            boundary = lib_scenes.beat_boundary(doc, sh, timing)
            prompt = lib_scenes.stamp_prompt(sh.prompt, boundary)
            generate_veo_clip(prompt, dst, sh.id)

    if missing_still:
        say("\n  아직 없는 생성물 (still — 사람이 직접):")
        for sh, dst in missing_still:
            say(f"    {sh.id}  →  {dst.relative_to(ROOT)}"
                f"   (프롬프트: prompts/{sh.id}.txt)")
        die(f"still 생성물 {len(missing_still)}개가 비었습니다. "
            "위 경로에 파일을 넣고 다시 실행하세요.")


def stage_diagram(ep: str, ep_dir: Path):
    """Manim 도해 렌더. 씬 코드가 없으면 무엇을 써야 하는지 알려준다."""
    doc = lib_scenes.load(ep)
    timing = load_timing(ep_dir)
    dur = lib_scenes.durations(timing)
    clips = ep_dir / "assets" / "clips"
    clips.mkdir(parents=True, exist_ok=True)
    missing = []

    for s in doc.scenes:
        if s.kind != "diagram" or not picked(s.id):
            continue
        py = ep_dir / "diagrams" / f"{s.id}.py"
        if not py.is_file():
            missing.append(f"{s.id} (DURATION = {dur.get(s.id, 0.0):.2f})")
            continue
        dst = clips / f"{s.id}.mov"
        if dst.is_file() and dst.stat().st_mtime >= py.stat().st_mtime:
            say(f"  최신 {s.id}")
            continue
        say(f"  렌더 {s.id} (투명)")
        subprocess.run(
            [sys.executable, "-m", "manim", "-qh", "-t",
             "--resolution", "1080,1920", str(py), "-o", s.id], check=True)
        hits = sorted(ROOT.glob(f"media/videos/{s.id}/**/{s.id}.mov"))
        if not hits:
            die(f"{s.id} Manim 출력물을 찾지 못했습니다.")
        dst.write_bytes(hits[-1].read_bytes())

    if missing:
        die("도해 씬 코드가 없습니다: " + ", ".join(missing) +
            "\n        Claude Code 에서 작성하세요. lib_style 만 import 하고 "
            "DURATION 을 위 값으로 맞춥니다.")


def stage_assemble(ep: str):
    subprocess.run([sys.executable, str(ROOT / "scripts" / "build.py"), ep],
                   check=True)


def stage_review(ep: str):
    """GATE2 — 사람이 결과를 보고 승인해야 넘어간다."""
    out = ROOT / "render" / f"{ep}_final.mp4"
    if not out.is_file():
        die("렌더 결과가 없습니다.")
    say(f"  결과: {out}")
    say("  QC 체크리스트(docs/03_제작_SOP.md §5)를 확인하세요.")
    say("  자동 검사:  .\\scripts\\qc.ps1 " + ep)
    if input("\n  발행 단계로 넘어갈까요? [y/N] ").strip().lower() != "y":
        die("사용자가 보류했습니다.")


def stage_publish(ep: str):
    """업로드는 사람이 한다. 빠뜨리기 쉬운 것만 짚어 준다."""
    say(f"  render/{ep}_final.mp4 를 업로드하세요.")
    say("    - AI 생성 콘텐츠 라벨 체크 (필수)")
    say("    - 예약 발행: 월/수/금")
    say("    - 제목·설명에 인과 구조 한 줄 + 출처 표기")
    say("    - 프로덕션 시트에 업로드일 기록 (SOP §6)")


# ============================================================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ep")
    ap.add_argument("--from", dest="start", default="script", choices=STAGES)
    ap.add_argument("--to", dest="end", default="assemble", choices=STAGES)
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--only", help="특정 샷/씬만 처리 (예: V02 또는 V02,S05)")
    ap.add_argument("--force", action="store_true", help="완료된 단계도 다시 실행")
    a = ap.parse_args()

    global ONLY
    ONLY = set(a.only.split(",")) if a.only else None

    ep_dir = ROOT / "episodes" / a.ep
    if not ep_dir.is_dir():
        die(f"에피소드가 없습니다: {ep_dir}")

    st = State(a.ep)
    st.sync()

    if a.status:
        say(f"[{a.ep}]  갱신 {st.data.get('updated', '-')}")
        for s in STAGES:
            say(f"  {'✓' if st.done(s) else '·'} {s}")
        return

    for stage in STAGES[STAGES.index(a.start):STAGES.index(a.end) + 1]:
        if st.done(stage) and not (a.force or ONLY):
            say(f"[건너뜀] {stage}")
            continue
        say(f"\n[{stage}]")
        if stage == "script":
            stage_script(a.ep)
        elif stage == "sources":
            stage_sources(ep_dir)
        elif stage == "narration":
            stage_narration(a.ep)
        elif stage == "prompt":
            stage_prompt(a.ep, ep_dir)
        elif stage == "video":
            stage_video(a.ep, ep_dir)
        elif stage == "diagram":
            stage_diagram(a.ep, ep_dir)
        elif stage == "assemble":
            stage_assemble(a.ep)
        elif stage == "review":
            stage_review(a.ep)
        elif stage == "publish":
            stage_publish(a.ep)
        st.mark(stage)

    say("\n완료.")


if __name__ == "__main__":
    main()
