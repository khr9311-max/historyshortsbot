"""
S04 — 지도 및 지리 장벽 대비 : 애팔래치아 산맥과 운송비 격차
나레이션: "진짜 장벽은 동부와 서부를 가로막은 애팔래치아 산맥이었거든요."

애팔래치아 산맥 육로(필라델피아/볼티모어 - 험준한 산악) vs 모호크 계곡 수운로(뉴욕 - 저고도 통로) 비교.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "scripts"))
from lib_style import *  # noqa: F403


class S04Scene(DiagramScene):
    DURATION = 5.49  # timing.json 과 일치
    DRIFT = 0.004

    def build(self):
        head = title_block("동서부를 가로막은 지리적 장벽과 물류")

        # --- 1. 애팔래치아 산맥 육로 (기존 방식) ---
        card_a = card(
            tag("기존 산악 육로 (필라델피아·볼티모어)", color=DIM),
            VGroup(
                pict_doc(DIM, height=1.1),
                VGroup(
                    txt("애팔래치아 산맥 마차 운송", size=FS_LEAD, color=DIM),
                    txt("톤당 $100 · 20일 이상 · 곡물값 초과 운임", size=FS_CAPTION, color=DIM, bold=False),
                ).arrange(DOWN, buff=0.15, aligned_edge=LEFT),
            ).arrange(RIGHT, buff=0.35),
            width=7.8,
            color=MUTE,
            pad_y=0.45,
        )
        card_a.move_to(UP * 4.3)
        guard(card_a, "card_a")

        # --- 2. 모호크 계곡 & 이리 운하 (자연 통로) ---
        card_b = card(
            tag("모호크 저고도 통로 (뉴욕)", color=SUB),
            VGroup(
                pict_coin(INK, height=1.2),
                VGroup(
                    txt("오대호-허드슨강 직결 수운", size=FS_LEAD, color=INK),
                    txt("톤당 $5~10 (95% 폭락) · 6일로 단축", size=FS_CAPTION, color=INK, bold=False),
                ).arrange(DOWN, buff=0.15, aligned_edge=LEFT),
            ).arrange(RIGHT, buff=0.35),
            footnote("출처: G. R. Taylor (1951) / R. Shaw (1990)"),
            width=7.8,
            accent=True,
            pad_y=0.50,
        )
        card_b.move_to(DOWN * 2.5)
        guard(card_b, "card_b")

        # --- 연결선 및 전환 대비 라벨 ---
        link = Arrow(
            card_a.get_bottom() + DOWN * 0.15,
            card_b.get_top() + UP * 0.15,
            color=SUB,
            stroke_width=4,
            buff=0.0,
            max_tip_length_to_length_ratio=0.10,
        )
        vs_lbl = txt("물류 혁명", size=FS_CAPTION, color=SUB, bold=True, outline=True)
        vs_lbl.move_to(link.get_center() + RIGHT * 1.5)

        no_overlap((card_a, "card_a"), (vs_lbl, "vs_lbl"), (card_b, "card_b"))

        self.play(
            AnimationGroup(
                FadeIn(head, shift=DOWN * 0.25),
                FadeIn(card_a, shift=RIGHT * 0.25),
                lag_ratio=0.3,
            ),
            run_time=1.3,
        )
        self.beat(0.3)

        self.reveal(link, vs_lbl, card_b, run_time=1.4, shift=UP * 0.25)
        self.pulse(card_b, times=1, scale=1.03, run_time=0.4)
