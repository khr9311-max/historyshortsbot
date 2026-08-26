"""
S04 — 수치/무기 비교 : 유목 기병 상대 연사 속도 비교 (각궁 vs 초기 총기)
나레이션: "초원의 유목 기병을 상대하기엔, 재장전이 느린 총보다 연사력이 빠른 활이 훨씬 치명적이었거든요."

색·폰트·크기·세이프에어리어는 scripts/lib_style.py (스타일 바이블) 에서만 가져온다.
숫자는 크게, 단독으로 (FS_NUM).
ACCENT 는 핵심 수치 한 곳에만 쓴다.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "scripts"))
from lib_style import *  # noqa: F403


class S04Scene(DiagramScene):
    DURATION = 7.29  # timing.json 과 일치
    DRIFT = 0.004    # 씬 내내 아주 느린 줌인

    def build(self):
        head = title_block("유목 기병 상대 1분당 발사 속도", sub_text="초기 화기 도입기 무기 효율성 비교")

        # --- 초기 총기 카드 (1발/분) ---
        gun_card = card(
            VGroup(
                txt("초기 총기 (화승총·총통)", size=FS_BODY, color=DIM),
                txt("분당 1발 이하", size=FS_NUM, color=DIM),
                txt("긴 재장전 시간 → 돌격 기병에 취약", size=FS_CAPTION, color=DIM),
            ).arrange(DOWN, buff=0.18),
            width=7.8,
            color=MUTE,
            pad_y=0.45,
        )
        gun_card.move_to(UP * 3.8)
        guard(gun_card, "gun-card")

        # --- 전통 각궁/복합궁 카드 (8발/분 강조) ---
        bow_card = card(
            VGroup(
                tag("기동 기병 요격의 핵심", color=SUB),
                txt("전통 각궁·복합궁", size=FS_LEAD, color=INK),
                txt("분당 8~10발", size=FS_NUM, color=ACCENT),
                footnote("출처: T. Andrade (2016) / P. Lorge (2008)"),
            ).arrange(DOWN, buff=0.18),
            width=7.8,
            accent=True,
            pad_y=0.5,
        )
        bow_card.move_to(DOWN * 0.9)
        guard(bow_card, "bow-card")

        no_overlap((gun_card, "gun-card"), (bow_card, "bow-card"))

        self.play(
            AnimationGroup(
                FadeIn(head, shift=DOWN * 0.25),
                FadeIn(gun_card, shift=UP * 0.25),
                lag_ratio=0.2,
            ),
            run_time=1.3,
        )

        self.reveal(bow_card, run_time=1.4, shift=UP * 0.3)
        self.pulse(bow_card, times=2, scale=1.04, run_time=0.5)
