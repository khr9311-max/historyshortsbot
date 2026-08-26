"""
S10 — 인과 수렴 요약 + 루프백 (마지막 컷)
나레이션: "결국 교회를 쪼갠 건 교리만이 아니라, 대량 복제가 만든 상업적 유혹과 분권화된 도시들이었습니다."

인과 화살표 수렴 패턴: 복제비 급감/상업성 + 분권 자치도시 네트워크 → 여론 양극화 & 종교 전쟁
LOOP_TAIL 로 끝 프레임을 BG 로 수렴시켜 루프 이음매를 만든다.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "scripts"))
from lib_style import *  # noqa: F403


class S10Scene(DiagramScene):
    DURATION = 8.14   # timing.json 과 일치
    LOOP_TAIL = 1.25  # 끝 프레임을 BG 로 수렴 → 반복 재생 이음매 제거
    DRIFT = 0.004

    def build(self):
        head = title_block("종교 갈등으로 이어진 인과 사슬", "기술 · 상업 · 정치 분권의 결합")

        # --- 상단 2가지 조건 카드 ---
        c1 = card(
            tag("조건 1 · 시장 유혹", color=SUB),
            txt("정보 복제 비용 급감\n& 자극적 소책자 수익", size=FS_BODY, color=INK),
            width=3.75,
            color=MUTE,
            pad_y=0.35,
            gap=0.15,
        )
        c1.move_to(UP * 4.4 + LEFT * 2.05)
        guard(c1, "cond-1")

        c2 = card(
            tag("조건 2 · 정치 구조", color=SUB),
            txt("신성로마제국의 분권\n& 자치 도시 인쇄망", size=FS_BODY, color=INK),
            width=3.75,
            color=MUTE,
            pad_y=0.35,
            gap=0.15,
        )
        c2.move_to(UP * 4.4 + RIGHT * 2.05)
        guard(c2, "cond-2")

        # --- 하단 결과 카드 ---
        res = card(
            tag("역사적 귀결", color=ACCENT),
            txt("중앙 검열 무력화 및 여론 극단화\n→ 타협 없는 종교 전쟁으로 격화", size=FS_LEAD, color=INK),
            footnote("출처: E. Eisenstein (1979) / M. Edwards (1994)"),
            width=7.8,
            accent=True,
            pad_y=0.55,
            gap=0.20,
        )
        res.move_to(DOWN * 2.5)  # guard() 가 세이프 하단 경계까지 끌어올린다
        guard(res, "result-card")

        # --- 수렴 화살표 ---
        arrows = converge_arrows(c1, c2, res, color=ACCENT)

        no_overlap(
            (c1, "cond-1"),
            (c2, "cond-2"),
            (res, "result-card"),
        )

        # 애니메이션 시퀀스
        self.play(FadeIn(head, shift=DOWN * 0.25), run_time=1.2)
        self.reveal(c1, c2, run_time=1.4, shift=DOWN * 0.15)
        self.draw(arrows, run_time=1.2)
        self.reveal(res, run_time=1.4, shift=UP * 0.2)
        self.pulse(res, times=1, scale=1.03, run_time=0.4)
        self.beat(0.8)
