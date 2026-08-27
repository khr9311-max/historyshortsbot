"""
S07 — 지도 이동 / 인과 도해 (러시아의 청야전술과 현지 조달 차단)
나레이션: "현지에서 뺏으면 되지 않냐고요? 러시아군은 후퇴하며 모든 물자를 불태워버렸습니다."

색·폰트·크기·세이프에어리어는 scripts/lib_style.py (스타일 바이블) 에서만 가져온다.
ACCENT 는 '보급선 단절 결과' 한 곳에만 쓴다 (바이블 §1).
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "scripts"))
from lib_style import *  # noqa: F403


class S07Scene(DiagramScene):
    DURATION = 8.95  # timing.json 과 일치
    DRIFT = 0.004

    def build(self):
        head = title_block("러시아군의 청야전술과 현지 조달 차단")

        # --- 상단: 청야전술 메커니즘 ---
        t_top = tag("러시아군의 조직적 청야전술", color=SUB)
        row_top = VGroup(
            pict_coal(DIM, height=0.90),
            txt("퇴각로 주변 식량·건초·우물 전면 소각\n→ 프랑스군 현지 약탈 원천 차단", size=FS_BODY, color=DIM),
        ).arrange(RIGHT, buff=0.35)
        card_top = card(
            VGroup(t_top, row_top).arrange(DOWN, buff=0.16),
            width=7.8,
            color=MUTE,
            pad_y=0.40,
        )
        card_top.move_to(UP * 4.3)
        guard(card_top, "card_top")

        # --- 하단: 보급망 마비 결과 ---
        t_bot = tag("현지 조달 완전 차단", color=ACCENT)
        row_bot = VGroup(
            pict_doc(INK, height=0.90),
            txt("현지 조달 불가 + 500km 한계선 직면\n→ 60만 대군 가용 식량 0% 도달", size=FS_BODY, color=INK),
            footnote("출처: C. von Clausewitz (1843) / D. Lieven (2009)"),
        ).arrange(DOWN, buff=0.15)
        card_bot = card(
            VGroup(t_bot, row_bot).arrange(DOWN, buff=0.16),
            width=7.8,
            accent=True,
            pad_y=0.42,
        )
        card_bot.move_to(DOWN * 2.2)
        guard(card_bot, "card_bot")

        # 연결 화살표
        link = down_arrow(color=MUTE, length=0.8)
        link.move_to(VGroup(card_top, card_bot).get_center())

        no_overlap((card_top, "card_top"), (link, "화살표"), (card_bot, "card_bot"))

        self.play(
            AnimationGroup(
                FadeIn(head, shift=DOWN * 0.25),
                FadeIn(card_top, shift=RIGHT * 0.25),
                lag_ratio=0.20,
            ),
            run_time=1.4,
        )
        self.beat(0.5)

        self.reveal(link, card_bot, run_time=1.6, shift=UP * 0.20)
        self.pulse(card_bot, times=1, scale=1.03, run_time=0.4)
        self.beat(1.0)
