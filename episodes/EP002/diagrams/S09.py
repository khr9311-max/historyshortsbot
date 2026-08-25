"""
S09 — 인과 요약 + 루프백 (마지막 컷)
나레이션: "그래서 전 세계 은을 가졌던 제국이, 가장 처참하게 무너졌습니다."

쇼츠는 자동 반복된다. 그래서 이 컷은 '끝'이 아니라 '이음매'다.

  1) 마지막 문장이 곧 S01 의 훅("전 세계 은의 3분의 1을 빨아들였던 제국이,
     은 때문에 파산했습니다")과 이어지도록 써서 반복 재생이 한 문맥으로 물린다.
  2) LOOP_TAIL 동안 모든 요소를 배경색으로 수렴시켜 끝 프레임을 순수 BG 로 만든다.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "scripts"))
from lib_style import *  # noqa: F403


class S09Scene(DiagramScene):
    DURATION = 6.14
    LOOP_TAIL = 1.25  # 배경색 수렴 구간

    def build(self):
        head = title_block("오늘의 인과")
        self.reveal(head, run_time=1.2, shift=DOWN * 0.25)

        # --- 한 줄 공식 ---
        formula = card(
            txt("조세 은납화   +   외부 통화 의존", size=FS_LEAD, color=INK),
            down_arrow(ACCENT, 0.7),
            txt("공급망 충격 시 디플레이션 파산", size=FS_LEAD, color=ACCENT),
            width=7.8, accent=True, pad_y=0.48, gap=0.18,
        )
        formula.move_to(UP * 3.9)
        guard(formula, "formula")
        self.reveal(formula, run_time=1.4, shift=UP * 0.2)

        # --- 루프백 명제: 다음 재생의 훅으로 넘겨준다 ---
        div = rule(6.8).move_to(UP * 1.1)
        prop = txt(
            "통화 통제력을 잃은 제국은\n돈이 들어올 때가 아니라\n끊길 때 무너진다",
            size=FS_LEAD, color=INK, line_spacing=1.0,
        )
        prop.move_to(DOWN * 0.7)

        # 학설 구분 명시 — 바이블 §8
        note = footnote("※ 보완설 — 보겔 · 골드스톤:\n국내 화폐 유통 불균형과 전비 부담을 강조")
        note.move_to(DOWN * 2.9)

        guard(VGroup(div, prop), "proposition")
        guard(note, "note")
        no_overlap((formula, "formula"), (prop, "proposition"), (note, "note"))
        self.reveal(div, prop, note, run_time=1.4, shift=UP * 0.2)

        self.beat(0.4)
