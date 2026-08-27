"""
S10 — 인과 수렴 요약 + 루프백 (마지막 컷)
나레이션: "결국 강군을 무너뜨린 건 적의 무기가 아니라, 500킬로미터 보급선의 물리적 한계였습니다."

색·폰트·크기·세이프에어리어는 scripts/lib_style.py (스타일 바이블) 에서만 가져온다.
마지막 컷은 LOOP_TAIL 로 배경색 수렴 → 반복 재생 이음매를 지운다.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "scripts"))
from lib_style import *  # noqa: F403


class S10Scene(DiagramScene):
    DURATION = 7.64  # timing.json 과 일치
    LOOP_TAIL = 1.25  # 끝 프레임을 BG 로 수렴 → 반복 재생 이음매 제거
    DRIFT = 0.003

    def build(self):
        head = title_block("결론 : 60만 대군을 무너뜨린 인과 구조")

        # --- 상단: 2대 결합 요인 ---
        c_top = card(
            VGroup(
                tag("2대 결합 조건 (병참 한계 + 청야전술)", color=SUB),
                txt("500km 초과로 짐칸 식량 자체 소진\n+ 러시아군의 소각으로 현지 조달 차단", size=FS_BODY, color=DIM),
            ).arrange(DOWN, buff=0.16),
            width=7.8,
            color=MUTE,
            pad_y=0.38,
        )
        c_top.move_to(UP * 4.4)
        guard(c_top, "c_top")

        # --- 하단: 역사적 결론 ---
        c_bot = card(
            VGroup(
                tag("전쟁의 구조적 법칙", color=ACCENT),
                txt("적의 무기나 동장군이 아닌\n'보급선의 물리적 한계'가 승패 결정", size=FS_BODY, color=INK),
                footnote("출처: M. van Creveld (1977) / D. Chandler (1966)"),
            ).arrange(DOWN, buff=0.16),
            width=7.8,
            accent=True,
            pad_y=0.42,
        )
        c_bot.move_to(DOWN * 2.2)
        guard(c_bot, "c_bot")

        # 인과 화살표
        link = Arrow(
            c_top.get_bottom() + DOWN * 0.12,
            c_bot.get_top() + UP * 0.12,
            color=MUTE,
            stroke_width=4,
            buff=0.0,
            max_tip_length_to_length_ratio=0.10,
        )
        link_txt = txt("보급망 마비", size=FS_CAPTION, color=DIM, bold=False, outline=True)
        link_txt.move_to(link.get_center() + RIGHT * 1.6)

        no_overlap((c_top, "c_top"), (link_txt, "보급망 마비"), (c_bot, "c_bot"))

        self.play(
            AnimationGroup(
                FadeIn(head, shift=DOWN * 0.25),
                FadeIn(c_top, shift=RIGHT * 0.25),
                lag_ratio=0.20,
            ),
            run_time=1.4,
        )
        self.beat(0.4)

        self.reveal(link, link_txt, c_bot, run_time=1.5, shift=UP * 0.20)
        self.pulse(c_bot, times=1, scale=1.03, run_time=0.4)
        self.beat(0.8)
