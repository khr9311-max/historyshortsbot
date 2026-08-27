"""
S06 픽토그램 컷: 손익 계산의 차이
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "scripts"))
from lib_style import *  # noqa: F403


class S06Scene(DiagramScene):
    DURATION = 8.14
    DRIFT = 0.004

    def build(self):
        head = title_block("전비와 목표의 비대칭성")

        # --- 상단: 강대국 vs 약소국 대비 카드 ---
        t_left = tag("강대국 (제한전)", color=DIM)
        txt_left = txt("국익 추구\n비용 상한선 존재", size=FS_BODY, color=DIM)
        left = card(
            VGroup(t_left, txt_left).arrange(DOWN, buff=0.15),
            width=3.7,
            color=MUTE,
            pad_y=0.35,
        )
        left.move_to(UP * 4.3 + LEFT * 2.1)
        guard(left, "left-card")

        t_right = tag("약소국 (총력전)", color=SUB)
        txt_right = txt("생존 추구\n무한대 비용 감내", size=FS_BODY, color=INK)
        right = card(
            VGroup(t_right, txt_right).arrange(DOWN, buff=0.15),
            width=3.7,
            accent=False,
            color=INK,
            pad_y=0.35,
        )
        right.move_to(UP * 4.3 + RIGHT * 2.1)
        guard(right, "right-card")

        # --- 하단: 비용 한계 초과 카드 ---
        t_bot = tag("강대국의 한계 도달 메커니즘", color=ACCENT)
        bot_content = VGroup(
            txt("전쟁 비용 > 국익 (예상 이익)", size=FS_LEAD, color=ACCENT),
            txt("→ 사상자·정치적 비용 누적으로 '철수'", size=FS_BODY, color=INK),
        ).arrange(DOWN, buff=0.15)
        
        bot_card = card(
            VGroup(t_bot, bot_content).arrange(DOWN, buff=0.16),
            width=7.8,
            accent=True,
            pad_y=0.42,
        )
        bot_card.move_to(DOWN * 1.8)
        guard(bot_card, "bot-card")

        link = down_arrow(color=MUTE, length=0.8)
        link.move_to(VGroup(left, bot_card).get_center() + RIGHT * 2.1)

        self.play(
            AnimationGroup(
                FadeIn(head, shift=DOWN * 0.25),
                FadeIn(left, shift=RIGHT * 0.25),
                FadeIn(right, shift=LEFT * 0.25),
                lag_ratio=0.15,
            ),
            run_time=1.2,
        )

        self.reveal(link, bot_card, run_time=1.1, shift=UP * 0.20)
        self.pulse(bot_card, times=1, scale=1.03, run_time=0.35)
