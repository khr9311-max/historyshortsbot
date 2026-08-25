"""
S03 — 픽토그램 대비 : 썩은 고기 방부용(상식) vs 귀족의 신선육 소비 및 신분 과시(현실)
나레이션: "신선한 고기를 먹던 귀족만 샀고, 가난한 사람은 구경도 못 했습니다."

색·폰트·크기·세이프에어리어는 scripts/lib_style.py (스타일 바이블) 에서만 가져온다.
X 표시는 픽토그램 위에만 올린다. 카드 전체에 그으면 라벨을 덮어 읽히지 않는다.
ACCENT 는 '실제 발생한 현실' 한 곳에만 쓴다 (바이블 §1).
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "scripts"))
from lib_style import *  # noqa: F403


class S03Scene(DiagramScene):
    DURATION = 5.66  # scenes.tsv 와 일치

    def build(self):
        head = title_block("상식과 다른 현실")
        self.reveal(head, run_time=1.2, shift=DOWN * 0.25)
        self.beat(0.20)

        # --- 기각되는 상식: 썩은 고기 냄새 제거/방부용 ---
        meat_icon = pict_doc(DIM, height=1.35)
        wrong = card(
            VGroup(
                meat_icon,
                txt("대중적 상식\n썩은 고기 냄새 방부용", size=FS_LEAD, color=DIM),
            ).arrange(RIGHT, buff=0.55),
            width=7.8, color=MUTE, pad_y=0.65,
        )
        wrong.move_to(UP * 4.3)
        guard(wrong, "wrong-card")
        self.reveal(wrong, run_time=1.2, shift=RIGHT * 0.25)

        # 픽토그램 위에만 X 표시 — 라벨은 계속 읽혀야 한다
        x_mark = cross_out(meat_icon, DIM, pad=-0.14)
        self.draw(x_mark, run_time=1.2)
        self.beat(0.15)

        # --- 대비 연결어 ---
        conj = txt("가 아니라", size=FS_CAPTION, color=DIM, bold=False)
        conj.move_to(UP * 2.05)

        # --- 실제 발생한 현실: 최상류층 귀족의 신선육 소비와 신분 과시 (ACCENT) ---
        noble = pict_person(INK, height=1.45)
        right = card(
            VGroup(
                noble,
                txt("상류층 귀족의\n신선육 소비와 신분 과시", size=FS_LEAD, color=INK),
            ).arrange(RIGHT, buff=0.55),
            width=7.8, accent=True, pad_y=0.75,
        )
        right.move_to(DOWN * 0.35)
        guard(right, "right-card")

        no_overlap((wrong, "wrong-card"), (conj, "가 아니라"), (right, "right-card"))

        self.reveal(conj, right, run_time=1.3, shift=UP * 0.25)
