"""
S10 — 조사 보드 인과선 : 성벽 무력화의 핵심 인과 및 결론
나레이션: "대포가 아니라 기동전이었죠 바로"

인과 구조:
천문학적 축성 비용 + 20만 군대의 기동전(요새 우회) → 고정 성벽의 무의미화 (야전군 중심 방어)
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "scripts"))
from lib_style import *  # noqa: F403


class S10Scene(DiagramScene):
    DURATION = 3.76  # timing.json 과 일치
    LOOP_TAIL = 1.25  # 끝 프레임을 BG 로 수렴 → 반복 재생 이음매 제거
    DRIFT = 0.003

    def build(self):
        head = title_block("성벽이 무의미해진 진짜 인과 구조")

        # --- 상단: 두 가지 원인 조건 ---
        cause_a = card(
            VGroup(
                pict_coin(INK, height=1.0),
                txt("천문학적 축성 비용\n(국가 재정 고갈)", size=FS_BODY, color=INK),
            ).arrange(RIGHT, buff=0.25),
            width=3.8,
            color=MUTE,
            pad_y=0.35,
        )
        cause_b = card(
            VGroup(
                pict_gear(INK, height=1.0),
                txt("20만 대군의 기동전\n(거점 요새 우회)", size=FS_BODY, color=INK),
            ).arrange(RIGHT, buff=0.25),
            width=3.8,
            color=MUTE,
            pad_y=0.35,
        )
        causes = VGroup(cause_a, cause_b).arrange(RIGHT, buff=0.25)
        causes.move_to(UP * 4.3)
        guard(causes, "causes")

        # --- 하단: 최종 역사적 귀결 ---
        result = card(
            tag("방어 패러다임 전환", color=SUB),
            VGroup(
                pict_bulb(INK, height=1.2),
                VGroup(
                    txt("고정 성벽의 무의미화", size=FS_LEAD, color=INK),
                    txt("돌벽에서 '국경 야전군' 중심으로 이동", size=FS_BODY, color=INK, bold=False),
                ).arrange(DOWN, buff=0.12, aligned_edge=LEFT),
            ).arrange(RIGHT, buff=0.35),
            source_stamp("Geoffrey Parker, The Military Revolution"),
            width=7.8,
            accent=True,
            pad_y=0.45,
        )
        result.move_to(DOWN * 2.3)
        guard(result, "result")

        # --- 원인에서 결과로 모이는 화살표 ---
        arrow_a = Arrow(
            cause_a.get_bottom() + DOWN * 0.1,
            result.get_top() + UP * 0.1 + LEFT * 1.5,
            color=SUB,
            stroke_width=4,
            buff=0.0,
            max_tip_length_to_length_ratio=0.12,
        )
        arrow_b = Arrow(
            cause_b.get_bottom() + DOWN * 0.1,
            result.get_top() + UP * 0.1 + RIGHT * 1.5,
            color=SUB,
            stroke_width=4,
            buff=0.0,
            max_tip_length_to_length_ratio=0.12,
        )
        arrows = VGroup(arrow_a, arrow_b)

        no_overlap((causes, "causes"), (result, "result"))

        # 애니메이션 타이밍: 0.9s + 1.0s + 0.3s = 2.2s (DURATION 3.76 - LOOP_TAIL 1.25 = 2.51s 이내)
        self.play(
            AnimationGroup(
                FadeIn(head, shift=DOWN * 0.25),
                FadeIn(causes, shift=DOWN * 0.20),
                lag_ratio=0.25,
            ),
            run_time=0.9,
        )

        self.play(
            AnimationGroup(
                Create(arrows),
                FadeIn(result, shift=UP * 0.20),
                lag_ratio=0.20,
            ),
            run_time=1.0,
        )
        self.pulse(result, times=1, scale=1.03, run_time=0.3)
