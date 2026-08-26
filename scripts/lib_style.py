"""
lib_style.py — 역사 인과 쇼츠 Manim 공용 스타일 모듈

docs/02_스타일_바이블.md 의 값을 코드 상수로 고정한다.
모든 diagram 씬은 이 모듈만 import 하고, 색·폰트·크기를 직접 쓰지 않는다.

사용법 (episodes/<EP>/diagrams/S0X.py):

    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "scripts"))
    from lib_style import *

    class S03Scene(DiagramScene):
        DURATION = 3.8
        def build(self):
            ...
"""
from __future__ import annotations

import math

import numpy as np
from manim import *  # noqa: F401,F403

# ============================================================
# 1. 규격
# ============================================================
PX_W, PX_H = 1080, 1920
FPS = 25
FRAME_W, FRAME_H = 9.0, 16.0
PPU = PX_W / FRAME_W  # 120 px = 1 scene unit

config.pixel_width = PX_W
config.pixel_height = PX_H
config.frame_width = FRAME_W
config.frame_height = FRAME_H
config.frame_rate = FPS

# ============================================================
# 2. 색상 상수 — 바이블 §1
# ============================================================
BG = "#0E1420"      # 배경 (딥 네이비)
INK = "#E8E4DC"     # 기본 텍스트·선
ACCENT = "#E4483A"  # 강조 1색 — 한 화면에 한 곳만
SUB = "#F2A73B"     # 보조 강조 (앰버)
MUTE = "#5A6472"    # 비활성 요소·격자

# MUTE 는 대비가 낮아 '읽어야 하는 본문'에 쓰면 안 된다.
# 비활성이지만 읽혀야 하는 텍스트는 DIM 을 쓴다.
DIM = "#8C97A8"

STROKE = 3  # 선 굵기 고정 — 바이블 §3

# ============================================================
# 3. 타이포 — 바이블 §2
# ============================================================
# 바이블 지정 폰트: Pretendard Bold (대체: Noto Sans KR Bold)
_FONT_CANDIDATES = ("Pretendard", "Noto Sans KR", "Malgun Gothic", "Segoe UI")


def _resolve_font() -> str:
    try:
        import manimpango

        installed = set(manimpango.list_fonts())
        for name in _FONT_CANDIDATES:
            if name in installed:
                return name
    except Exception:
        pass
    return _FONT_CANDIDATES[0]


FONT = _resolve_font()

# 실측 상수: 한글 글자 높이(px) = font_size * KO_H_PER_FS  (1080x1920 / frame_w 9.0 기준)
KO_H_PER_FS = 1.456


def fs(pct_of_width: float) -> float:
    """화면 '폭' 대비 퍼센트로 글자 높이를 지정한다 → manim font_size 반환."""
    return (PX_W * pct_of_width / 100.0) / KO_H_PER_FS


FS_TITLE = fs(5.2)    # ~56px  화면 내 제목
FS_LEAD = fs(4.4)     # ~48px  핵심 라벨
FS_BODY = fs(3.8)     # ~41px  본문 라벨
FS_CAPTION = fs(3.1)  # ~33px  보조 설명 (하한선)
FS_TAG = fs(2.6)      # ~28px  태그·단위. 이보다 작게 쓰지 않는다
FS_NUM = fs(9.5)      # ~103px 숫자는 크게, 단독으로 — 바이블 §2

# ============================================================
# 4. 세이프 에어리어
# ============================================================
# 쇼츠 UI(하단 제목/채널/설명, 우측 버튼열)와 번인 자막 밴드를 피한 실제 작업 영역.
#   x: ±4.0  (좌우 60px 여백)
#   y: -3.4 ~ 6.9  (상단 132px, 하단 1368px 아래는 자막·UI 영역)
SAFE_L, SAFE_R = -4.0, 4.0
SAFE_B, SAFE_T = -3.4, 6.9
SAFE_CY = (SAFE_T + SAFE_B) / 2.0   # 1.75 — 도해 구성의 실제 중심
SAFE_W = SAFE_R - SAFE_L            # 8.0
SAFE_H = SAFE_T - SAFE_B            # 10.3


def safe_box(**kw) -> Rectangle:
    """디버그용 세이프 에어리어 가이드."""
    r = Rectangle(width=SAFE_W, height=SAFE_H, color=SUB, stroke_width=1, **kw)
    r.move_to(UP * SAFE_CY)
    return r


class SafeAreaError(RuntimeError):
    pass


class OverlapError(RuntimeError):
    pass


def _bbox(m: Mobject):
    return (m.get_left()[0], m.get_right()[0], m.get_bottom()[1], m.get_top()[1])


def no_overlap(*named, pad: float = 0.05):
    """
    (mobject, "이름") 쌍들의 바운딩 박스가 서로 겹치면 예외를 던진다.
    guard() 는 화면 밖으로 나가는 것만 잡는다. 요소끼리 포개지는 사고는
    이 함수로 잡는다 — 렌더해서 눈으로 발견하기 전에.
    """
    items = [(n, _bbox(m)) for m, n in named]
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            na, (l1, r1, b1, t1) = items[i]
            nb, (l2, r2, b2, t2) = items[j]
            if (
                l1 + pad < r2 - pad and l2 + pad < r1 - pad
                and b1 + pad < t2 - pad and b2 + pad < t1 - pad
            ):
                raise OverlapError(
                    f"'{na}' 와 '{nb}' 가 겹칩니다: "
                    f"{na} x[{l1:.2f},{r1:.2f}] y[{b1:.2f},{t1:.2f}] / "
                    f"{nb} x[{l2:.2f},{r2:.2f}] y[{b2:.2f},{t2:.2f}]"
                )


def fit(mob: Mobject, max_w: float = SAFE_W, max_h: float | None = None) -> Mobject:
    """세이프 폭/높이를 넘으면 비율을 유지한 채 축소한다."""
    scale = 1.0
    if mob.width > max_w:
        scale = min(scale, max_w / mob.width)
    if max_h is not None and mob.height > max_h:
        scale = min(scale, max_h / mob.height)
    if scale < 1.0:
        mob.scale(scale)
    return mob


def guard(mob: Mobject, name: str = "mobject", shrink: bool = True) -> Mobject:
    """
    세이프 에어리어 밖으로 나가면 자동으로 줄이고 밀어 넣는다.
    끝내 들어가지 않으면 예외 — 렌더 전에 잘림을 잡는다.
    """
    if shrink:
        fit(mob, SAFE_W, SAFE_H)

    l, r = mob.get_left()[0], mob.get_right()[0]
    b, t = mob.get_bottom()[1], mob.get_top()[1]

    if r > SAFE_R:
        mob.shift(LEFT * (r - SAFE_R))
    if mob.get_left()[0] < SAFE_L:
        mob.shift(RIGHT * (SAFE_L - mob.get_left()[0]))
    if t > SAFE_T:
        mob.shift(DOWN * (t - SAFE_T))
    if mob.get_bottom()[1] < SAFE_B:
        mob.shift(UP * (SAFE_B - mob.get_bottom()[1]))

    l, r = mob.get_left()[0], mob.get_right()[0]
    b, t = mob.get_bottom()[1], mob.get_top()[1]
    eps = 1e-3
    if l < SAFE_L - eps or r > SAFE_R + eps or b < SAFE_B - eps or t > SAFE_T + eps:
        raise SafeAreaError(
            f"'{name}' 이(가) 세이프 에어리어를 벗어납니다: "
            f"x[{l:.2f},{r:.2f}] y[{b:.2f},{t:.2f}] "
            f"(허용 x[{SAFE_L},{SAFE_R}] y[{SAFE_B},{SAFE_T}])"
        )
    return mob


# ============================================================
# 5. 텍스트 · 카드
# ============================================================
def txt(
    s: str,
    size: float = FS_BODY,
    color: str = INK,
    bold: bool = True,
    line_spacing: float = 0.9,
    max_w: float | None = None,
) -> Text:
    t = Text(
        s,
        font=FONT,
        font_size=size,
        color=color,
        weight=BOLD if bold else NORMAL,
        line_spacing=line_spacing,
    )
    if max_w is not None:
        fit(t, max_w)
    return t


def num(s: str, color: str = ACCENT, size: float = FS_NUM) -> Text:
    """숫자는 항상 크게, 단독으로 — 바이블 §2"""
    return txt(s, size=size, color=color, bold=True)


def card(
    *rows: Mobject,
    width: float = 7.6,
    color: str = INK,
    accent: bool = False,
    pad_y: float = 0.42,
    gap: float = 0.24,
    corner: float = 0.22,
) -> VGroup:
    """
    라운드 박스 + 내부 세로 정렬 컨텐츠.
    박스 높이를 컨텐츠에 맞춰 계산하므로 텍스트가 박스 밖으로 새지 않는다.
    """
    body = VGroup(*rows).arrange(DOWN, buff=gap)
    fit(body, width - 0.7)

    frame = RoundedRectangle(
        corner_radius=corner,
        width=width,
        height=body.height + pad_y * 2,
        color=ACCENT if accent else color,
        stroke_width=STROKE if accent else 2,
    )
    frame.set_fill(BG, opacity=0.92)
    body.move_to(frame.get_center())
    return VGroup(frame, body)


def rule(width: float = 6.6, color: str = MUTE) -> Line:
    return Line(LEFT * width / 2, RIGHT * width / 2, color=color, stroke_width=1.5)


def tag(s: str, color: str = SUB) -> Text:
    """상단 소제목/카테고리 태그."""
    return txt(s, size=FS_TAG, color=color, bold=True)


def footnote(s: str) -> Text:
    """학설 구분·출처 각주 — 바이블 §8"""
    return txt(s, size=FS_TAG, color=DIM, bold=False)


# ============================================================
# 6. 픽토그램 (벡터 실루엣) — 이모지 금지
# ============================================================
# Manim/Pango 는 컬러 이모지(💡⚙️)를 렌더하지 못하고 빈 칸으로 떨어뜨린다.
# 픽토그램은 반드시 아래 벡터 함수로 만든다.
def _solid(m: VMobject, color: str) -> VMobject:
    return m.set_stroke(width=0).set_fill(color, opacity=1)


def pict_person(color: str = INK, height: float = 1.0) -> VGroup:
    head = _solid(Circle(radius=0.21), color).move_to(UP * 0.44)
    torso = _solid(
        RoundedRectangle(width=0.66, height=0.62, corner_radius=0.30), color
    ).move_to(DOWN * 0.12)
    skirt = _solid(Rectangle(width=0.66, height=0.30), color).move_to(DOWN * 0.28)
    g = VGroup(head, torso, skirt)
    g.set_height(height)
    return g


def pict_gear(color: str = INK, height: float = 1.0, teeth: int = 8) -> VGroup:
    body = _solid(Circle(radius=0.50), color)
    cogs = VGroup(
        *[
            _solid(Rectangle(width=0.19, height=0.26), color)
            .move_to(UP * 0.57)
            .rotate(TAU * i / teeth, about_point=ORIGIN)
            for i in range(teeth)
        ]
    )
    hub = _solid(Circle(radius=0.17), BG)
    g = VGroup(body, cogs, hub)
    g.set_height(height)
    return g


def pict_bulb(color: str = INK, height: float = 1.0) -> VGroup:
    glass = _solid(Circle(radius=0.40), color).move_to(UP * 0.22)
    neck = _solid(Rectangle(width=0.34, height=0.20), color).move_to(DOWN * 0.18)
    base = _solid(
        RoundedRectangle(width=0.40, height=0.26, corner_radius=0.08), color
    ).move_to(DOWN * 0.38)
    g = VGroup(glass, neck, base)
    g.set_height(height)
    return g


def pict_coal(color: str = INK, height: float = 1.0) -> VGroup:
    a = _solid(
        Polygon(
            [-0.50, -0.28, 0], [-0.22, 0.22, 0], [0.16, 0.30, 0],
            [0.48, -0.06, 0], [0.30, -0.34, 0], [-0.18, -0.36, 0],
        ),
        color,
    )
    b = _solid(
        Polygon([-0.02, 0.10, 0], [0.26, 0.44, 0], [0.52, 0.20, 0], [0.34, -0.02, 0]),
        color,
    ).set_opacity(0.75)
    g = VGroup(a, b)
    g.set_height(height)
    return g


def pict_doc(color: str = INK, height: float = 1.0, seal: str | None = None) -> VGroup:
    page = _solid(
        Polygon(
            [-0.34, 0.52, 0], [0.14, 0.52, 0], [0.36, 0.30, 0],
            [0.36, -0.52, 0], [-0.34, -0.52, 0],
        ),
        color,
    )
    fold = _solid(Polygon([0.14, 0.52, 0], [0.14, 0.30, 0], [0.36, 0.30, 0]), BG)
    parts = [page, fold]
    if seal:
        parts.append(_solid(Circle(radius=0.13), seal).move_to([0.10, -0.30, 0]))
    g = VGroup(*parts)
    g.set_height(height)
    return g


def pict_factory(color: str = INK, height: float = 1.0) -> VGroup:
    base = _solid(Rectangle(width=1.10, height=0.44), color).move_to(DOWN * 0.30)
    saw = VGroup(
        *[
            _solid(Polygon([-0.18, 0, 0], [0.0, 0.22, 0], [0.18, 0, 0]), color).move_to(
                RIGHT * (-0.36 + i * 0.36) + DOWN * 0.01
            )
            for i in range(3)
        ]
    )
    stack = _solid(Rectangle(width=0.20, height=0.72), color).move_to(
        LEFT * 0.44 + UP * 0.26
    )
    g = VGroup(base, saw, stack)
    g.set_height(height)
    return g


def pict_coin(color: str = INK, height: float = 1.0) -> VGroup:
    """동전 더미. 위쪽부터 그려 아래 동전이 위를 덮게 한다."""
    g = VGroup()
    for i in (2, 1, 0):
        e = Ellipse(width=0.92, height=0.32)
        e.set_stroke(color, 6).set_fill(BG, opacity=1)
        e.move_to(DOWN * 0.34 + UP * 0.34 * i)
        g.add(e)
    g.set_height(height)
    return g


PICTOGRAMS = {
    "person": pict_person,
    "gear": pict_gear,
    "bulb": pict_bulb,
    "coal": pict_coal,
    "doc": pict_doc,
    "factory": pict_factory,
    "coin": pict_coin,
}


def cross_out(mob: Mobject, color: str = ACCENT, pad: float = 0.10) -> VGroup:
    """대상 위에 X 표시. 대상 크기를 따라간다."""
    ul, dr = mob.get_corner(UL), mob.get_corner(DR)
    ur, dl = mob.get_corner(UR), mob.get_corner(DL)
    return VGroup(
        Line(ul + np.array([pad, -pad, 0]), dr + np.array([-pad, pad, 0]),
             color=color, stroke_width=6),
        Line(ur + np.array([-pad, -pad, 0]), dl + np.array([pad, pad, 0]),
             color=color, stroke_width=6),
    )


# ============================================================
# 7. 씬 베이스 — 길이를 프레임 단위로 정확히 맞춘다
# ============================================================
MIN_RUN_TIME = 1.2  # 바이블 §3: run_time 최소 1.2초
_TIMING_STRICT = True


class DiagramScene(MovingCameraScene):
    """
    도해 컷 공통 베이스.

    - 배경(BG + MUTE 격자)을 자동으로 깐다
    - DURATION 을 선언하면 씬 길이가 그 값에 '정확히' 맞춰진다
      (모자라면 마지막 프레임을 유지, 넘치면 렌더 시 에러)
      => scenes.tsv 와 오디오 사이의 타임라인 드리프트가 구조적으로 불가능해진다
    - 마지막 LOOP_TAIL 초 동안 배경색으로 수렴시켜 반복 재생 이음매를 지운다

    MovingCameraScene 을 상속하므로 `dolly()` 로 카메라를 움직일 수 있다.
    기존 씬은 프레임을 건드리지 않으므로 동작이 달라지지 않는다.
    """

    DURATION: float | None = None
    LOOP_TAIL: float = 0.0  # >0 이면 씬 끝에서 BG 로 수렴 (마지막 컷 전용)
    SHOW_GRID: bool = True
    DRIFT: float = 0.0      # >0 이면 씬 내내 아주 느린 줌인 (초당 배율 증가분)

    def construct(self):
        self.camera.background_color = BG
        self._home = self.camera.frame.get_center()
        self._home_h = self.camera.frame.height
        if self.SHOW_GRID:
            self.add(self.backdrop())
        if self.DRIFT:
            self._start_drift()
        self.build()
        self._settle()

    @property
    def elapsed(self) -> float:
        """지금까지의 씬 길이(초). Scene.wait 은 내부적으로 play(Wait) 를 호출하므로
        직접 누적하면 이중 계산된다. 렌더러 시각을 그대로 쓴다."""
        return float(self.renderer.time)

    # --- 하위 클래스가 구현 ---
    def build(self):  # pragma: no cover
        raise NotImplementedError

    # --- 공통 요소 ---
    def backdrop(self) -> NumberPlane:
        return NumberPlane(
            x_range=[-4.5, 4.5, 1],
            y_range=[-8, 8, 1],
            background_line_style={
                "stroke_color": MUTE,
                "stroke_width": 1,
                "stroke_opacity": 0.08,
            },
            axis_config={"stroke_opacity": 0},
        )

    # --- 애니메이션 헬퍼 (바이블 타이밍 규칙 강제) ---
    def reveal(self, *mobs, run_time: float = MIN_RUN_TIME, shift=None, hold: float = 0.0):
        """요소 등장. run_time 하한 1.2초를 강제한다.

        여러 요소를 한 번에 넘겨도 동시에 튀어나오지 않는다 — 바이블 §3
        '동시 등장 금지'를 지키도록 살짝 시차(lag_ratio)를 둔다.
        shift 는 화면에 이미 떠 있는 다른 요소 위로 미끄러져 겹쳐 보이지
        않도록 이동 거리를 작게 눌러 둔다.
        """
        rt = max(run_time, MIN_RUN_TIME)
        capped_shift = None
        if shift is not None:
            mag = np.linalg.norm(shift)
            capped_shift = shift * (0.15 / mag) if mag > 0.15 else shift
        anims = []
        for m in mobs:
            if isinstance(m, Animation):
                anims.append(m)
            else:
                anims.append(FadeIn(m, shift=capped_shift if capped_shift is not None else ORIGIN))
        lag = 0.65 if len(anims) > 1 else 0.0
        self.play(AnimationGroup(*anims, lag_ratio=lag), run_time=rt)
        if hold:
            self.wait(hold)

    def draw(self, *mobs, run_time: float = MIN_RUN_TIME, hold: float = 0.0):
        rt = max(run_time, MIN_RUN_TIME)
        self.play(*[Create(m) for m in mobs], run_time=rt)
        if hold:
            self.wait(hold)

    def beat(self, t: float = 0.8):
        """등장 후 정지 — 바이블 §3 최소 0.8초."""
        self.wait(max(t, 0.0))

    # --- 카메라 (달리 인/아웃) ---
    def dolly(self, target=None, zoom: float = 1.0, run_time: float = MIN_RUN_TIME,
              hold: float = 0.0):
        """카메라를 밀거나 당긴다.

            self.dolly(card, zoom=0.62)   # card 로 달리 인
            self.dolly(zoom=1.0)          # 전체 뷰로 달리 아웃 (원위치)

        zoom < 1 이면 프레임이 좁아진다(= 확대). 안전 범위는 0.55~1.0.
        요소를 새로 만들지 않고 프레임만 움직이므로 guard() 와 충돌하지 않는다.
        """
        z = min(max(zoom, 0.45), 1.0)
        frame = self.camera.frame
        anims = [frame.animate.set(height=self._home_h * z)]
        if target is not None:
            c = target.get_center() if isinstance(target, Mobject) else target
            if isinstance(target, Mobject):
                # 대상을 화면 밖으로 잘라내는 줌은 허용하지 않는다.
                # guard() 가 요소를 지키듯 여기서는 프레임이 대상을 지킨다.
                aspect = config.frame_width / config.frame_height
                need = max(target.height, target.width / aspect) * 1.14
                z = max(z, need / self._home_h)
                z = min(z, 1.0)
            anims = [frame.animate.set(height=self._home_h * z).move_to(c)]
        elif z >= 1.0:
            anims = [frame.animate.set(height=self._home_h).move_to(self._home)]
        self.play(*anims, run_time=max(run_time, MIN_RUN_TIME),
                  rate_func=rate_functions.ease_in_out_sine)
        if hold:
            self.wait(hold)

    def _start_drift(self):
        """씬 내내 아주 느린 줌인. updater 라 다른 애니메이션과 겹쳐 돈다."""
        rate = self.DRIFT
        frame = self.camera.frame

        def _creep(m, dt):
            m.set(height=m.height * (1.0 - rate * dt))

        frame.add_updater(_creep)

    # --- 동적 강조 ---
    def count_up(self, target: str, color: str = ACCENT, size: float = FS_NUM,
                 run_time: float = MIN_RUN_TIME, at=ORIGIN, unit: str = ""):
        """숫자가 0 에서 목표값까지 굴러 올라간다. 수치 컷의 기본기.

            self.count_up("1,750", unit="km")

        정수·소수·천단위 콤마를 그대로 복원한다. 반환값은 화면에 남는 VGroup.
        """
        digits = target.replace(",", "")
        dec = len(digits.split(".")[1]) if "." in digits else 0
        value = float(digits)
        comma = "," in target

        tracker = ValueTracker(0.0)
        label = num("0", color=color, size=size)
        u = tag(unit, color=color) if unit else None

        def _fmt(m):
            v = tracker.get_value()
            s = f"{v:,.{dec}f}" if comma else f"{v:.{dec}f}"
            m.become(num(s, color=color, size=size).move_to(at))
            # 자릿수가 늘면 폭이 커진다. 단위는 매 프레임 따라붙어야 겹치지 않는다.
            if u is not None:
                u.next_to(m, RIGHT, buff=0.18).align_to(m, DOWN)

        label.add_updater(_fmt)
        group = VGroup(label)
        if u is not None:
            group.add(u)
        self.add(group)
        self.play(tracker.animate.set_value(value),
                  run_time=max(run_time, MIN_RUN_TIME),
                  rate_func=rate_functions.ease_out_expo)
        label.remove_updater(_fmt)
        return group

    def pulse(self, mob: Mobject, times: int = 2, scale: float = 1.06,
              run_time: float = 0.45):
        """한 요소를 두어 번 맥동시켜 시선을 잡는다. 결정타 자리에만.

        scale 은 1.03 을 넘지 않도록 눌러 둔다 — 갓 fade-in 한 요소가
        곧바로 커졌다 작아지면 '툭 튀어나오는' 느낌이 과해진다.
        """
        scale = min(scale, 1.03)
        for _ in range(times):
            self.play(mob.animate.scale(scale), run_time=run_time / 2,
                      rate_func=rate_functions.ease_out_sine)
            self.play(mob.animate.scale(1 / scale), run_time=run_time / 2,
                      rate_func=rate_functions.ease_in_sine)

    def sweep(self, mob: Mobject, color: str = ACCENT, run_time: float = MIN_RUN_TIME):
        """요소 위를 빛줄기가 한 번 훑고 지나간다 (계측선 연출)."""
        box = mob.get_critical_point(UL), mob.get_critical_point(DR)
        line = Line(
            [box[0][0], box[0][1] + 0.1, 0],
            [box[0][0], box[1][1] - 0.1, 0],
            stroke_color=color, stroke_width=5, stroke_opacity=0.9,
        )
        self.add(line)
        self.play(line.animate.shift(RIGHT * (box[1][0] - box[0][0])),
                  run_time=max(run_time, MIN_RUN_TIME),
                  rate_func=rate_functions.ease_in_out_sine)
        self.play(FadeOut(line), run_time=0.3)

    # --- 길이 정합 ---
    def _settle(self):
        if self.LOOP_TAIL > 0:
            self._collapse_to_bg(self.LOOP_TAIL)

        if self.DURATION is None:
            return

        target = self.DURATION
        now = self.elapsed
        slack = target - now
        if slack > 1 / FPS:
            self.wait(slack)
        elif slack < -1 / FPS:
            msg = (
                f"{type(self).__name__}: 애니메이션 길이 {now:.2f}s 가 "
                f"선언 길이 {target:.2f}s 를 초과했습니다 ({-slack:.2f}s 초과)."
            )
            # 프레임 양자화로 1~2프레임 넘치는 것은 build 가 잘라내므로 경고만 한다.
            if _TIMING_STRICT and slack < -3 / FPS:
                raise RuntimeError(msg)
            print("[warn]", msg)

    def _collapse_to_bg(self, dur: float):
        """
        마지막 컷 전용. 화면의 모든 요소를 배경색으로 수렴시킨다.
        끝 프레임 = 순수 BG → 첫 컷의 BG 페이드인과 만나 루프 이음매가 사라진다.
        """
        movers = [m for m in self.mobjects if m is not None]
        if not movers:
            self.wait(dur)
            return
        self.play(
            *[FadeOut(m, scale=0.94) for m in movers],
            run_time=max(dur, 0.4),
            rate_func=rate_functions.ease_in_sine,
        )


# ============================================================
# 8. 자주 쓰는 조합
# ============================================================
def title_block(text: str, sub_text: str | None = None, y: float = SAFE_T) -> VGroup:
    """상단 제목. 세이프 상단에 붙인다."""
    parts = [txt(text, size=FS_TITLE, color=INK, max_w=SAFE_W)]
    if sub_text:
        parts.append(txt(sub_text, size=FS_CAPTION, color=DIM, bold=False, max_w=SAFE_W))
    g = VGroup(*parts).arrange(DOWN, buff=0.22)
    g.move_to(UP * (y - g.height / 2))
    return guard(g, "title_block")


def down_arrow(color: str = ACCENT, length: float = 0.9) -> Arrow:
    return Arrow(
        start=UP * length / 2,
        end=DOWN * length / 2,
        color=color,
        stroke_width=6,
        max_tip_length_to_length_ratio=0.35,
        buff=0,
    )


def converge_arrows(src_a: Mobject, src_b: Mobject, dst: Mobject, color: str = ACCENT):
    """두 원인 → 하나의 결과. 인과 화살표 패턴."""
    a = Arrow(
        src_a.get_bottom(), dst.get_top() + LEFT * 0.7,
        color=color, stroke_width=5, buff=0.16,
        max_tip_length_to_length_ratio=0.22,
    )
    b = Arrow(
        src_b.get_bottom(), dst.get_top() + RIGHT * 0.7,
        color=color, stroke_width=5, buff=0.16,
        max_tip_length_to_length_ratio=0.22,
    )
    return VGroup(a, b)


__all__ = [n for n in dir() if not n.startswith("_")]
