"""
S04 — 수치·비용 구조 비교 : 인쇄 시장의 생존 방정식
나레이션: "진짜 방아쇠는 기술 혁신이 아니라 인쇄업자들의 생존 문제였거든요."

라틴어 대작(자본 잠식/파산 위험) vs 모국어 소책자(빠른 회전율/폭발적 흑자) 비교.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "scripts"))
from lib_style import *  # noqa: F403


class S04Scene(DiagramScene):
    DURATION = 5.47  # timing.json 과 일치
    DRIFT = 0.004

    def build(self):
        head = title_block("초기 인쇄소의 경제적 생존 구조")

        # --- 1. 라틴어 대형 성경 (만성 적자) ---
        card_a = card(
            tag("전통 출판물", color=DIM),
            VGroup(
                pict_doc(DIM, height=1.1),
                VGroup(
                    txt("라틴어 대형 성경", size=FS_LEAD, color=DIM),
                    txt("막대한 양피지·활자 비용 · 수년의 회수 기간", size=FS_CAPTION, color=DIM, bold=False),
                ).arrange(DOWN, buff=0.15, aligned_edge=LEFT),
            ).arrange(RIGHT, buff=0.35),
            width=7.8,
            color=MUTE,
            pad_y=0.45,
        )
        # 제목 바로 아래로 바짝 붙이고, card_b 를 세이프 하단까지 끌어내려
        # 두 카드 사이의 화살표가 화면 중단~하단을 채우게 한다.
        card_a.move_to(UP * 4.3)
        guard(card_a, "card_a")

        # --- 3. 모국어 소책자 (폭발적 흑자) ---
        card_b = card(
            tag("대중 출판물", color=SUB),
            VGroup(
                pict_coin(INK, height=1.2),
                VGroup(
                    txt("모국어 논쟁 소책자", size=FS_LEAD, color=INK),
                    txt("수일 내 인쇄 · 1/100 가격 · 당일 완판", size=FS_CAPTION, color=INK, bold=False),
                ).arrange(DOWN, buff=0.15, aligned_edge=LEFT),
            ).arrange(RIGHT, buff=0.35),
            footnote("출처: A. Pettegree, Brand Luther (2015)"),
            width=7.8,
            accent=True,
            pad_y=0.50,
        )
        card_b.move_to(DOWN * 2.5)  # guard() 가 세이프 하단 경계까지 끌어올린다
        guard(card_b, "card_b")

        # --- 2. 전환 대비 (두 카드 사이 빈 공간을 화살표로 채운다) ---
        link = Arrow(
            card_a.get_bottom() + DOWN * 0.15,
            card_b.get_top() + UP * 0.15,
            color=SUB,
            stroke_width=4,
            buff=0.0,
            max_tip_length_to_length_ratio=0.10,
        )
        vs_lbl = txt("생존의 돌파구", size=FS_CAPTION, color=SUB, bold=True, outline=True)
        vs_lbl.move_to(link.get_center() + RIGHT * 1.5)

        no_overlap((card_a, "card_a"), (vs_lbl, "vs_lbl"), (card_b, "card_b"))

        self.play(
            AnimationGroup(
                FadeIn(head, shift=DOWN * 0.25),
                FadeIn(card_a, shift=RIGHT * 0.25),
                lag_ratio=0.3,
            ),
            run_time=1.4,
        )
        self.beat(0.4)

        self.reveal(link, vs_lbl, card_b, run_time=1.4, shift=UP * 0.25)
        self.pulse(card_b, times=1, scale=1.03, run_time=0.4)
