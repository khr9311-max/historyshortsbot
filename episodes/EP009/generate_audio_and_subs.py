"""
EP009 — 나레이션 · 자막 · 컷 길이 생성

대본은 이 파일이 아니라 **scenes.json** 에 있다 (단일 권원).
처리는 scripts/lib_narration.py 가 한다.

    python episodes/EP009/generate_audio_and_subs.py
    → assets/vo/vo.wav · sub.ass · scenes.tsv · timing.json

보통은 이걸 직접 부르지 않고 파이프라인을 쓴다.

    python scripts/pipeline.py EP009
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "scripts"))
from lib_narration import generate_from_scenes  # noqa: E402

if __name__ == "__main__":
    generate_from_scenes("EP009")
