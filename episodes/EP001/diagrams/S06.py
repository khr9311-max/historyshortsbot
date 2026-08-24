"""
S06 — 수치 그래프 : 기계 도입의 채산성 (프랑스 vs 영국)
나레이션: "증기기관은 석탄을 쏟아부어야 겨우 돌았습니다.
          그 낭비가 이득이 되는 곳은 영국뿐이었죠."

수치 출처: Robert C. Allen, *The British Industrial Revolution in Global
Perspective* (Cambridge UP, 2009) — 은화 환산 임금 및 에너지 가격 비교.
근사치이므로 화면에 '약'과 출처를 함께 표기한다 (바이블 §8).

이전 판의 사고 두 건을 코드로 막는다.
  - '손익분기점 (0)' 라벨이 화면 오른쪽 밖으로 86px 잘려 나갔다 → guard()
  - 프랑스 설명과 수치 블록이 포개졌다                        → no_overlap()

화면 세로를 네 개 띠로 나눠 쓴다.
  제목 6.9~5.9 / 그래프 5.6~1.2 / 국가 라벨 1.2~-0.6 / 수치 -0.8~-3.4
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "scripts"))
from lib_style import *  # noqa: F403

BASE_Y = 2.55         # 손익분기선
BAR_W = 1.8
FR_X, UK_X = -1.95, 1.95


class S06Scene(DiagramScene):
    DURATION = 7.90

    def build(self):
        head = title_block("같은 기계, 다른 계산")
        self.reveal(head, run_time=1.2, shift=DOWN * 0.25)

        # --- 축 먼저 (바이블 §3 '수치 그래프' 문법) ---
        base = Line(LEFT * 3.6, RIGHT * 3.6, color=MUTE, stroke_width=2)
        base.move_to(UP * BASE_Y)
        zero = tag("손익분기 0", DIM)
        # 선의 왼쪽 '위' 빈 공간. 오른쪽 끝에 붙이면 화면 밖으로 나간다.
        zero.next_to(base.get_left(), UP, buff=0.14, aligned_edge=LEFT)
        axis = VGroup(base, zero)
        guard(axis, "baseline")
        self.reveal(Create(base), FadeIn(zero), run_time=1.2)

        # --- 프랑스: 적자 (기준선 아래로 자란다) ---
        fr_bar = Rectangle(
            width=BAR_W, height=1.25,
            color=MUTE, fill_color=MUTE, fill_opacity=0.35, stroke_width=2,
        )
        fr_bar.next_to([FR_X, BASE_Y, 0], DOWN, buff=0, aligned_edge=UP)
        fr_txt = txt("프랑스\n사람값이 싸다", size=FS_CAPTION, color=DIM, bold=False)
        fr_txt.next_to(fr_bar, DOWN, buff=0.3)
        fr = VGroup(fr_bar, fr_txt)

        # --- 영국: 흑자 (기준선 위로 자란다) — 화면의 유일한 ACCENT ---
        uk_bar = Rectangle(
            width=BAR_W, height=2.85,
            color=ACCENT, fill_color=ACCENT, fill_opacity=0.55, stroke_width=STROKE,
        )
        uk_bar.next_to([UK_X, BASE_Y, 0], UP, buff=0, aligned_edge=DOWN)
        uk_cap = txt("그래서 기계가 이득", size=FS_CAPTION, color=ACCENT)
        uk_cap.next_to(uk_bar, UP, buff=0.28)
        uk_txt = txt("영국\n사람값이 비싸다", size=FS_CAPTION, color=INK)
        uk_txt.next_to([UK_X, BASE_Y, 0], DOWN, buff=0.3)
        uk = VGroup(uk_bar, uk_cap, uk_txt)

        # --- 수치는 크게, 단독으로 (바이블 §2) ---
        def figure(value: str, what: str, versus: str):
            return VGroup(
                num(value, color=SUB, size=fs(6.2)),
                txt(what, size=FS_CAPTION, color=INK),
                txt(versus, size=FS_TAG, color=DIM, bold=False),
            ).arrange(DOWN, buff=0.13)

        figures = VGroup(
            figure("약 2배", "런던 임금", "파리 대비"),
            figure("약 1/4", "석탄 가격", "대륙 대비"),
        ).arrange(RIGHT, buff=1.4)
        note = footnote("※ 은화 환산 근사치 · Allen(2009)")
        block = VGroup(figures, note).arrange(DOWN, buff=0.3)
        block.move_to(DOWN * 2.05)

        for m, n in ((fr, "france"), (uk, "britain"), (block, "figures")):
            guard(m, n)
        no_overlap(
            (head, "title"), (axis, "baseline"),
            (fr_txt, "france-label"), (uk_txt, "britain-label"),
            (uk_cap, "britain-caption"), (block, "figures"),
        )

        self.play(GrowFromEdge(fr_bar, UP), FadeIn(fr_txt), run_time=1.4)
        self.beat(0.4)
        self.play(
            GrowFromEdge(uk_bar, DOWN), FadeIn(uk_cap), FadeIn(uk_txt), run_time=1.6
        )
        self.reveal(block, run_time=1.3, shift=UP * 0.2)
