"""
S03 — 픽토그램 대비 : 통념 부정 (화약 발명 vs 총기 체계 직행 ✕)
나레이션: "중국은 이미 10세기에 화약을 무기로 썼지만, 서양처럼 총으로 직행하지 않았습니다."

색·폰트·크기·세이프에어리어는 scripts/lib_style.py (스타일 바이블) 에서만 가져온다.
X 표시는 픽토그램 위에만 올린다.
ACCENT 는 '채택되는 설명' 한 곳에만 쓴다 (바이블 §1).
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "scripts"))
from lib_style import *  # noqa: F403


class S03Scene(DiagramScene):
    DURATION = 6.19  # timing.json 과 일치
    DRIFT = 0.004    # 씬 내내 아주 느린 줌인

    def build(self):
        head = title_block("화약 발명 이후의 무기 경로")

        # --- 통념 (총기로의 즉시 발전) ---
        doc = pict_doc(DIM, height=1.35)
        wrong = card(
            VGroup(
                doc,
                txt("화약 발명 직후\n개인 총기 체계로 직행", size=FS_LEAD, color=DIM),
            ).arrange(RIGHT, buff=0.4),
            width=7.8,
            color=MUTE,
            pad_y=0.55,
        )
        wrong.move_to(UP * 4.2)
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

        # --- 연결어 & 실제 역사적 선택 ---
        conj = txt("이 아니라", size=FS_CAPTION, color=DIM, bold=False)
        conj.move_to(UP * 2.1)

        right = card(
            VGroup(
                pict_bulb(INK, height=1.4),
                txt("기병 대응 & 공성 중심의\n화차·포병 무기 발전", size=FS_LEAD, color=INK),
                footnote("출처: J. Needham (1986) / T. Andrade (2016)"),
            ).arrange(DOWN, buff=0.2),
            width=7.8,
            accent=True,
            pad_y=0.6,
        )
        right.move_to(DOWN * 0.4)
        guard(right, "right-card")

        no_overlap((wrong, "wrong-card"), (conj, "이 아니라"), (right, "right-card"))

        self.reveal(conj, right, run_time=1.3, shift=UP * 0.25)
        self.pulse(right, times=1, scale=1.03, run_time=0.4)
