"""
S04 — 인과 화살표 : 두 조건의 수렴
나레이션: "다단계 무역로와 중세 의학, 두 조건이 가격을 밀어 올렸습니다."

바이블 §8: 단일 원인 설명 금지.
'조건 1 + 조건 2 → 결과' 형태로만 결론을 낸다.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "scripts"))
from lib_style import *  # noqa: F403


class S04Scene(DiagramScene):
    DURATION = 5.42

    def build(self):
        label = tag("결정적 조건은 둘", SUB)
        label.move_to(UP * (SAFE_T - label.height / 2))

        def condition(no: str, name: str, detail: str, icon):
            return card(
                VGroup(
                    icon,
                    VGroup(
                        tag(no, SUB),
                        txt(name, size=FS_LEAD, color=INK),
                        txt(detail, size=FS_CAPTION, color=DIM, bold=False),
                    ).arrange(DOWN, buff=0.12, aligned_edge=LEFT),
                ).arrange(RIGHT, buff=0.5),
                width=7.8, pad_y=0.44,
            )

        c1 = condition("조건 1", "공급 구조", "다단계 독점 중개 무역로",
                       pict_doc(INK, height=1.15, seal=SUB))
        c2 = condition("조건 2", "수요 구조", "사체액설 의약품 & 신분 과시재",
                       pict_bulb(INK, height=1.15))

        c1.move_to(UP * 4.9)
        c2.move_to(UP * 1.9)
        plus = txt("+", size=FS_TITLE, color=DIM).move_to(UP * 3.4)

        for m, n in ((c1, "cond-1"), (c2, "cond-2"), (plus, "plus")):
            guard(m, n)

        self.play(
            AnimationGroup(
                FadeIn(label, shift=DOWN * 0.2),
                FadeIn(c1, shift=RIGHT * 0.3),
                FadeIn(plus),
                FadeIn(c2, shift=RIGHT * 0.3),
                lag_ratio=0.3,
            ),
            run_time=1.5,
        )

        # --- 수렴 → 결과 ---
        result = card(
            txt("산지 대비 60배 이상의 가격 폭등", size=FS_LEAD, color=ACCENT),
            width=7.6, accent=True, pad_y=0.40,
        )
        result.move_to(DOWN * 1.5)
        guard(result, "result")

        arrow = Arrow(
            start=c2.get_bottom() + DOWN * 0.12,
            end=result.get_top() + UP * 0.12,
            color=ACCENT, stroke_width=6, buff=0.06,
            max_tip_length_to_length_ratio=0.34,
        )

        no_overlap((c1, "cond-1"), (c2, "cond-2"), (result, "result"))

        self.play(GrowArrow(arrow), FadeIn(result, shift=UP * 0.25), run_time=1.4)
