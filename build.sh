#!/usr/bin/env bash
# ============================================================
#  역사 인과 쇼츠 조립 파이프라인 (래퍼)
#  사용법: ./build.sh EP007
#
#  실제 로직은 scripts/build.py 에 있다.
#  Windows/PowerShell 과 동일한 결과를 내야 해서 파이프라인을 두 벌로
#  관리하지 않고 Python 한 벌로 둔다. (manim / edge-tts 때문에 어차피
#  파이썬은 필수 의존성이다.)
# ============================================================
set -euo pipefail

EP="${1:?사용법: ./build.sh EP007}"
cd "$(dirname "$0")"

PY="${PYTHON:-python3}"
command -v "$PY" >/dev/null 2>&1 || PY=python

exec "$PY" scripts/build.py "$EP" "${@:2}"
