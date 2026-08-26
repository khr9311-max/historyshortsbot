"""
S03 — 픽토그램 대비 : 통념 부정 (천혜의 자연 항구 vs 배후지 연결망)
나레이션: "단순히 타고난 천혜의 항구 때문이 아니었습니다."

색·폰트·크기·세이프에어리어는 scripts/lib_style.py (스타일 바이블) 에서만 가져온다.
X 표시는 픽토그램 위에만 올린다.
ACCENT 는 '채택되는 설명' 한 곳에만 쓴다 (바이블 §1).
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "scripts"))
from lib_style import *  # noqa: F403


class S03Scene(DiagramScene):
    DURATION = 4.05  # timing.json 과 일치
    DRIFT = 0.004    # 씬 내내 아주 느린 줌인

    def build(self):
        head = title_block("뉴욕의 상업 패권을 가른 진짜 원인")

        # --- 통념 (단순히 우수한 자연 항만 조건) ---
        icon_wrong = pict_doc(DIM, height=1.35)
        wrong = card(
            VGroup(
                icon_wrong,
                txt("수심 깊고 결빙 적은\n천혜의 자연 항만 조건", size=FS_LEAD, color=DIM),
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
        x_mark = cross_out(icon_wrong, DIM, pad=-0.14)
        self.draw(x_mark, run_time=1.0)

        # --- 실제 역사적 결합 (배후지 독점 연결망) ---
        right = card(
            VGroup(
                pict_bulb(INK, height=1.35),
                txt("중서부 곡창지대와\n독점 연결된 내륙 수운망", size=FS_LEAD, color=INK),
                footnote("출처: P. Bernstein (2005) / R. Shaw (1990)"),
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
