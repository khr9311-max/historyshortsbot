"""
lib_scenes.py — scenes.json 로더 · 검증기 (타임라인 권원의 입구)

`episodes/<EP>/scenes.json` 이 대본·씬 분해·프롬프트의 **단일 권원**이다.
claude.ai 프로젝트가 이 파일 하나만 뱉고, 나머지는 전부 여기서 파생된다.

    scenes.json ──> lib_narration ──> vo.wav · sub.ass · scenes.tsv · timing.json
                └─> pipeline      ──> prompts/*.txt (실측 비트 경계가 박힌 최종 프롬프트)
                └─> build.py      ──> render/<EP>_final.mp4

--------------------------------------------------------------------
샷과 씬은 다르다
--------------------------------------------------------------------
샷(shot)  = API 호출 한 번 = 돈이 나가는 단위
씬(scene) = 컷 한 개 = 나레이션 한 덩어리

veo 샷 하나는 8초짜리 2비트 클립이고, **씬 두 개를 채운다.**

    V01 (8초 t2v 클립)
      ├── S01  beat A  side_track   ← 나레이션 4.2초
      └── S02  beat B  push_in      ← 나레이션 3.1초

비트 경계는 대본이 정한다. S01 나레이션이 4.2초면 경계도 4.2초고,
프롬프트의 `[0-5s]` / `[5-8s]` 토큰은 생성 직전에 실측값으로 갈린다.
그래서 "8초 2비트"와 "나레이션이 컷 길이를 정한다"가 충돌하지 않는다.
두 씬이 클립을 연속으로 소진하므로 버려지는 구간도 없다.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# ============================================================
# 상수 — 영상 프롬프트 규칙 (docs/05_영상프롬프트_규칙.md)
# ============================================================
CLIP_SEC = 8.0        # t2v 클립 길이. 모델 출력이 8초로 고정이다.
PAIR_MIN = 6.0        # 2비트 페어가 이보다 짧으면 생성분을 버리는 셈
KINDS = ("veo", "still", "diagram")

# 비트별 무브. A 는 상황을 열고, B 는 결정타로 파고든다.
#   다큐멘터리 계열(GP-01~05)  : side_track → push_in
#   디오라마 계열(GP-06~08)    : dolly_out  → zoom_in
# 계열을 섞지 않는다. 한 클립 안에서 A 와 B 는 같은 계열이어야 한다.
MOVES_BEAT_A = ("side_track", "dolly_out")
MOVES_BEAT_B = ("push_in", "zoom_in")
MOVES_VEO = MOVES_BEAT_A + MOVES_BEAT_B
MOVE_FAMILY = {"side_track": "doc", "push_in": "doc",
               "dolly_out": "diorama", "zoom_in": "diorama"}

MOVES_STILL = ("dolly_in", "orbit", "crane_up")       # 바이블 §5 무브 3종
RISKS = ("low", "mid", "high")
DIAGRAM_RANGE = (3, 4)          # 서사 클립 3개(=veo 6컷) 기준선 (SOP §4)
STILL_MAX = 1                   # 정지 톤이 겹치지 않도록 편당 1컷

# 도해 배경 플레이트. assets_global/plates/P_<name>.mp4 로 해석된다 (규칙 §1).
PLATES = ("fog", "dust", "grid")
PLATE_DEFAULT = "fog"

# 어미 리듬 (docs/07_대본_문체_규칙.md §2)
_ENDINGS = (
    ("질문", ("까요", "나요", "습니까", "건가요", "죠?")),
    ("요체", ("거든요", "죠", "군요", "네요", "예요", "에요")),
    ("다체", ("니다", "겁니다", "셈입니다", "함", "이다")),
)
_ENDING_RUN = 3       # 같은 부류가 이만큼 연속되면 경고

# 프롬프트 안의 비트 타임스탬프 토큰
_BEAT_TOKEN = re.compile(r"\[\s*\d+(?:\.\d+)?\s*-\s*\d+(?:\.\d+)?\s*s\s*\]")
_HANGUL = re.compile(r"[가-힣]")

# 근거 없는 계측선/숫자 주석 탐지 (docs/06 §GP-01~04).
# "measurement lines / numeric annotation" 문구는 GP 앵커의 고정 어휘라
# 씬마다 그대로 복사되기 쉽지만, 딸린 따옴표 라벨("SUBTERRANEAN YIELD" 같은)이
# 없으면 화면에 근거 없는 숫자만 튀어나온다 (EP005 V01 사고).
_ANNOTATION_HINT = re.compile(r"measurement line|numeric annotation|annotation overlaid|leader line", re.I)
_QUOTED_LABEL = re.compile(r'"[^"]+"')


def _norm_for_compare(s: str) -> str:
    """자막 vs 나레이션 대조용 정규화. 강조 표시만 지우고 나머지는 그대로 둔다
    (구두점까지 똑같아야 '자막 = 나레이션 줄바꿈'이 성립한다)."""
    return re.sub(r"\s+", " ", s.replace("*", "")).strip()


# ============================================================
@dataclass
class Shot:
    """생성 단위 하나. veo 클립 또는 still 이미지."""
    id: str
    kind: str
    scenes: list[str]
    prompt: str = ""
    chars: int = 0
    risk: str = "low"
    golden_ref: str = ""

    @property
    def two_beat(self) -> bool:
        return self.kind == "veo" and len(self.scenes) == 2


@dataclass
class Scene:
    """컷 하나 = 나레이션 한 덩어리."""
    id: str
    kind: str
    narration: str
    subs: list[str] = field(default_factory=list)
    pause: float = 0.40
    note: str = ""
    shot: str = ""
    beat: str = ""       # "A" | "B" | ""
    move: str = "-"
    plate: str = ""      # diagram 전용. "" 는 로드 시 PLATE_DEFAULT 로 채워진다

    def __post_init__(self):
        if not self.subs:
            self.subs = [self.narration]


@dataclass
class Doc:
    episode: str
    title: str
    scenes: list[Scene]
    shots: dict[str, Shot]

    def scene(self, scene_id: str) -> Scene | None:
        return next((s for s in self.scenes if s.id == scene_id), None)

    def shot_of(self, scene_id: str) -> Shot | None:
        sc = self.scene(scene_id)
        return self.shots.get(sc.shot) if sc and sc.shot else None


# ============================================================
def path_for(ep: str) -> Path:
    return ROOT / "episodes" / ep / "scenes.json"


def load(ep: str) -> Doc:
    p = path_for(ep)
    if not p.is_file():
        raise SystemExit(
            f"오류: {p} 가 없습니다.\n"
            "      claude.ai 프로젝트에서 씬 분해를 받아 scenes.json 으로 저장하세요.\n"
            "      스키마: docs/05_영상프롬프트_규칙.md §6")
    raw = json.loads(p.read_text(encoding="utf-8"))

    shots: dict[str, Shot] = {}
    for s in raw.get("shots", []):
        shots[s["id"]] = Shot(
            id=s["id"], kind=s["kind"], scenes=list(s.get("scenes", [])),
            prompt=s.get("prompt", ""), chars=int(s.get("chars") or 0),
            risk=s.get("risk", "low"), golden_ref=s.get("golden_ref", ""))

    scenes: list[Scene] = []
    for s in raw["scenes"]:
        shot_id = s.get("shot", "")
        kind = s.get("kind") or (shots[shot_id].kind if shot_id in shots else "")
        plate = s.get("plate") or (PLATE_DEFAULT if kind == "diagram" else "")
        scenes.append(Scene(
            id=s["id"], kind=kind, narration=s["narration"],
            subs=list(s.get("subs") or []), pause=float(s.get("pause", 0.40)),
            note=s.get("note", ""), shot=shot_id, beat=s.get("beat", ""),
            move=s.get("move", "-"), plate=plate))

    return Doc(episode=raw.get("episode", ep), title=raw.get("title", ""),
               scenes=scenes, shots=shots)


# ============================================================
# 구조 검증 — 나레이션을 뽑기 전에 걸러낸다
# ============================================================
def validate(doc: Doc) -> tuple[list[str], list[str]]:
    """(오류, 경고) 를 돌려준다. 오류가 있으면 진행 불가."""
    err: list[str] = []
    warn: list[str] = []
    ids = [s.id for s in doc.scenes]

    if len(set(ids)) != len(ids):
        err.append("씬 id 가 중복됩니다.")

    for s in doc.scenes:
        if s.kind not in KINDS:
            err.append(f"{s.id}: kind '{s.kind}' 는 {KINDS} 중 하나여야 합니다.")
        if not s.narration.strip():
            err.append(f"{s.id}: narration 이 비어 있습니다.")
        if len(s.subs) > 2:
            err.append(f"{s.id}: 자막이 {len(s.subs)}줄입니다 (최대 2줄, 바이블 §3).")
        if sum(line.count("*") for line in s.subs) > 2:
            warn.append(f"{s.id}: 한 컷에 강조가 두 곳 이상입니다 (바이블 §1).")
        joined = _norm_for_compare(" ".join(s.subs))
        narr = _norm_for_compare(s.narration)
        if joined != narr:
            err.append(f"{s.id}: 자막이 나레이션과 다릅니다 — TTS가 말하는 내용과 "
                       "자막이 어긋납니다. 자막은 나레이션을 줄바꿈만 해서 써야 "
                       "합니다(요약·누락·단어 교체 금지). 표현을 바꾸고 싶으면 "
                       "나레이션 자체를 고치세요(그래야 TTS도 같이 바뀝니다).\n"
                       f"        나레이션: {narr}\n"
                       f"        자막:     {joined}")
        if s.kind == "diagram":
            if s.shot:
                err.append(f"{s.id}: diagram 컷에는 shot 을 달 수 없습니다.")
            if s.plate not in PLATES:
                err.append(f"{s.id}: plate '{s.plate}' 는 {PLATES} 중 하나여야 합니다.")
        elif not s.shot:
            err.append(f"{s.id}: {s.kind} 컷에 shot 이 없습니다.")
        elif s.shot not in doc.shots:
            err.append(f"{s.id}: 샷 '{s.shot}' 이 shots 에 없습니다.")
        if s.kind == "veo" and s.move not in MOVES_VEO:
            err.append(f"{s.id}: veo 컷의 move 는 {MOVES_VEO} 중 하나입니다.")
        if s.kind == "still" and s.move not in MOVES_STILL:
            err.append(f"{s.id}: still 컷의 move 는 {MOVES_STILL} 중 하나입니다.")

    # --- 샷 ---
    for sh in doc.shots.values():
        if sh.kind not in ("veo", "still"):
            err.append(f"{sh.id}: 샷 kind 는 veo 또는 still 입니다.")
        if not sh.prompt.strip():
            err.append(f"{sh.id}: prompt 가 비어 있습니다.")
        if sh.risk not in RISKS:
            err.append(f"{sh.id}: risk 는 {RISKS} 중 하나입니다.")
        if sh.risk == "high":
            err.append(f"{sh.id}: risk=high — 씬을 쪼개거나 diagram 으로 바꾸세요 "
                       "(규칙 §5). 이 상태로는 진행하지 않습니다.")
        if _HANGUL.search(sh.prompt):
            err.append(f"{sh.id}: 프롬프트에 한글이 들어 있습니다. 모델이 반드시 깨뜨립니다.")
        if sh.chars and abs(sh.chars - len(sh.prompt)) > 5:
            warn.append(f"{sh.id}: chars={sh.chars} 인데 실제 {len(sh.prompt)}자입니다.")
        if not sh.golden_ref:
            warn.append(f"{sh.id}: golden_ref 가 없습니다 (docs/06 의 GP-NN).")
        if _ANNOTATION_HINT.search(sh.prompt) and not _QUOTED_LABEL.search(sh.prompt):
            warn.append(f"{sh.id}: 계측선/숫자 주석 문구가 있는데 실제 라벨(따옴표 문자열)이 "
                       "없습니다 — 근거 없는 숫자가 화면에 튀어나올 수 있습니다 "
                       "(EP005 V01 사고). \"+25% POPULATION\" 처럼 라벨을 넣거나 문구를 빼세요.")

        missing = [x for x in sh.scenes if x not in ids]
        if missing:
            err.append(f"{sh.id}: 없는 씬을 가리킵니다 — {', '.join(missing)}")
            continue

        pos = [ids.index(x) for x in sh.scenes]
        if pos != sorted(pos) or any(b - a != 1 for a, b in zip(pos, pos[1:])):
            err.append(f"{sh.id}: 붙어 있지 않은 씬을 한 샷으로 묶었습니다 ({sh.scenes}).")

        if sh.kind == "still" and len(sh.scenes) != 1:
            err.append(f"{sh.id}: still 샷은 씬 하나만 채웁니다.")
        if sh.kind == "veo":
            if len(sh.scenes) not in (1, 2):
                err.append(f"{sh.id}: veo 샷은 씬 1~2개입니다 (2비트 = 2씬).")
                continue
            want_beats = ["A", "B"][:len(sh.scenes)]
            beats = [doc.scene(x).beat for x in sh.scenes]
            if beats != want_beats:
                err.append(f"{sh.id}: beat 표기가 {beats} 입니다. {want_beats} 여야 합니다.")
            moves = [doc.scene(x).move for x in sh.scenes]
            allowed = [MOVES_BEAT_A, MOVES_BEAT_B][:len(sh.scenes)]
            for mv, ok, bt in zip(moves, allowed, want_beats):
                if mv not in ok:
                    err.append(f"{sh.id}: 비트 {bt} 의 무브 '{mv}' 는 쓸 수 없습니다. "
                               f"{ok} 중 하나여야 합니다 (규칙 §3).")
            fams = {MOVE_FAMILY.get(m) for m in moves if m in MOVE_FAMILY}
            if len(fams) > 1:
                err.append(f"{sh.id}: 한 클립 안에서 무브 계열이 섞였습니다 ({moves}). "
                           "다큐멘터리 계열과 디오라마 계열을 섞지 않습니다.")
            if len(_BEAT_TOKEN.findall(sh.prompt)) != len(sh.scenes):
                err.append(f"{sh.id}: 프롬프트의 비트 토큰이 씬 수와 다릅니다. "
                           "[0-5s] / [5-8s] 형식으로 비트마다 하나씩 두세요.")
            if len(sh.scenes) == 1:
                warn.append(f"{sh.id}: 1비트 클립입니다. 8초를 다 쓰지 못합니다.")

    warn += _check_rhythm(doc)

    # --- 배치 ---
    kinds = [s.kind for s in doc.scenes]
    if kinds and kinds[0] != "veo":
        err.append("1번 씬이 veo 가 아닙니다 (SOP §5).")
    for i in range(len(kinds) - 2):
        if kinds[i] == kinds[i + 1] == kinds[i + 2] == "diagram":
            err.append(f"diagram 이 3연속입니다 ({doc.scenes[i].id} 부터).")
    n_dia = kinds.count("diagram")
    if not (DIAGRAM_RANGE[0] <= n_dia <= DIAGRAM_RANGE[1]):
        warn.append(f"diagram 컷이 {n_dia}개입니다 "
                    f"(권장 {DIAGRAM_RANGE[0]}~{DIAGRAM_RANGE[1]}, SOP §4).")
    n_still = kinds.count("still")
    if n_still > STILL_MAX:
        warn.append(f"still 컷이 {n_still}개입니다 (권장 {STILL_MAX}개 — "
                    "정지 톤이 겹칩니다. 규칙 §1).")
    if kinds and kinds[-1] != "diagram":
        warn.append("마지막 컷이 요약 도해가 아닙니다 (SOP §5).")

    return err, warn


def ending_of(sentence: str) -> str:
    """문장의 어미 부류를 판정한다. 판정 불가는 빈 문자열."""
    s = sentence.strip().rstrip('."\'”’ ')
    if not s:
        return ""
    if s.endswith("?"):
        return "질문"
    s = s.rstrip("?!")
    for name, pats in _ENDINGS:
        if any(s.endswith(p) for p in pats):
            return name
    return ""


def _sentences(doc: Doc) -> list[tuple[str, str]]:
    """(씬 id, 문장) 목록. 나레이션은 한 씬에 두 문장까지 들어간다."""
    out = []
    for sc in doc.scenes:
        for part in re.split(r"(?<=[.?!])\s+", sc.narration.strip()):
            if part.strip():
                out.append((sc.id, part.strip()))
    return out


def _check_rhythm(doc: Doc) -> list[str]:
    """어미 리듬 — 같은 어미가 이어지면 대본이 늘어진다 (문체 규칙 §2).

    이건 취향이 아니라 이 포맷의 이탈률 문제다. 45초 안에서 같은 어미가
    세 번 이어지면 시청자가 '정보 낭독'으로 인식한다.
    """
    warn: list[str] = []
    sents = _sentences(doc)

    run, run_kind, run_ids = 0, "", []
    for sid, text in sents:
        kind = ending_of(text)
        if kind and kind == run_kind:
            run += 1
            run_ids.append(sid)
        else:
            run, run_kind, run_ids = 1, kind, [sid]
        if run == _ENDING_RUN:
            warn.append(f"어미 '{run_kind}' 가 {run}연속입니다 "
                        f"({' → '.join(run_ids)}). 하나를 다른 어미로 바꾸세요.")

    if not any(ending_of(t) == "질문" for _, t in sents):
        warn.append("셀프 문답이 없습니다. 중반 이후 시청자가 떠올릴 반박을 "
                    "대신 묻고 즉시 답하는 문장을 하나 넣으세요 (문체 규칙 §3).")
    return warn


# ============================================================
# 실측 검증 — 나레이션을 뽑은 뒤에만 할 수 있다
# ============================================================
def durations(timing: dict) -> dict[str, float]:
    return {t["scene"]: float(t["dur"]) for t in timing["scenes"]}


def validate_timing(doc: Doc, timing: dict) -> tuple[list[str], list[str]]:
    """8초 클립 안에 두 비트가 실제로 들어가는지 본다."""
    err: list[str] = []
    warn: list[str] = []
    dur = durations(timing)

    for sh in doc.shots.values():
        if sh.kind != "veo":
            continue
        total = sum(dur.get(x, 0.0) for x in sh.scenes)
        detail = " + ".join(f"{x} {dur.get(x, 0.0):.2f}s" for x in sh.scenes)
        if total > CLIP_SEC + 1e-6:
            err.append(
                f"{sh.id}: 두 비트 합이 {total:.2f}s 로 8초 클립을 넘칩니다 ({detail}).\n"
                f"        대본을 줄이거나 씬 하나를 diagram 으로 돌리세요.")
        elif sh.two_beat and total < PAIR_MIN:
            warn.append(f"{sh.id}: 두 비트 합이 {total:.2f}s 뿐입니다 ({detail}). "
                        f"8초를 사고 {CLIP_SEC - total:.1f}s 를 버립니다.")
    return err, warn


def beat_boundary(doc: Doc, shot: Shot, timing: dict) -> float:
    """비트 A 가 끝나는 시각 = 실측된 A 씬 길이."""
    return round(durations(timing).get(shot.scenes[0], 0.0), 2)


def clip_offset(doc: Doc, scene: Scene, timing: dict) -> float:
    """이 씬이 소스 클립의 몇 초 지점부터 쓰는지."""
    sh = doc.shots.get(scene.shot)
    if sh is None or sh.kind != "veo" or scene.beat != "B":
        return 0.0
    return beat_boundary(doc, sh, timing)


def stamp_prompt(prompt: str, boundary: float) -> str:
    """프롬프트의 비트 타임스탬프를 실측 경계로 갈아끼운다.

        [0-5s] …  [5-8s] …     →     [0-4.2s] …  [4.2-8s] …
    """
    b = f"{boundary:.1f}".rstrip("0").rstrip(".")
    tokens = [f"[0-{b}s]", f"[{b}-{CLIP_SEC:.0f}s]"]
    it = iter(tokens)
    return _BEAT_TOKEN.sub(lambda _: next(it, tokens[-1]), prompt)


# ============================================================
def to_beats(doc: Doc):
    """lib_narration 이 먹는 Beat 목록으로 변환한다."""
    from lib_narration import Beat
    kindmap = {"veo": "ai_hero", "still": "ai_still", "diagram": "diagram"}
    return [Beat(scene=s.id, kind=kindmap[s.kind], move=s.move,
                 vo=s.narration, subs=list(s.subs), pause=s.pause, note=s.note,
                 shot=s.shot or s.id, beat=s.beat, plate=s.plate)
            for s in doc.scenes]


def asset_for(doc: Doc, scene: Scene, assets: Path) -> Path | None:
    """씬을 채울 원본 파일. veo/still 은 씬이 아니라 **샷** 이름을 쓴다."""
    if scene.kind == "diagram":
        return assets / "clips" / f"{scene.id}.mov"
    sh = doc.shots.get(scene.shot)
    if sh is None:
        return None
    return (assets / "clips" / f"{sh.id}.mp4") if sh.kind == "veo" \
        else (assets / "images" / f"{sh.id}.png")
