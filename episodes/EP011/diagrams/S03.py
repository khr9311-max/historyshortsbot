"""
S03 픽토그램 컷: 통념 부정 (지형/게릴라 X, 목표 비대칭성 O)
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "scripts"))
from lib_style import *  # noqa: F403


class S03Scene(DiagramScene):
    DURATION = 9.81
    DRIFT = 0.004

    def build(self):
        head = title_block("강대국이 패배하는 진짜 이유")

        # --- 통념 ---
        t_wrong = tag("흔히 생각하는 원인", color=MUTE)
        row_wrong = VGroup(
            pict_person(DIM, height=0.85),
            txt("게릴라 전술과 험난한 지형", size=FS_BODY, color=DIM),
        ).arrange(RIGHT, buff=0.35)
        
        wrong = card(
            VGroup(t_wrong, row_wrong).arrange(DOWN, buff=0.16),
            width=7.8,
            color=MUTE,
            pad_y=0.38,
        )
        wrong.move_to(UP * 4.4)
        guard(wrong, "wrong-card")

        self.play(
            AnimationGroup(
                FadeIn(head, shift=DOWN * 0.25),
                FadeIn(wrong, shift=RIGHT * 0.25),
                lag_ratio=0.20,
            ),
            run_time=1.1,
        )

        # 픽토그램 위에 X 표시
        x_mark = cross_out(wrong, DIM, pad=-0.14)
        self.draw(x_mark, run_time=0.7)

        # --- 진짜 원인 ---
        t_right = tag("핵심 원인 (인과)", color=ACCENT)
        num_block = VGroup(
            txt("목표의 비대칭성", size=FS_NUM, color=ACCENT),
            txt("강대국(국익·제한전) vs 약소국(생존·총력전)", size=FS_BODY, color=INK),
            footnote("출처: Andrew Mack (1975) / Ivan Arreguín-Toft (2005)"),
        ).arrange(DOWN, buff=0.15)

        right = card(
            VGroup(t_right, num_block).arrange(DOWN, buff=0.16),
            width=7.8,
            accent=True,
            pad_y=0.42,
        )
        right.move_to(DOWN * 2.1)
        guard(right, "right-card")

        link = down_arrow(color=MUTE, length=0.8)
        link.move_to(VGroup(wrong, right).get_center())

        no_overlap((wrong, "wrong-card"), (link, "화살표"), (right, "right-card"))

        self.reveal(link, right, run_time=1.1, shift=UP * 0.20)
        self.pulse(right, times=1, scale=1.03, run_time=0.35)
