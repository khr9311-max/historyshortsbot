"""
S03 — 픽토그램 대비 : 통념 부정 (인쇄 기술 자체 vs 사회·경제적 결합)
나레이션: "인쇄 기술 자체가 갈등을 만든 건 아니었습니다."

색·폰트·크기·세이프에어리어는 scripts/lib_style.py (스타일 바이블) 에서만 가져온다.
X 표시는 픽토그램 위에만 올린다.
ACCENT 는 '채택되는 설명' 한 곳에만 쓴다 (바이블 §1).
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "scripts"))
from lib_style import *  # noqa: F403


class S03Scene(DiagramScene):
    DURATION = 4.04  # timing.json 과 일치
    DRIFT = 0.004    # 씬 내내 아주 느린 줌인

    def build(self):
        head = title_block("활자 인쇄와 사회적 파급의 경로")

        # --- 통념 (기술 하나가 곧바로 전쟁 직행) ---
        doc = pict_doc(DIM, height=1.35)
        wrong = card(
            VGroup(
                doc,
                txt("활자 인쇄 발명 직후\n종교 분열·전쟁 직행", size=FS_LEAD, color=DIM),
            ).arrange(RIGHT, buff=0.4),
            width=7.8,
            color=MUTE,
            pad_y=0.50,
        )
        wrong.move_to(UP * 4.3)
        guard(wrong, "wrong-card")

        self.play(
            AnimationGroup(
                FadeIn(head, shift=DOWN * 0.25),
                FadeIn(wrong, shift=RIGHT * 0.25),
                lag_ratio=0.20,
            ),
            run_time=1.2,
        )

        # 픽토그램 위에만 X 표시
        x_mark = cross_out(doc, DIM, pad=-0.14)
        self.draw(x_mark, run_time=1.2)

        # --- 실제 역사적 결합 ---
        right = card(
            VGroup(
                pict_bulb(INK, height=1.35),
                txt("인쇄소의 경제적 생존과\n분권 도시 네트워크의 결합", size=FS_LEAD, color=INK),
                footnote("출처: E. Eisenstein (1979) / A. Pettegree (2015)"),
            ).arrange(DOWN, buff=0.18),
            width=7.8,
            accent=True,
            pad_y=0.55,
        )
        right.move_to(DOWN * 2.4)
        guard(right, "right-card")

        # 두 카드 사이 연결 화살표
        link = Arrow(
            wrong.get_bottom() + DOWN * 0.15,
            right.get_top() + UP * 0.15,
            color=MUTE,
            stroke_width=4,
            buff=0.0,
            max_tip_length_to_length_ratio=0.10,
        )
        conj = txt("이 아니라", size=FS_CAPTION, color=DIM, bold=False, outline=True)
        conj.move_to(link.get_center() + RIGHT * 1.5)

        no_overlap((wrong, "wrong-card"), (conj, "이 아니라"), (right, "right-card"))

        self.reveal(link, conj, right, run_time=1.2, shift=UP * 0.20)
        self.pulse(right, times=1, scale=1.03, run_time=0.4)
