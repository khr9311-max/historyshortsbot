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

# 도해 컷 길이 상한. 쇼츠 배포는 완주율이 열고, 완주율은 정적 화면에서 죽는다.
# EP011 S03 이 9.81초짜리 한 장이었고 그게 훅 직후 구간이었다.
DIAGRAM_MAX_SEC = 4.0
# 첫 컷은 스와이프 이탈을 막는 유일한 구간이다. 여기서 길게 끌면 배포가 안 열린다.
OPENING_MAX_SEC = 3.2
DIAGRAM_RANGE = (3, 4)          # 서사 클립 3개(=veo 6컷) 기준선 (SOP §4)
STILL_MAX = 1                   # 정지 톤이 겹치지 않도록 편당 1컷

# 도해 배경 플레이트 — 2026-08-27 부로 build.py 가 더는 읽지 않는다 (바이블
# §0 원안대로 밝은 종이 단색으로 되돌렸다). 필드는 옛 씬 파일과의 호환을
# 위해 남겨 두고 계속 검증한다. 새 씬에는 안 써도 된다.
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

# 마무리·루프백 문장 검사 (문체 규칙 §5) — 반전은 주체·순서·비용 중 하나에
# 걸어야 하고, "원인의 단일화"로 미끄러지면 안 된다.
_REVERSAL_MARK = re.compile(r"아니(?:라|었습니다|고|에요|었죠|었네요)")
_CONJOIN = re.compile(r"[가-힣]+(?:와|과)\s*[가-힣]")

# 계측선/주석 오버레이 탐지 (docs/06 §GP-01~04, §GP-06~08).
# 라벨 유무와 무관하게 veo/still 프롬프트에는 넣지 않는다 — 디퓨전이
# 매 클립마다 선과 글자를 새로 그려 흔들리거나 뭉개진다 (EP005 V01,
# EP007 V01~V03 사고). 화면 정보는 전부 diagram 컷으로 보낸다.
_ANNOTATION_HINT = re.compile(r"measurement line|numeric annotation|annotation overlaid|leader line", re.I)

# 첫 클립의 비트 A 는 상황 설명이 아니라 가장 센 장면으로 열어야 한다.
# establishing/wide 로 열면 첫 1~2초가 정지처럼 보이고 거기서 스와이프가 난다
# (EP011 V01 이 정글 와이드로 열고, 정작 제일 센 프레임은 4.9초에 있었다).
# 네거티브 지시("no establishing shot", "No Korean text") 는 검사 대상에서 뺀다.
_NEGATION = re.compile(r"(?<![A-Za-z])no\s+[^.;,]*", re.I)
_SLOW_OPEN = re.compile(
    r"establishing shot|wide establishing|slow (?:pan|reveal|drift)|"
    r"empty landscape|calm (?:sea|field)", re.I)
# 1초 안에 화면이 실제로 바뀌게 만드는 사건 어휘. 카메라 무브만으로는 부족하다 —
# 디퓨전 모델이 카메라 지시를 자주 무시한다.
_MOTION_EVENT = re.compile(
    r"collaps|topple|ignit|burst|shatter|surge|stumbl|fall|drop|slam|"
    r"spill|erupt|snap|tear|breach|flood|charge|bolt|swing|hurl|"
    r"pull(?:s|ing)? away|rush", re.I)


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
class Package:
    """업로드용 메타데이터 — 발행 단계(package)에서 검증·출력된다."""
    youtube_title: str = ""
    description: str = ""
    hashtags: list[str] = field(default_factory=list)
    thumbnail_scene: str = ""
    thumbnail_time: float = 1.0
    # 썸네일 전용 설정 — scripts/make_thumbnail.py 가 읽는다.
    # {source, t, lines[], accent, kicker}. 비어 있으면 hook_text 로 폴백한다.
    thumbnail: dict = field(default_factory=dict)


@dataclass
class Doc:
    episode: str
    title: str
    scenes: list[Scene]
    shots: dict[str, Shot]
    hook_text: str = ""
    package: Package = field(default_factory=Package)

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

    pkg_raw = raw.get("package") or {}
    package = Package(
        youtube_title=pkg_raw.get("youtube_title", ""),
        description=pkg_raw.get("description", ""),
        hashtags=list(pkg_raw.get("hashtags") or []),
        thumbnail_scene=pkg_raw.get("thumbnail_scene", ""),
        thumbnail_time=float(pkg_raw.get("thumbnail_time", 1.0)),
        thumbnail=dict(pkg_raw.get("thumbnail") or {}),
    )

    return Doc(episode=raw.get("episode", ep), title=raw.get("title", ""),
               scenes=scenes, shots=shots,
               hook_text=raw.get("hook_text", ""), package=package)


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
        if _ANNOTATION_HINT.search(sh.prompt):
            warn.append(f"{sh.id}: 계측선/주석 오버레이 문구가 있습니다 — veo/still은 "
                       "선·글자를 매번 새로 그려 흔들리거나 뭉개집니다 (EP005 V01, "
                       "EP007 V01~V03 사고). 이 문구를 빼고 정보는 diagram 컷으로 옮기세요.")

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
    warn += _check_ending(doc)
    warn += _check_opening_shot(doc)

    # --- 배치 ---
    kinds = [s.kind for s in doc.scenes]
    if kinds and kinds[0] != "veo":
        err.append("1번 씬이 veo 가 아닙니다 (SOP §5).")
    # 도해가 연달아 붙으면 그 구간이 통째로 정적 화면이 된다. 쇼츠에서 그건
    # 이탈 지점이다 (EP009 S03~S04, EP010 S03~S04 가 실제로 그랬다).
    for i in range(len(kinds) - 1):
        if kinds[i] == kinds[i + 1] == "diagram":
            err.append(
                f"diagram 이 연속입니다 ({doc.scenes[i].id}→{doc.scenes[i + 1].id}). "
                "사이에 veo/still 컷을 넣거나 둘을 한 씬으로 합치세요.")
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


def _check_opening_shot(doc: Doc) -> list[str]:
    """첫 클립이 '가장 센 장면'으로 여는지 본다.

    쇼츠 조회수는 첫 프레임부터 집계되고, 배포는 시드 오디언스의 스와이프
    이탈률이 연다. 상황 설명으로 시작하는 도입부는 그 구간을 통째로 버린다.
    가장 강한 그림을 비트 B 에 두면 이미 스와이프된 뒤다.
    """
    if not doc.scenes:
        return []
    first = doc.scenes[0]
    sh = doc.shots.get(first.shot)
    if sh is None or sh.kind != "veo":
        return []

    beats = _BEAT_TOKEN.split(sh.prompt)
    beat_a = beats[1] if len(beats) > 1 else sh.prompt
    # "No establishing shot" 같은 네거티브 지시는 금지어가 아니라 금지 선언이다.
    # 그대로 검사하면 규칙을 지킨 프롬프트가 오히려 걸린다.
    probe = _NEGATION.sub(" ", beat_a)

    warn: list[str] = []
    m = _SLOW_OPEN.search(probe)
    if m:
        warn.append(f"{sh.id}: 첫 클립이 '{m.group(0)}' 로 엽니다 — 상황 설명 도입은 "
                    "첫 3초를 버립니다. 가장 센 장면을 비트 A 로 올리세요.")
    if not _MOTION_EVENT.search(probe):
        warn.append(f"{sh.id}: 첫 클립 비트 A 에 움직임 사건이 없습니다. 카메라 무브만 "
                    "적으면 모델이 무시하고 거의 정지한 클립을 냅니다 (EP010·EP011 "
                    "첫 1.5초가 실제로 그랬습니다). 무너진다/불붙는다/쓰러진다 같은 "
                    "피사체 사건을 넣으세요.")
    return warn


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


def _check_ending(doc: Doc) -> list[str]:
    """마지막 컷(루프백)이 나열형 결말로 미끄러졌는지 본다 (문체 규칙 §5).

    "반전 솔루션으로 카타르시스"는 구조상 단일 원인 서사로 미끄러지기
    쉽다. 반전은 주체·순서·비용 중 하나에만 걸어야 하는데("A가 아니라
    B였습니다"), 실제로는 "A가 아니라 B와 C였습니다"처럼 반전 뒤에
    명사를 두 개 이상 나열해 버리는 경우가 많다 — 여전히 원인이 여럿인
    척하지만 화면 밖에서는 "그냥 다 합쳐서 결론"으로 읽힌다.
    이건 취향이 아니라 §5가 명시적으로 금지하는 패턴이다. 경고지 오류는
    아니다 — 의도했으면(예: 두 조건이 정말 대등하게 결합) 그대로 가도 된다.
    """
    warn: list[str] = []
    if not doc.scenes:
        return warn
    last = doc.scenes[-1]
    text = last.narration.strip()
    if not text:
        return warn

    m = _REVERSAL_MARK.search(text)
    if not m:
        warn.append(
            f"{last.id}: 마지막 문장(루프백)에 반전 표현('~이 아니라' 등)이 "
            "없습니다. 결론을 그냥 요약·나열하고 있지 않은지 확인하세요 "
            "(문체 규칙 §5 — 반전은 주체·순서·비용 중 하나에 걸 것)."
        )
    else:
        tail = text[m.end():]
        if _CONJOIN.search(tail):
            warn.append(
                f"{last.id}: 마지막 문장이 반전 뒤에 명사를 '~와/과'로 "
                "나열합니다 (예: 'A가 아니라 B와 C였습니다') — 원인의 단일화를 "
                "피하려다 나열형 결말로 샌 패턴일 수 있습니다 (문체 규칙 §5). "
                "좋은 예는 '~와/과' 없이 반전 하나로 끝납니다: "
                "'표준시를 만든 건 정부가 아니라 철도 회사였습니다.' "
                "반전은 주체·순서·비용 중 하나에만 걸고, 나머지 원인은 도해 "
                "화면이 설명하게 하세요. 두 조건이 정말 대등하게 결합한다는 "
                "의도라면 그대로 두어도 됩니다."
            )
    return warn


def validate_package(doc: Doc) -> tuple[list[str], list[str]]:
    """업로드 패키징 필드 검증 — package 단계 전용 (script 단계와 분리:

    옛 에피소드는 이 필드가 아예 없으므로 구조 검증과 묶으면 소급 경고가
    쏟아진다)."""
    err: list[str] = []
    warn: list[str] = []
    p = doc.package
    ids = [s.id for s in doc.scenes]

    if not p.youtube_title.strip():
        err.append("package.youtube_title 이 비어 있습니다.")
    elif len(p.youtube_title) > 100:
        warn.append(f"package.youtube_title 이 {len(p.youtube_title)}자입니다 "
                    "(유튜브 제목은 100자 넘으면 잘립니다).")
    if not p.description.strip():
        err.append("package.description 이 비어 있습니다.")
    if not p.hashtags:
        warn.append("package.hashtags 가 비어 있습니다.")
    if not p.thumbnail_scene:
        err.append("package.thumbnail_scene 이 없습니다 — 썸네일로 쓸 씬 id를 지정하세요.")
    elif p.thumbnail_scene not in ids:
        err.append(f"package.thumbnail_scene '{p.thumbnail_scene}' 은 없는 씬입니다.")
    if not doc.hook_text.strip():
        warn.append("hook_text 가 없습니다 — 0~2초 훅 카드 없이 나갑니다 "
                    "(영상 프롬프트 규칙 §2 훅 카드).")
    elif len(doc.hook_text.strip()) > 12:
        warn.append(f"hook_text 가 {len(doc.hook_text.strip())}자입니다 — 12자를 "
                    "넘으면 훅 카드 폭에서 잘리거나 줄어듭니다. 짧게 줄이세요.")

    warn += _check_thumbnail(doc)
    return err, warn


def _check_thumbnail(doc: Doc) -> list[str]:
    """썸네일 설정 점검.

    썸네일은 피드가 아니라 검색·채널 그리드에서 작동한다. 거기서는 200px 폭으로
    줄어들기 때문에 글자 수와 강조 위치가 전부다.
    """
    t = doc.package.thumbnail
    if not t:
        return ["package.thumbnail 이 없습니다 — hook_text 를 잘라 쓰지만, "
                "썸네일 문구는 훅 문구와 목적이 달라 따로 쓰는 편이 낫습니다."]

    warn: list[str] = []
    src = t.get("source")
    if src:
        shot = doc.shots.get(src)
        if shot is None:
            warn.append(f"package.thumbnail.source '{src}' 은 shots 에 없는 샷입니다.")
        elif shot.kind == "diagram":
            warn.append(f"package.thumbnail.source '{src}' 은 도해입니다 — "
                        "썸네일은 veo/still 샷에서 뽑으세요.")

    lines = [l for l in (t.get("lines") or []) if str(l).strip()]
    if len(lines) > 2:
        warn.append(f"package.thumbnail.lines 가 {len(lines)}줄입니다 — "
                    "2줄까지만 쓰입니다.")
    for l in lines[:2]:
        if len(str(l)) > 12:
            warn.append(f"썸네일 문구 '{l}' 가 {len(str(l))}자입니다 — "
                        "12자를 넘으면 글자가 줄어들어 그리드에서 안 읽힙니다.")

    accent = t.get("accent")
    if accent and not any(accent in str(l) for l in lines):
        warn.append(f"package.thumbnail.accent '{accent}' 가 lines 안에 없습니다 "
                    "— 강조가 적용되지 않습니다.")
    if lines and not accent:
        warn.append("package.thumbnail.accent 가 없습니다 — 강조 없는 두 줄은 "
                    "축소됐을 때 어디를 읽어야 할지 알려주지 못합니다.")
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

    err += _check_retention(doc, dur)
    return err, warn


def _check_retention(doc: Doc, dur: dict[str, float]) -> list[str]:
    """정적 화면이 얼마나 오래 이어지는지 본다.

    쇼츠 배포는 시드 오디언스의 완주율이 연다. 도해 컷은 정보 밀도는 높지만
    움직임이 거의 없어서, 길어지면 그 구간이 그대로 이탈 지점이 된다.
    """
    err: list[str] = []

    for s in doc.scenes:
        if s.kind != "diagram":
            continue
        d = dur.get(s.id, 0.0)
        if d > DIAGRAM_MAX_SEC + 1e-6:
            err.append(
                f"{s.id}: 도해 컷이 {d:.2f}s 입니다 (상한 {DIAGRAM_MAX_SEC:.1f}s).\n"
                f"        나레이션을 줄이거나 씬을 둘로 쪼개세요. "
                "쇼츠에서 4초 넘는 정지 화면은 이탈 지점입니다.")

    if doc.scenes:
        first = doc.scenes[0]
        d = dur.get(first.id, 0.0)
        if d > OPENING_MAX_SEC + 1e-6:
            err.append(
                f"{first.id}: 첫 컷이 {d:.2f}s 입니다 (상한 {OPENING_MAX_SEC:.1f}s).\n"
                "        첫 3초가 스와이프 이탈을 막는 유일한 구간입니다. "
                "한 문장으로 줄이세요.")

    kind_of = {s.id: s.kind for s in doc.scenes}
    total = sum(dur.values())
    static = sum(d for sid, d in dur.items()
                 if kind_of.get(sid) in ("diagram", "still"))
    if total and static / total > 0.45:
        err.append(
            f"정지 톤 컷(diagram+still)이 전체의 {static / total * 100:.0f}% 입니다 "
            f"({static:.1f}s / {total:.1f}s, 상한 45%).\n"
            "        veo 컷으로 옮기거나 도해를 줄이세요.")
    return err


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
