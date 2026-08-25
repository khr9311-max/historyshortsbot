"""
S09 — 요약 + 루프백 (마지막 컷)
나레이션: "그래서 향신료가 비쌌던 진짜 이유는, 맛이 아니라 독점과 신분이었습니다."

바이블 §7: 마지막 컷은 diagram 요약 패턴으로 닫는다.
바이블 §11: 루프백 — 끝 프레임을 BG(배경색)로 수렴시켜 S01의 BG 페이드인과 이음매 없이 연결.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "scripts"))
from lib_style import *  # noqa: F403


class S09Scene(DiagramScene):
    DURATION = 6.86  # scenes.tsv 와 일치
    LOOP_TAIL = 1.25  # 끝 프레임을 BG 로 수렴 → 반복 재생 이음매 제거

    def build(self):
        head = title_block("향신료 폭등의 인과 법칙", "역사는 다인과다")

        # --- 인과 종합 카드 2단 ---
        top_card = card(
            tag("두 조건의 결합", SUB),
            txt("다단계 독점 공급망\n+ 사체액설·신분 과시 수요", size=FS_LEAD, color=INK),
            width=7.8,
            pad_y=0.45,
        )
        top_card.move_to(UP * 3.4)

        arrow = down_arrow(color=ACCENT, length=0.85)
        arrow.move_to(UP * 1.5)

        bot_card = card(
            tag("역사적 결과", ACCENT),
            txt("향신료의 화폐화\n& 대항해시대 항로 개척 유인", size=FS_LEAD, color=ACCENT),
            width=7.8,
            accent=True,
            pad_y=0.55,
        )
        bot_card.move_to(DOWN * 0.5)

        note = footnote("지배학설: 프리드먼(2008) · 터너(2004) / 보완설: 무역로 독점론(브로델 1992)")
        note.move_to(DOWN * 2.8)

        for m, n in (
            (top_card, "top_card"),
            (arrow, "arrow"),
            (bot_card, "bot_card"),
            (note, "note"),
        ):
            guard(m, n)

        no_overlap(
            (head, "title"),
            (top_card, "top_card"),
            (arrow, "arrow"),
            (bot_card, "bot_card"),
            (note, "note"),
        )

        self.reveal(head, top_card, run_time=1.4, shift=DOWN * 0.2)
        self.play(GrowArrow(arrow), FadeIn(bot_card, shift=UP * 0.2), run_time=1.5)
        self.reveal(note, run_time=1.2)
        self.beat(0.8)
