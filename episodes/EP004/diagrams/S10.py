"""
S10 — 인과 요약 + 루프백 (마지막 컷)
나레이션: "세상의 시계를 하나로 맞춘 건 하늘의 해가 아니라, 선로 위를 달리는 기차였습니다."

쇼츠는 자동 반복된다. 그래서 이 컷은 '끝'이 아니라 '이음매'다.
  1) 마지막 문장이 곧 S01 의 훅("19세기 이전엔, 도시마다 낮 12시가 달랐습니다")과
     이어지도록 써서, 반복 재생이 한 문단처럼 읽히게 한다.
  2) LOOP_TAIL 동안 모든 요소를 배경색으로 수렴시켜 끝 프레임을 순수 BG 로 만든다.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "scripts"))
from lib_style import *  # noqa: F403


class S10Scene(DiagramScene):
    DURATION = 6.93
    LOOP_TAIL = 1.25  # 배경색 수렴 구간

    def build(self):
        head = title_block("오늘의 인과")
        self.reveal(head, run_time=1.2, shift=DOWN * 0.25)

        # --- 한 줄 공식 (화면의 유일한 ACCENT) ---
        formula = card(
            txt("고속 단선 철도   +   전신망 동기화", size=FS_BODY, color=INK),
            down_arrow(ACCENT, 0.6),
            txt("1883년 4대 표준시간대 탄생", size=FS_LEAD, color=ACCENT),
            width=7.8, accent=True, pad_y=0.42, gap=0.15,
        )
        formula.move_to(UP * 3.8)
        guard(formula, "formula")
        self.reveal(formula, run_time=1.3, shift=UP * 0.2)

        # --- 루프백 명제: 다음 재생의 훅으로 넘겨준다 ---
        div = rule(6.8).move_to(UP * 1.1)
        prop = txt(
            "시계를 맞춘 것은\n자연의 태양이 아니라\n기계의 속도였다",
            size=FS_LEAD, color=INK, line_spacing=1.0,
        )
        prop.move_to(DOWN * 0.7)

        # 학설/법제화 선후관계 각주
        note = footnote("※ 1883년 철도 표준시 도입 → 1918년 연방 표준시간법 제정")
        note.move_to(DOWN * 2.7)

        guard(VGroup(div, prop), "proposition")
        guard(note, "note")
        no_overlap((formula, "formula"), (prop, "proposition"), (note, "note"))

        self.reveal(div, prop, note, run_time=1.4, shift=UP * 0.2)
        self.beat(0.4)
        # 이후 _settle 이 LOOP_TAIL(1.25s) 동안 BG 로 수렴시킨다
