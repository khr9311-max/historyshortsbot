"""
S04 — 인과 화살표 : 징세 청부(외주) vs 직접 관료 징수
나레이션: "핵심은 세금을 누가 어떻게 걷었는가였거든요."

색·폰트·크기·세이프에어리어는 scripts/lib_style.py (스타일 바이블) 에서만 가져온다.
ACCENT 는 '채택되는 설명' 한 곳에만 쓴다 (바이블 §1).
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "scripts"))
from lib_style import *  # noqa: F403


class S04Scene(DiagramScene):
    DURATION = 4.21  # timing.json 과 일치
    DRIFT = 0.004    # 씬 내내 아주 느린 줌인

    def build(self):
        head = title_block("두 제국의 조세 징수 구조 비교")

        # --- 상단: 프랑스 구체제 (민간 징세 청부제) ---
        t_top = tag("프랑스 · 징세 청부제 (민간 외주)", color=SUB)
        row_top = VGroup(
            pict_person(DIM, height=0.85),
            txt("민간업자 중간 착복\n→ 국고 유입분 대폭 누수", size=FS_BODY, color=DIM),
        ).arrange(RIGHT, buff=0.35)
        card_top = card(
            VGroup(t_top, row_top).arrange(DOWN, buff=0.18),
            width=7.8,
            color=MUTE,
            pad_y=0.40,
        )
        card_top.move_to(UP * 4.3)
        guard(card_top, "card_top")

        # --- 하단: 영국 (중앙 관료 직접 징수) ---
        t_bot = tag("영국 · 소비세청 직접 징수", color=ACCENT)
        row_bot = VGroup(
            pict_coin(INK, height=0.85),
            txt("투명한 국고 유입\n→ 국가 신용도 및 전비 조달력 극대화", size=FS_BODY, color=INK),
        ).arrange(RIGHT, buff=0.35)
        note_bot = footnote("출처: P. O'Brien (1988) / P. Hoffman (1994)")
        card_bot = card(
            VGroup(t_bot, row_bot, note_bot).arrange(DOWN, buff=0.18),
            width=7.8,
            accent=True,
            pad_y=0.45,
        )
        card_bot.move_to(DOWN * 2.3)
        guard(card_bot, "card_bot")

        # 연결/비교 화살표
        link = Arrow(
            card_top.get_bottom() + DOWN * 0.12,
            card_bot.get_top() + UP * 0.12,
            color=MUTE,
            stroke_width=4,
            buff=0.0,
            max_tip_length_to_length_ratio=0.10,
        )
        mid_txt = txt("vs 직접 징수", size=FS_CAPTION, color=DIM, bold=False, outline=True)
        mid_txt.move_to(link.get_center() + RIGHT * 1.6)

        no_overlap((card_top, "card_top"), (mid_txt, "vs 직접 징수"), (card_bot, "card_bot"))

        self.play(
            AnimationGroup(
                FadeIn(head, shift=DOWN * 0.25),
                FadeIn(card_top, shift=RIGHT * 0.25),
                lag_ratio=0.20,
            ),
            run_time=1.3,
        )

        self.reveal(link, mid_txt, card_bot, run_time=1.3, shift=UP * 0.20)
        self.pulse(card_bot, times=1, scale=1.03, run_time=0.4)
