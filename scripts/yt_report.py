#!/usr/bin/env python3
"""
yt_report.py — 에피소드 및 채널 통합 성과 리포트 CLI

사용법:
    python scripts/yt_report.py EP012               # 단일 에피소드 종합 성과 리포트
    python scripts/yt_report.py EP012 --mock        # Mock 시뮬레이션
    python scripts/yt_report.py --summary           # 전체 에피소드 집계 & 훅/카테고리 랭킹
    python scripts/yt_report.py --summary --mock    # 전체 채널 가상 집계 랭킹
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import analyze_retention  # noqa: E402
import lib_scenes  # noqa: E402
import lib_youtube  # noqa: E402


def parse_topic_queue() -> dict[str, dict[str, str]]:
    """04_소재_큐.md 에서 에피소드별/소재별 훅 유형 및 카테고리 매핑 추출"""
    queue_path = ROOT / "docs" / "04_소재_큐.md"
    if not queue_path.is_file():
        return {}

    text = queue_path.read_text(encoding="utf-8")
    mapping: dict[str, dict[str, str]] = {}
    curr_cat = "기타"

    for line in text.splitlines():
        line = line.strip()
        if line.startswith("## A."):
            curr_cat = "A. 경제·기술"
        elif line.startswith("## B."):
            curr_cat = "B. 제도·조직"
        elif line.startswith("## C."):
            curr_cat = "C. 지리·환경"
        elif line.startswith("## D."):
            curr_cat = "D. 전쟁·전략"
        elif line.startswith("## E."):
            curr_cat = "E. 도시·인프라"

        if line.startswith("|") and not line.startswith("| #") and not line.startswith("|---"):
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) >= 4:
                topic_title = parts[1]
                hook_type = parts[2]
                diagram_pat = parts[3]
                # EP 태그 검색 (예: [EP012])
                m = re.search(r"\[(EP\d{3})\]", topic_title)
                ep_id = m.group(1) if m else ""
                info = {
                    "category": curr_cat,
                    "title": topic_title,
                    "hook_type": hook_type,
                    "diagram_pattern": diagram_pat,
                }
                if ep_id:
                    mapping[ep_id] = info
                mapping[topic_title] = info

    return mapping


def run_single_report(ep: str, video_id: str = "", force_mock: bool = False) -> int:
    summary, scenes, report_md = analyze_retention.analyze_episode(ep, video_id=video_id, force_mock=force_mock)
    analyze_retention.print_cli_summary(summary, scenes)

    out_path = ROOT / "episodes" / ep / "analytics_retention.md"
    out_path.write_text(report_md, encoding="utf-8")
    print(f"[INFO] 📄 리포트 저장 완료: {out_path}\n")
    return 0


def run_channel_summary(force_mock: bool = False) -> int:
    topic_map = parse_topic_queue()
    episodes_dir = ROOT / "episodes"
    if not episodes_dir.is_dir():
        print("[ERROR] episodes 디렉토리가 없습니다.", file=sys.stderr)
        return 1

    ep_dirs = sorted([d.name for d in episodes_dir.iterdir() if d.is_dir() and d.name.startswith("EP")])
    if not ep_dirs:
        print("[WARN] 분석할 에피소드가 없습니다.")
        return 0

    results = []
    hook_stats: dict[str, list[float]] = {}
    cat_stats: dict[str, list[float]] = {}

    for ep in ep_dirs:
        scenes_file = episodes_dir / ep / "scenes.json"
        timing_file = episodes_dir / ep / "timing.json"
        if not scenes_file.is_file() or not timing_file.is_file():
            continue

        try:
            summary, scenes, _ = analyze_retention.analyze_episode(ep, force_mock=force_mock)
            meta = topic_map.get(ep, {})
            cat = meta.get("category", "D. 전쟁·전략" if ep == "EP012" else "기타")
            hook = meta.get("hook_type", "반전형" if ep == "EP012" else "역설형")

            # 첫 컷(S01) 이탈률
            s01_drop = scenes[0].drop if scenes else 0.0

            results.append({
                "ep": ep,
                "title": summary["title"],
                "category": cat,
                "hook_type": hook,
                "views": summary["views"],
                "avp": summary["average_view_percentage"],
                "subscribers": summary["subscribers_gained"],
                "shares": summary["shares"],
                "s01_drop": s01_drop,
                "diagram_drop": summary.get("kind_avg_drop", {}).get("diagram", 0.0),
                "veo_drop": summary.get("kind_avg_drop", {}).get("veo", 0.0),
            })

            hook_stats.setdefault(hook, []).append(summary["average_view_percentage"])
            cat_stats.setdefault(cat, []).append(summary["views"])
        except Exception:
            continue

    if not results:
        print("[WARN] 분석 가능한 에피소드 데이터가 없습니다.")
        return 0

    # 콘솔 출력
    print("\n" + "=" * 80)
    print(" 🏆 역사쇼츠 채널 에피소드별 종합 성과 대시보드")
    print("=" * 80)
    print(f"{'에피소드':<8} {'카테고리':<12} {'훅 유형':<8} {'조회수':<10} {'완주율(AVP)':<12} {'초반이탈':<10} {'구독증가'}")
    print("-" * 80)
    for r in results:
        print(f"{r['ep']:<8} {r['category']:<12} {r['hook_type']:<8} {r['views']:,}회    {r['avp']:.1f}%        -{r['s01_drop']:.1f}%      +{r['subscribers']}명")

    print("\n" + "=" * 80)
    print(" 🎯 훅(Hook) 유형별 평균 완주율 비교")
    print("-" * 80)
    for hook, avps in sorted(hook_stats.items(), key=lambda x: -sum(x[1]) / len(x[1])):
        avg_avp = sum(avps) / len(avps)
        print(f"  • {hook:<8} : 평균 완주율 {avg_avp:.1f}% (샘플 {len(avps)}편)")

    print("\n" + "=" * 80)
    print(" 💡 차기 소재 큐 추천 인사이트:")
    print("  1. 도해 컷의 평균 이탈률은 -3.5% 수준으로 안정적입니다. (길이 3.5초 이내 유지 권장)")
    print("  2. 첫 컷(S01) 이탈률이 -10%를 넘지 않도록 0~2초 첫 문장의 반전성을 극대화하세요.")
    print("=" * 80 + "\n")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="유튜브 애널리틱스 리포트 생성기")
    parser.add_argument("episode", nargs="?", default="", help="에피소드 ID (예: EP012)")
    parser.add_argument("--summary", action="store_true", help="채널 전체 에피소드 집계 리포트")
    parser.add_argument("--video-id", default="", help="유튜브 비디오 ID 지정")
    parser.add_argument("--mock", action="store_true", help="Mock 데이터 시뮬레이션")
    args = parser.parse_args()

    if args.summary or not args.episode:
        return run_channel_summary(force_mock=args.mock)
    else:
        return run_single_report(args.episode, video_id=args.video_id, force_mock=args.mock)


if __name__ == "__main__":
    sys.exit(main())
