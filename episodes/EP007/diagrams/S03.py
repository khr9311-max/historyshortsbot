"""
S03 — 픽토그램 대비 : 통념 부정 (인쇄술 발명 vs 종교 갈등 직행 ✕)
나레이션: "인쇄기가 종교 갈등을 홀로 만든 건 아니었습니다."

색·폰트·크기·세이프에어리어는 scripts/lib_style.py (스타일 바이블) 에서만 가져온다.
X 표시는 픽토그램 위에만 올린다.
ACCENT 는 '채택되는 설명' 한 곳에만 쓴다 (바이블 §1).
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "scripts"))
from lib_style import *  # noqa: F403


class S03Scene(DiagramScene):
    DURATION = 4.07  # timing.json 과 일치
    DRIFT = 0.004    # 씬 내내 아주 느린 줌인

    def build(self):
        head = title_block("활자 인쇄와 종교 분열의 경로")

        # --- 통념 (인쇄술 발명이 곧바로 종교 분열 직행) ---
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
        # 제목 바로 아래로 바짝 붙인다 — 카드가 상단 40%에만 몰리지 않도록
        # 아래쪽 right-card 를 세이프 하단까지 끌어내려 화면 전체를 쓴다.
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

        # --- 실제 역사적 결합 (세이프 하단까지 내려 화면 하단을 채운다) ---
        right = card(
            VGroup(
                pict_bulb(INK, height=1.35),
                txt("인쇄업자의 상업적 생존과\n분권 도시 네트워크의 결합", size=FS_LEAD, color=INK),
                footnote("출처: E. Eisenstein (1979) / A. Pettegree (2015)"),
            ).arrange(DOWN, buff=0.18),
            width=7.8,
            accent=True,
            pad_y=0.55,
        )
        right.move_to(DOWN * 2.4)  # guard() 가 세이프 하단 경계까지 끌어올린다
        guard(right, "right-card")

        # 두 카드 사이 빈 공간을 인과 화살표로 채운다 (바이블 §3 인과 화살표 패턴)
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
