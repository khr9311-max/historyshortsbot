"""
S03 — 픽토그램 대비 : 개인의 천재성 vs 구조적 조건
나레이션: "천재가 나타나서도, 운이 좋아서도 아닙니다. 조건이 먼저였습니다."

색·폰트·크기·세이프에어리어는 scripts/lib_style.py (스타일 바이블) 에서만 가져온다.
X 표시는 픽토그램 위에만 올린다. 카드 전체에 그으면 라벨을 덮어 읽히지 않는다.
ACCENT 는 '채택되는 설명' 한 곳에만 쓴다 (바이블 §1).
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "scripts"))
from lib_style import *  # noqa: F403


class S03Scene(DiagramScene):
    DURATION = 6.76  # scenes.tsv 와 일치. 어긋나면 렌더 시 에러.

    def build(self):
        head = title_block("무엇이 먼저였나")
        self.reveal(head, run_time=1.2, shift=DOWN * 0.25)
        self.beat(0.25)

        # --- 기각되는 설명: 개인의 천재성 ---
        bulb = pict_bulb(DIM, height=1.45)
        wrong = card(
            VGroup(bulb, txt("개인의 천재성", size=FS_LEAD, color=DIM))
            .arrange(RIGHT, buff=0.6),
            width=7.8, color=MUTE, pad_y=0.72,
        )
        wrong.move_to(UP * 4.3)
        guard(wrong, "wrong-card")
        self.reveal(wrong, run_time=1.3, shift=RIGHT * 0.25)

        # 픽토그램 위에만 — 라벨은 계속 읽혀야 한다
        x_mark = cross_out(bulb, DIM, pad=-0.16)
        self.draw(x_mark, run_time=1.2)
        self.beat(0.2)

        # --- 대비 연결어 ---
        conj = txt("가 아니라", size=FS_CAPTION, color=DIM, bold=False)
        conj.move_to(UP * 2.05)

        # --- 채택되는 설명: 구조적 조건 (화면의 유일한 ACCENT) ---
        right = card(
            VGroup(
                pict_gear(INK, height=1.6),
                txt("구조가 만든\n비용 · 제도 조건", size=FS_LEAD, color=INK),
            ).arrange(RIGHT, buff=0.6),
            width=7.8, accent=True, pad_y=0.8,
        )
        right.move_to(DOWN * 0.35)
        guard(right, "right-card")

        no_overlap((wrong, "wrong-card"), (conj, "가 아니라"), (right, "right-card"))

        self.reveal(conj, right, run_time=1.5, shift=UP * 0.25)
        # 남는 시간은 _settle 이 마지막 프레임 유지로 채운다 (정지 ≥0.8초)
