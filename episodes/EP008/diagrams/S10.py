"""
S10 — 인과 수렴 요약 + 루프백 (마지막 컷)
나레이션: "결국 도시의 패권을 가른 건 항구의 위치가 아니라, 광대한 배후지를 독점 연결한 수운 인프라였습니다."

인과 화살표 수렴 패턴: 모호크 지리 통로 + 584km 운하 인프라 → 95% 물류비 폭락 & 뉴욕 무역·금융 패권 독점
LOOP_TAIL 로 끝 프레임을 BG 로 수렴시켜 루프 이음매를 만든다.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "scripts"))
from lib_style import *  # noqa: F403


class S10Scene(DiagramScene):
    DURATION = 8.37   # timing.json 과 일치
    LOOP_TAIL = 1.25  # 끝 프레임을 BG 로 수렴 → 반복 재생 이음매 제거
    DRIFT = 0.004

    def build(self):
        head = title_block("뉴욕의 도시 패권을 가른 인과 사슬", "지리적 조건 · 운하 인프라 · 물류 독점의 결합")

        # --- 상단 2가지 조건 카드 ---
        c1 = card(
            tag("조건 1 · 지리적 조건", color=SUB),
            txt("애팔래치아 산맥의 유일한\n모호크 저고도 협곡 통로", size=FS_BODY, color=INK),
            width=3.75,
            color=MUTE,
            pad_y=0.35,
            gap=0.15,
        )
        c1.move_to(UP * 4.4 + LEFT * 2.05)
        guard(c1, "cond-1")

        c2 = card(
            tag("조건 2 · 인프라 혁신", color=SUB),
            txt("584km 이리 운하 개통\n& 운송비 95% 폭락", size=FS_BODY, color=INK),
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
            txt("중서부 내륙 자원 독점 흡수\n→ 뉴욕시 무역·금융 패권 장악", size=FS_LEAD, color=INK),
            footnote("출처: P. Bernstein (2005) / C. Sheriff (1996)"),
            width=7.8,
            accent=True,
            pad_y=0.55,
            gap=0.20,
        )
        res.move_to(DOWN * 2.5)
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
        self.reveal(c1, c2, run_time=1.3, shift=DOWN * 0.15)
        self.draw(arrows, run_time=1.1)
        self.reveal(res, run_time=1.3, shift=UP * 0.2)
        self.pulse(res, times=1, scale=1.03, run_time=0.4)
        self.beat(0.6)
