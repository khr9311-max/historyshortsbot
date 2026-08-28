"""
S03 — 픽토그램 대비 : 통념 부정 (대포로 인한 성벽 몰락 vs 성형 요새로의 진화)
나레이션: "대포를 막는 '별모양 요새'로 진화했죠."

색·폰트·크기·세이프에어리어는 scripts/lib_style.py 에서만 가져온다.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "scripts"))
from lib_style import *  # noqa: F403


class S03Scene(DiagramScene):
    DURATION = 3.13  # timing.json 과 일치
    DRIFT = 0.004

    def build(self):
        head = title_block("대포 등장 이후 성벽의 진화")

        # --- 1. 통념 (1453년 대포 등장) ---
        icon_wrong = pict_doc(DIM, height=1.2)
        wrong = card(
            VGroup(
                icon_wrong,
                VGroup(
                    txt("1453년 대포 등장", size=FS_CAPTION, color=DIM),
                    txt("높은 성벽의 시대 종말?", size=FS_LEAD, color=DIM),
                ).arrange(DOWN, buff=0.12, aligned_edge=LEFT),
            ).arrange(RIGHT, buff=0.35),
            width=7.8,
            color=MUTE,
            pad_y=0.45,
        )
        wrong.move_to(UP * 4.3)
        guard(wrong, "wrong-card")

        # --- 2. 실제 역사 (성형 요새의 등장) ---
        right = card(
            tag("16세기 군사 혁명", color=SUB),
            VGroup(
                pict_bulb(INK, height=1.2),
                VGroup(
                    txt("낮고 두꺼운 '성형 요새'", size=FS_LEAD, color=INK),
                    txt("대포 튕겨내며 200년 방어 우위", size=FS_CAPTION, color=INK, bold=False),
                ).arrange(DOWN, buff=0.12, aligned_edge=LEFT),
            ).arrange(RIGHT, buff=0.35),
            footnote("출처: Geoffrey Parker (1988)"),
            width=7.8,
            accent=True,
            pad_y=0.45,
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
        conj = txt("오히려 진화", size=FS_CAPTION, color=SUB, bold=True, outline=True)
        conj.move_to(link.get_center() + RIGHT * 1.5)

        x_mark = cross_out(icon_wrong, DIM, pad=-0.14)

        no_overlap((wrong, "wrong-card"), (conj, "오히려 진화"), (right, "right-card"))

        # 애니메이션 타이밍: 1.1s + 1.2s + 0.3s = 2.6s (< 3.13s)
        self.play(
            AnimationGroup(
                FadeIn(head, shift=DOWN * 0.25),
                FadeIn(wrong, shift=RIGHT * 0.25),
                Create(x_mark),
                lag_ratio=0.25,
            ),
            run_time=1.1,
        )

        self.play(
            AnimationGroup(
                Create(link),
                FadeIn(conj, shift=UP * 0.15),
                FadeIn(right, shift=UP * 0.20),
                lag_ratio=0.20,
            ),
            run_time=1.2,
        )
        self.pulse(right, times=1, scale=1.03, run_time=0.3)
