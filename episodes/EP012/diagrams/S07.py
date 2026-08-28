"""
S07 — 수치 및 전략 전환 대비 : 군대 규모 폭증과 요새 우회
나레이션: "20만 대군은 성벽을 그냥 지나쳤습니다."

16세기 소규모 군대(요새 공성 필수) vs 18세기 대규모 군대(요새 우회 기동전) 대조.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "scripts"))
from lib_style import *  # noqa: F403


class S07Scene(DiagramScene):
    DURATION = 3.31  # timing.json 과 일치
    DRIFT = 0.004

    def build(self):
        head = title_block("군대 규모 팽창과 전쟁 규칙의 변화")

        # --- 1. 16세기 군대 (2만 명 규모) ---
        card_a = card(
            tag("16세기 공성전 (군대 2만 명)", color=DIM),
            VGroup(
                pict_doc(DIM, height=1.1),
                VGroup(
                    txt("요새 포위 공성전 필수", size=FS_LEAD, color=DIM),
                    txt("수개월 소모 · 거점 함락이 승패 결정", size=FS_CAPTION, color=DIM, bold=False),
                ).arrange(DOWN, buff=0.12, aligned_edge=LEFT),
            ).arrange(RIGHT, buff=0.35),
            width=7.8,
            color=MUTE,
            pad_y=0.45,
        )
        card_a.move_to(UP * 4.3)
        guard(card_a, "card_a")

        # --- 2. 18세기 군대 (20만 명 규모) ---
        card_b = card(
            tag("18세기 기동전 (군대 20만 명)", color=SUB),
            VGroup(
                pict_gear(INK, height=1.2),
                VGroup(
                    txt("거점 요새 우회 (Bypass)", size=FS_LEAD, color=INK),
                    txt("성벽 무시 · 야전군 격멸 및 수도 직격", size=FS_CAPTION, color=INK, bold=False),
                ).arrange(DOWN, buff=0.12, aligned_edge=LEFT),
            ).arrange(RIGHT, buff=0.35),
            footnote("출처: John A. Lynn (1991)"),
            width=7.8,
            accent=True,
            pad_y=0.45,
        )
        card_b.move_to(DOWN * 2.4)
        guard(card_b, "card_b")

        # --- 연결 화살표 ---
        link = Arrow(
            card_a.get_bottom() + DOWN * 0.15,
            card_b.get_top() + UP * 0.15,
            color=SUB,
            stroke_width=4,
            buff=0.0,
            max_tip_length_to_length_ratio=0.10,
        )
        vs_lbl = txt("기동전 전환", size=FS_CAPTION, color=SUB, bold=True, outline=True)
        vs_lbl.move_to(link.get_center() + RIGHT * 1.5)

        no_overlap((card_a, "card_a"), (vs_lbl, "vs_lbl"), (card_b, "card_b"))

        self.play(
            AnimationGroup(
                FadeIn(head, shift=DOWN * 0.25),
                FadeIn(card_a, shift=RIGHT * 0.25),
                lag_ratio=0.25,
            ),
            run_time=1.0,
        )

        self.play(
            AnimationGroup(
                Create(link),
                FadeIn(vs_lbl, shift=UP * 0.15),
                FadeIn(card_b, shift=UP * 0.20),
                lag_ratio=0.20,
            ),
            run_time=1.1,
        )
        self.pulse(card_b, times=1, scale=1.03, run_time=0.3)
