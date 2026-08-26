#!/usr/bin/env python3
"""
check_scenes.py — scenes.json 구조·비트 길이 검사 (qc 스크립트용)

    python scripts/check_scenes.py EP007

한 줄에 하나씩 `FAIL …` / `WARN …` 을 찍는다. 아무것도 안 찍히면 통과.
종료 코드: 0 통과 · 1 오류 있음 · 2 scenes.json 없음 (구 방식 에피소드)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib_scenes  # noqa: E402


def main() -> int:
    if len(sys.argv) != 2:
        print("사용법: python scripts/check_scenes.py EP007", file=sys.stderr)
        return 1
    ep = sys.argv[1]

    if not lib_scenes.path_for(ep).is_file():
        return 2

    doc = lib_scenes.load(ep)
    err, warn = lib_scenes.validate(doc)

    timing = lib_scenes.ROOT / "episodes" / ep / "timing.json"
    if timing.is_file():
        e2, w2 = lib_scenes.validate_timing(
            doc, json.loads(timing.read_text(encoding="utf-8")))
        err += e2
        warn += w2

    for w in warn:
        print("WARN " + " ".join(w.split()))
    for e in err:
        print("FAIL " + " ".join(e.split()))
    return 1 if err else 0


if __name__ == "__main__":
    sys.exit(main())
