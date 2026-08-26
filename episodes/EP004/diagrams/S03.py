"""
S03 — 픽토그램 대비 : 통념 부정 (정부 법률 강제 vs 철도 안전 계산)
나레이션: "정부가 국민을 통제하려고 법으로 시간을 강제한 것이 아닙니다."

색·폰트·크기·세이프에어리어는 scripts/lib_style.py (스타일 바이블) 에서만 가져온다.
X 표시는 픽토그램 위에만 올린다. 카드 전체에 그으면 라벨을 덮어 읽히지 않는다.
ACCENT 는 '채택되는 설명' 한 곳에만 쓴다 (바이블 §1).
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "scripts"))
from lib_style import *  # noqa: F403


class S03Scene(DiagramScene):
    DURATION = 4.64  # timing.json 과 일치

    def build(self):
        head = title_block("시간을 통일한 주체는?")
        doc = pict_doc(DIM, height=1.35)
        wrong = card(
            VGroup(doc, txt("정부의 법률 강제", size=FS_LEAD, color=DIM))
            .arrange(RIGHT, buff=0.5),
            width=7.8, color=MUTE, pad_y=0.65,
        )
        wrong.move_to(UP * 4.3)
        guard(wrong, "wrong-card")

        self.play(
            AnimationGroup(
                FadeIn(head, shift=DOWN * 0.25),
                FadeIn(wrong, shift=RIGHT * 0.25),
                lag_ratio=0.25,
            ),
            run_time=1.3,
        )

        # 픽토그램 위에만 X 표시
        x_mark = cross_out(doc, DIM, pad=-0.14)
        self.draw(x_mark, run_time=1.2)

        # --- 대비 연결어 & 채택되는 설명 ---
        conj = txt("가 아니라", size=FS_CAPTION, color=DIM, bold=False)
        conj.move_to(UP * 2.1)

        right = card(
            VGroup(
                pict_gear(INK, height=1.5),
                txt("철도 회사의\n충돌 방지 계산", size=FS_LEAD, color=INK),
            ).arrange(RIGHT, buff=0.5),
            width=7.8, accent=True, pad_y=0.75,
        )
        right.move_to(DOWN * 0.3)
        guard(right, "right-card")

        no_overlap((wrong, "wrong-card"), (conj, "가 아니라"), (right, "right-card"))

        self.reveal(conj, right, run_time=1.3, shift=UP * 0.25)
