#!/usr/bin/env bash
# 사용법: ./scripts/new_episode.sh EP007
set -euo pipefail

EP="${1:?사용법: ./scripts/new_episode.sh EP007}"
DIR="episodes/${EP}"

if [ -d "$DIR" ]; then
  echo "이미 존재합니다: $DIR" >&2
  exit 1
fi

mkdir -p "$DIR"/{diagrams,assets/{images,clips,vo,bgm}}

cat > "$DIR/scenes.tsv" <<'TSV'
scene	kind	move	dur	note
S01	ai_hero	orbit	2	훅
TSV

cat > "$DIR/script.md" <<MD
# ${EP}

## 소재
(소재 큐 번호 · 제목)

## 인과 구조 한 줄
조건 A + 조건 B → 결과 C

## 대본
### ① 도입 (0~5초)
### ② 난관 (5~18초)
### ③ 해결 (18~45초)
### ④ 요약 (45~53초)
MD

cat > "$DIR/sources.md" <<MD
# ${EP} 출처

> 모든 수치·연도·인용에 근거를 기입한다.
> **빈칸이 하나라도 있으면 발행 금지.**

| 항목 | 대본 내 위치 | 출처 | 확인일 |
|---|---|---|---|
|  |  |  |  |

## 학설 구분
- 지배적 학설:
- 소수설/반론:
MD

touch "$DIR/sub.ass"

echo "생성 완료: $DIR"
echo "다음: claude.ai 프로젝트에서 대본을 뽑아 script.md에 넣고 /new-episode ${EP} 실행"
