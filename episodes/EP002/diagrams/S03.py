"""
S03 — 픽토그램 대비 : 은의 대량 유입(상식) vs 국고 파산 및 반란(현실)
나레이션: "돈이 넘치는데 국고는 비었고, 반란이 터졌습니다. 왜였을까요?"

색·폰트·크기·세이프에어리어는 scripts/lib_style.py (스타일 바이블) 에서만 가져온다.
X 표시는 픽토그램 위에만 올린다. 카드 전체에 그으면 라벨을 덮어 읽히지 않는다.
ACCENT 는 '실제 발생한 현실' 한 곳에만 쓴다 (바이블 §1).
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "scripts"))
from lib_style import *  # noqa: F403


class S03Scene(DiagramScene):
    DURATION = 6.73  # scenes.tsv 와 일치

    def build(self):
        head = title_block("상식과 다른 현실")
        self.reveal(head, run_time=1.2, shift=DOWN * 0.25)
        self.beat(0.25)

        # --- 기각되는 상식: 은 유입 = 부국강병 ---
        coin = pict_coin(DIM, height=1.45)
        wrong = card(
            VGroup(coin, txt("은 대량 유입\n제국의 번영", size=FS_LEAD, color=DIM))
            .arrange(RIGHT, buff=0.6),
            width=7.8, color=MUTE, pad_y=0.72,
        )
        wrong.move_to(UP * 4.3)
        guard(wrong, "wrong-card")
        self.reveal(wrong, run_time=1.3, shift=RIGHT * 0.25)

        # 픽토그램 위에만 X 표시 — 라벨은 계속 읽혀야 한다
        x_mark = cross_out(coin, DIM, pad=-0.16)
        self.draw(x_mark, run_time=1.2)
        self.beat(0.2)

        # --- 대비 연결어 ---
        conj = txt("가 아니라", size=FS_CAPTION, color=DIM, bold=False)
        conj.move_to(UP * 2.05)

        # --- 실제 발생한 현실: 국고 고갈 + 반란 (화면의 유일한 ACCENT) ---
        person = pict_person(INK, height=1.55)
        right = card(
            VGroup(
                person,
                txt("국고 파산과\n농민 반란의 폭발", size=FS_LEAD, color=INK),
            ).arrange(RIGHT, buff=0.6),
            width=7.8, accent=True, pad_y=0.8,
        )
        right.move_to(DOWN * 0.35)
        guard(right, "right-card")

        no_overlap((wrong, "wrong-card"), (conj, "가 아니라"), (right, "right-card"))

        self.reveal(conj, right, run_time=1.5, shift=UP * 0.25)
