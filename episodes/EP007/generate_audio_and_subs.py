"""
EP007 — 나레이션 · 자막 · 컷 길이 생성

대본은 이 파일이 아니라 **scenes.json** 에 있다 (단일 권원).
처리는 scripts/lib_narration.py 가 한다.

    python episodes/EP007/generate_audio_and_subs.py
    → assets/vo/vo.wav · sub.ass · scenes.tsv · timing.json
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "scripts"))
from lib_narration import generate_from_scenes  # noqa: E402

if __name__ == "__main__":
    generate_from_scenes("EP007")
