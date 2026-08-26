"""
S10 — 인과 요약 + 루프백 (마지막 컷)
나레이션: "산업혁명의 배를 불린 건 화려한 밀밭이 아니라, 땅속에 숨죽여 있던 감자였습니다."

색·폰트·크기·세이프에어리어는 scripts/lib_style.py (스타일 바이블) 에서만 가져온다.
마지막 프레임은 LOOP_TAIL 에 의해 BG 색으로 수렴된다 (루프백 이음매 제거).
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "scripts"))
from lib_style import *  # noqa: F403


class S10Scene(DiagramScene):
    DURATION = 7.00   # timing.json 과 일치
    LOOP_TAIL = 1.25  # 끝 프레임을 BG 로 수렴 → 반복 재생 이음매 제거 (바이블 §11)
    DRIFT = 0.004     # 씬 내내 아주 느린 줌인

    def build(self):
        head = title_block("산업혁명의 진짜 동력")

        # --- 상단: 통념 (밀밭) ---
        wrong = card(
            VGroup(
                txt("지상의 화려한 밀밭", size=FS_BODY, color=DIM),
            ),
            width=7.8, color=MUTE, pad_y=0.45,
        )
        wrong.move_to(UP * 4.2)
        guard(wrong, "wrong-card")

        self.play(
            AnimationGroup(
                FadeIn(head, shift=DOWN * 0.25),
                FadeIn(wrong, shift=RIGHT * 0.25),
                lag_ratio=0.25,
            ),
            run_time=1.3,
        )

        x_mark = cross_out(wrong, DIM, pad=0.08)
        self.draw(x_mark, run_time=1.2)

        # --- 연결어 ---
        conj = txt("이 아니라", size=FS_CAPTION, color=DIM, bold=False)
        conj.move_to(UP * 2.5)

        # --- 하단: 핵심 인과 (감자) ---
        right = card(
            VGroup(
                pict_factory(INK, height=1.3),
                txt("땅속에 숨겨진 감자", size=FS_LEAD, color=INK),
                txt("유럽 인구 25% 견인 · 도시 노동력 공급", size=FS_CAPTION, color=ACCENT),
            ).arrange(DOWN, buff=0.22),
            width=7.8, accent=True, pad_y=0.55,
        )
        right.move_to(DOWN * 0.3)
        guard(right, "right-card")

        no_overlap((wrong, "wrong-card"), (conj, "이 아니라"), (right, "right-card"))

        self.reveal(conj, right, run_time=1.3, shift=UP * 0.25)
        self.pulse(right, times=2, scale=1.04, run_time=0.5)
