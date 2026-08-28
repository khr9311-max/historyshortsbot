#!/usr/bin/env python3
"""
analyze_retention.py — 유튜브 시청 유지율(Retention Curve) & 씬(Scene) 타임라인 매핑 분석기

사용법:
    python scripts/analyze_retention.py EP012
    python scripts/analyze_retention.py EP012 --mock
    python scripts/analyze_retention.py EP012 --video-id <YOUTUBE_ID> --save

동작:
    1. episodes/<EP>/scenes.json 및 timing.json 에서 씬별 타임코드(시작/종료/길이/컷타입) 로드
    2. YouTube Analytics API (또는 --mock) 에서 0~100% 진행률별 시청 유지율 곡선 수집
    3. 각 씬(S01, S02, ...) 구간의 시청 유지율 변화(Δ Retention) 및 이탈률 분석
    4. 도해 컷(diagram) / Veo 컷(veo) 구간별 성능 비교 및 위험 씬(Cliff Drop) 진단
    5. 터미널 시각화 출력 및 episodes/<EP>/analytics_retention.md 리포트 생성
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import lib_scenes  # noqa: E402
import lib_youtube  # noqa: E402


@dataclass
class SceneRetention:
    scene_id: str
    kind: str
    shot_id: str
    start_sec: float
    end_sec: float
    dur_sec: float
    narration: str
    start_pct: float
    end_pct: float
    ret_start: float
    ret_end: float
    drop: float
    drop_per_sec: float
    avg_ret: float
    warning: str = ""


def interpolate_retention(curve: list[dict[str, float]], ratio: float) -> float:
    """진행률 ratio (0.0 ~ 1.0)에 해당하는 유지율(%)을 선형 보간"""
    if not curve:
        return 100.0
    if ratio <= curve[0]["elapsed_ratio"]:
        return curve[0]["retention_pct"]
    if ratio >= curve[-1]["elapsed_ratio"]:
        return curve[-1]["retention_pct"]

    for i in range(len(curve) - 1):
        r1 = curve[i]["elapsed_ratio"]
        r2 = curve[i + 1]["elapsed_ratio"]
        if r1 <= ratio <= r2:
            if abs(r2 - r1) < 1e-6:
                return curve[i]["retention_pct"]
            t = (ratio - r1) / (r2 - r1)
            v1 = curve[i]["retention_pct"]
            v2 = curve[i + 1]["retention_pct"]
            return v1 + t * (v2 - v1)

    return curve[-1]["retention_pct"]


def analyze_episode(ep: str, video_id: str = "", force_mock: bool = False) -> tuple[dict, list[SceneRetention], str]:
    ep_dir = ROOT / "episodes" / ep
    scenes_path = ep_dir / "scenes.json"
    timing_path = ep_dir / "timing.json"

    if not scenes_path.is_file():
        raise FileNotFoundError(f"{ep}: scenes.json 파일이 없습니다.")
    if not timing_path.is_file():
        raise FileNotFoundError(f"{ep}: timing.json 파일이 없습니다. (build/lib_narration 실행 필요)")

    doc = lib_scenes.load(ep)
    timing_data = json.loads(timing_path.read_text(encoding="utf-8"))
    total_dur = float(timing_data.get("total", 0.0))
    if total_dur <= 0:
        total_dur = sum(float(s.get("dur", 0.0)) for s in timing_data.get("scenes", []))

    # 비디오 ID 결정
    target_vid = video_id or doc.package.youtube_video_id or f"MOCK_{ep}"
    metrics = None

    if not force_mock and doc.package.youtube_video_id or (video_id and not force_mock):
        metrics = lib_youtube.fetch_video_analytics(target_vid)

    if metrics is None:
        metrics = lib_youtube.get_mock_metrics(target_vid, total_dur)

    # 씬별 유지율 매핑
    scene_results: list[SceneRetention] = []
    curve = metrics.retention_curve

    for raw_s in timing_data.get("scenes", []):
        sid = raw_s.get("scene", "")
        sc_obj = doc.scene(sid)
        kind = raw_s.get("kind", "")
        # fallback kind from doc
        if not kind or kind.startswith("ai_"):
            kind = sc_obj.kind if sc_obj else "veo"

        start_s = float(raw_s.get("start", 0.0))
        end_s = float(raw_s.get("end", 0.0))
        dur_s = float(raw_s.get("dur", end_s - start_s))
        vo = raw_s.get("vo", "") or (sc_obj.narration if sc_obj else "")
        shot = raw_s.get("shot", "") or (sc_obj.shot if sc_obj else "")

        start_ratio = min(1.0, max(0.0, start_s / total_dur))
        end_ratio = min(1.0, max(0.0, end_s / total_dur))

        ret_start = interpolate_retention(curve, start_ratio)
        ret_end = interpolate_retention(curve, end_ratio)
        drop = ret_start - ret_end
        drop_rate = drop / dur_s if dur_s > 0 else 0.0
        avg_ret = (ret_start + ret_end) / 2.0

        # 경고 판별 규칙
        warn = ""
        if kind == "diagram" and dur_s > lib_scenes.DIAGRAM_MAX_SEC:
            warn = f"⚠️ 도해 길이 초과 ({dur_s:.1f}s > 4.0s)"
        elif kind == "diagram" and drop > 8.0:
            warn = f"⚠️ 도해 구간 급이탈 (-{drop:.1f}%)"
        elif sid == "S01" and drop > 15.0:
            warn = f"⚠️ 훅 이탈 과다 (-{drop:.1f}%)"
        elif drop > 10.0 or drop_rate > 2.2:
            warn = f"⚠️ 급격한 이탈 (-{drop:.1f}%)"

        scene_results.append(SceneRetention(
            scene_id=sid,
            kind=kind,
            shot_id=shot,
            start_sec=start_s,
            end_sec=end_s,
            dur_sec=dur_s,
            narration=vo,
            start_pct=start_ratio * 100.0,
            end_pct=end_ratio * 100.0,
            ret_start=ret_start,
            ret_end=ret_end,
            drop=drop,
            drop_per_sec=drop_rate,
            avg_ret=avg_ret,
            warning=warn,
        ))

    # 종합 통계
    summary = {
        "episode": ep,
        "title": doc.title,
        "youtube_title": doc.package.youtube_title or doc.title,
        "total_duration": total_dur,
        "video_id": metrics.video_id,
        "is_mock": metrics.is_mock,
        "views": metrics.views,
        "average_view_percentage": metrics.average_view_percentage,
        "average_view_duration_sec": metrics.average_view_duration_sec,
        "subscribers_gained": metrics.subscribers_gained,
        "shares": metrics.shares,
        "likes": metrics.likes,
    }

    # 컷 타입별 평균 이탈률
    kind_drops: dict[str, list[float]] = {}
    for sr in scene_results:
        k = "diagram" if sr.kind == "diagram" else ("veo" if "veo" in sr.kind or "hero" in sr.kind else "still")
        kind_drops.setdefault(k, []).append(sr.drop)

    summary["kind_avg_drop"] = {
        k: round(sum(v) / len(v), 2) for k, v in kind_drops.items() if v
    }

    report_md = _build_markdown_report(doc, summary, scene_results, metrics)
    return summary, scene_results, report_md


def _build_markdown_report(doc: lib_scenes.Doc, summary: dict, scenes: list[SceneRetention], metrics: lib_youtube.VideoMetrics) -> str:
    lines: list[str] = []
    mode_badge = "🧪 Mock 시뮬레이션 데이터" if metrics.is_mock else "🔴 실시간 유튜브 데이터"

    lines.append(f"# {doc.episode} 시청 유지율 & 씬 분석 리포트")
    lines.append(f"> **영상 제목:** {summary['youtube_title']}  ")
    lines.append(f"> **데이터 소스:** {mode_badge} (동영상 ID: `{metrics.video_id}`)  ")
    lines.append(f"> **영상 길이:** {summary['total_duration']:.1f}초 · **평균 완주율(AVP):** {summary['average_view_percentage']:.1f}%\n")

    lines.append("## 1. 핵심 성과 지표 (KPIs)")
    lines.append("| 조회수 | 평균 시청 시간 | 완주율 | 좋아요 | 공유 | 구독 전환 |")
    lines.append("|---|---|---|---|---|---|")
    lines.append(f"| {metrics.views:,}회 | {metrics.average_view_duration_sec:.1f}초 | {metrics.average_view_percentage:.1f}% | {metrics.likes:,}개 | {metrics.shares:,}회 | +{metrics.subscribers_gained}명 |\n")

    lines.append("## 2. 컷 타입별 평균 이탈률")
    lines.append("| 컷 타입 | 씬 수 | 평균 이탈폭 (Δ Retention) | 평가 |")
    lines.append("|---|---|---|---|")
    for k, avg_d in summary.get("kind_avg_drop", {}).items():
        eval_str = "🟢 안정적" if avg_d < 4.5 else ("🟡 보통" if avg_d < 7.5 else "🔴 주의 필요")
        name = "도해 컷 (diagram)" if k == "diagram" else ("AI 영상 컷 (veo)" if k == "veo" else "정지 컷 (still)")
        count = sum(1 for s in scenes if (k == "diagram" and s.kind == "diagram") or (k == "veo" and ("veo" in s.kind or "hero" in s.kind)) or (k == "still" and s.kind not in ("diagram", "veo") and "hero" not in s.kind))
        lines.append(f"| {name} | {count}개 | -{avg_d:.2f}% | {eval_str} |")
    lines.append("")

    lines.append("## 3. 씬(Scene)별 정밀 시청 유지율 타임라인")
    lines.append("| 씬 ID | 컷타입 | 구간 | 길이 | 시작 유지율 | 종료 유지율 | 이탈폭 | 나레이션 요약 | 비고 |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for s in scenes:
        short_vo = (s.narration[:24] + "…") if len(s.narration) > 24 else s.narration
        warn_txt = s.warning if s.warning else "-"
        lines.append(f"| `{s.scene_id}` | `{s.kind}` | {s.start_sec:.1f}~{s.end_sec:.1f}s | {s.dur_sec:.1f}s | {s.ret_start:.1f}% | {s.ret_end:.1f}% | **-{s.drop:.1f}%** | {short_vo} | {warn_txt} |")
    lines.append("")

    lines.append("## 4. 파이프라인 최적화 피드백")
    # 자동 피드백 생성
    warnings = [s for s in scenes if s.warning]
    if not warnings:
        lines.append("✅ **모든 씬이 안정적인 시청 유지율을 기록했습니다.** 도해 및 영상 전환 타이밍이 적절합니다.")
    else:
        lines.append("다음 씬에서 상대적으로 높은 시청자 이탈이 감지되었습니다. 차기작 제작 시 반영하세요:\n")
        for w in warnings:
            lines.append(f"- **`{w.scene_id}` ({w.kind}, {w.dur_sec:.1f}초)**: {w.warning}")
            if w.kind == "diagram":
                lines.append(f"  * *개선 팁:* 도해 애니메이션의 텍스트 밀도를 줄이고 노출 시간을 3.0초 이하로 압축하세요.")
            elif w.scene_id == "S01":
                lines.append(f"  * *개선 팁:* 0~2초 첫 문장의 훅 텍스트(`hook_text`)를 더 충격적인 대조/수치형으로 강화하세요.")

    return "\n".join(lines)


def print_cli_summary(summary: dict, scenes: list[SceneRetention]):
    print("\n" + "=" * 70)
    print(f" 📊 [{summary['episode']}] 시청 유지율(Retention) & 씬 분석 결과")
    print("=" * 70)
    print(f" 제목: {summary['youtube_title']}")
    print(f" 조회수: {summary['views']:,}회  ·  완주율(AVP): {summary['average_view_percentage']:.1f}%  ·  구독: +{summary['subscribers_gained']}명")
    print("-" * 70)
    print(f"{'씬':<5} {'타입':<8} {'구간':<12} {'유지율':<16} {'이탈폭':<10} {'진단'}")
    print("-" * 70)

    for s in scenes:
        time_range = f"{s.start_sec:.1f}~{s.end_sec:.1f}s"
        ret_range = f"{s.ret_start:.1f}% -> {s.ret_end:.1f}%"
        drop_str = f"-{s.drop:.1f}%"
        warn = s.warning or "정상"
        print(f"{s.scene_id:<5} {s.kind:<8} {time_range:<12} {ret_range:<16} {drop_str:<10} {warn}")

    print("-" * 70)
    print(" 💡 컷타입별 평균 이탈률:")
    for k, avg_d in summary.get("kind_avg_drop", {}).items():
        print(f"    - {k:<10}: 평균 -{avg_d:.2f}%")
    print("=" * 70 + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="유튜브 시청 유지율 씬 분석기")
    parser.add_argument("episode", help="에피소드 ID (예: EP012)")
    parser.add_argument("--video-id", default="", help="유튜브 비디오 ID 지정")
    parser.add_argument("--mock", action="store_true", help="Mock 시뮬레이션 모드로 강제 실행")
    parser.add_argument("--save", action="store_true", default=True, help="analytics_retention.md 리포트 파일 저장")
    args = parser.parse_args()

    try:
        summary, scenes, report_md = analyze_episode(args.episode, video_id=args.video_id, force_mock=args.mock)
        print_cli_summary(summary, scenes)

        if args.save:
            out_path = ROOT / "episodes" / args.episode / "analytics_retention.md"
            out_path.write_text(report_md, encoding="utf-8")
            print(f"[INFO] 📄 리포트가 저장되었습니다: {out_path}")

        return 0
    except Exception as e:
        print(f"[ERROR] 분석 실패: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
