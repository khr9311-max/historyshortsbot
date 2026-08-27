"""
S04 — 수치 그래프 / 한계선 도해 (거리의 수학: 500km 보급 한계선)
나레이션: "전염병이나 탈영을 꼽는 반론도 있지만, 핵심은 날씨가 아니라 '거리의 수학'이었습니다."

색·폰트·크기·세이프에어리어는 scripts/lib_style.py (스타일 바이블) 에서만 가져온다.
ACCENT 는 '500km 한계 수치' 한 곳에만 쓴다 (바이블 §1).
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "scripts"))
from lib_style import *  # noqa: F403


class S04Scene(DiagramScene):
    DURATION = 7.36  # timing.json 과 일치
    DRIFT = 0.004

    def build(self):
        head = title_block("19세기 마차 보급선의 수학적 한계")

        # --- 상단 카드: 마차 운송 메커니즘 설명 ---
        t_top = tag("마차 수송의 치명적 제약", color=SUB)
        row_top = VGroup(
            pict_gear(DIM, height=0.85),
            txt("말을 먹일 건초도 짐칸에 적재\n→ 거리 비례 자체 식량 소모 급증", size=FS_BODY, color=DIM),
        ).arrange(RIGHT, buff=0.35)
        card_top = card(
            VGroup(t_top, row_top).arrange(DOWN, buff=0.16),
            width=7.8,
            color=MUTE,
            pad_y=0.38,
        )
        card_top.move_to(UP * 4.4)
        guard(card_top, "card_top")

        # --- 하단 카드: 500km 한계선 데이터 ---
        t_bot = tag("수학적 보급 한계선", color=ACCENT)
        num_block = VGroup(
            txt("유효 보급 한계", size=FS_LEAD, color=INK),
            txt("500 km", size=FS_NUM, color=ACCENT),
            txt("(편도 15~20일 소요 시 적재 식량 100% 소진)", size=FS_CAPTION, color=DIM, bold=False),
            footnote("출처: Martin van Creveld, Supplying War (1977)"),
        ).arrange(DOWN, buff=0.15)

        card_bot = card(
            VGroup(t_bot, num_block).arrange(DOWN, buff=0.16),
            width=7.8,
            accent=True,
            pad_y=0.42,
        )
        card_bot.move_to(DOWN * 2.1)
        guard(card_bot, "card_bot")

        # 연결/도출 화살표
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
        self.beat(0.4)

        self.reveal(link, card_bot, run_time=1.5, shift=UP * 0.20)
        self.pulse(card_bot, times=1, scale=1.03, run_time=0.4)
        self.beat(0.8)
