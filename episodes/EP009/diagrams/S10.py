"""
S10 — 인과 수렴 요약 + 루프백 (마지막 컷)
나레이션: "결국 국가의 수명을 가른 건 세율의 크기가 아니라, 중간 누수를 막고 신용을 지켜낸 세금 징수 방식이었습니다."

색·폰트·크기·세이프에어리어는 scripts/lib_style.py (스타일 바이블) 에서만 가져온다.
마지막 컷은 LOOP_TAIL 로 배경색 수렴 → 반복 재생 이음매를 지운다.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "scripts"))
from lib_style import *  # noqa: F403


class S10Scene(DiagramScene):
    DURATION = 9.07  # timing.json 과 일치
    LOOP_TAIL = 1.25  # 끝 프레임을 BG 로 수렴 → 반복 재생 이음매 제거
    DRIFT = 0.003

    def build(self):
        head = title_block("결론 : 국가 수명을 결정한 인과 구조")

        # --- 실패 경로 (프랑스식 징세 청부) ---
        c_fail = card(
            VGroup(
                tag("징세권 민간 외주 (청부제)", color=SUB),
                txt("가혹한 중간 착복 + 국고 세수 누수\n→ 국가 신용 붕괴 & 고금리 파산", size=FS_BODY, color=DIM),
            ).arrange(DOWN, buff=0.16),
            width=7.8,
            color=MUTE,
            pad_y=0.38,
        )
        c_fail.move_to(UP * 4.4)
        guard(c_fail, "c_fail")

        # --- 성공 경로 (영국식 직접 징수) ---
        c_succ = card(
            VGroup(
                tag("중앙 관료 직접 징수", color=ACCENT),
                txt("누수 없는 투명한 국고 유입\n→ 초저금리 국채 발행 & 장기 존속", size=FS_BODY, color=INK),
                footnote("출처: D. North & B. Weingast (1989) / J. Brewer (1989)"),
            ).arrange(DOWN, buff=0.16),
            width=7.8,
            accent=True,
            pad_y=0.42,
        )
        c_succ.move_to(DOWN * 2.3)
        guard(c_succ, "c_succ")

        # 인과 화살표
        link = Arrow(
            c_fail.get_bottom() + DOWN * 0.12,
            c_succ.get_top() + UP * 0.12,
            color=MUTE,
            stroke_width=4,
            buff=0.0,
            max_tip_length_to_length_ratio=0.10,
        )
        link_txt = txt("제도적 분기점", size=FS_CAPTION, color=DIM, bold=False, outline=True)
        link_txt.move_to(link.get_center() + RIGHT * 1.8)

        no_overlap((c_fail, "c_fail"), (link_txt, "제도적 분기점"), (c_succ, "c_succ"))

        self.play(
            AnimationGroup(
                FadeIn(head, shift=DOWN * 0.25),
                FadeIn(c_fail, shift=RIGHT * 0.25),
                lag_ratio=0.20,
            ),
            run_time=1.5,
        )
        self.beat(0.8)

        self.reveal(link, link_txt, c_succ, run_time=1.6, shift=UP * 0.20)
        self.pulse(c_succ, times=1, scale=1.03, run_time=0.5)
        self.beat(1.2)
