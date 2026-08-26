"""
S04 — 수치 그래프 : 헥타르당 칼로리 생산성 비교 (밀 vs 감자)
나레이션: "하지만 1헥타르당 밀의 3배가 넘는 칼로리를 쏟아내며 기근의 사슬을 끊어냈죠."

색·폰트·크기·세이프에어리어는 scripts/lib_style.py (스타일 바이블) 에서만 가져온다.
숫자는 크게, 단독으로 (FS_NUM).
ACCENT 는 '감자 3.0배' 한 곳에만 쓴다 (바이블 §1).
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "scripts"))
from lib_style import *  # noqa: F403


class S04Scene(DiagramScene):
    DURATION = 5.90  # timing.json 과 일치
    DRIFT = 0.004    # 씬 내내 아주 느린 줌인

    def build(self):
        head = title_block("1헥타르당 생산 칼로리", sub_text="동일 면적 기준 에너지 공급량")

        # --- 밀 카드 (기준선 1.0배) ---
        wheat_card = card(
            VGroup(
                txt("전통 곡물 (밀·호밀)", size=FS_BODY, color=DIM),
                txt("1.0배", size=FS_NUM, color=DIM),
            ).arrange(DOWN, buff=0.2),
            width=7.8, color=MUTE, pad_y=0.45,
        )
        wheat_card.move_to(UP * 3.8)
        guard(wheat_card, "wheat-card")

        # --- 감자 카드 (3.0배 강조) ---
        potato_card = card(
            VGroup(
                tag("단위 면적당 칼로리 혁명", color=SUB),
                txt("감자 (Potato)", size=FS_LEAD, color=INK),
                txt("3.0배", size=FS_NUM, color=ACCENT),
                footnote("출처: W. McNeill (1999) / Nunn & Qian (2011)"),
            ).arrange(DOWN, buff=0.22),
            width=7.8, accent=True, pad_y=0.55,
        )
        potato_card.move_to(DOWN * 0.8)
        guard(potato_card, "potato-card")

        no_overlap((wheat_card, "wheat-card"), (potato_card, "potato-card"))

        self.play(
            AnimationGroup(
                FadeIn(head, shift=DOWN * 0.25),
                FadeIn(wheat_card, shift=UP * 0.25),
                lag_ratio=0.2,
            ),
            run_time=1.3,
        )

        self.reveal(potato_card, run_time=1.4, shift=UP * 0.3)
        self.pulse(potato_card, times=2, scale=1.04, run_time=0.5)
