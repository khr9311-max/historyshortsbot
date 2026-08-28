#!/usr/bin/env python3
"""
lib_youtube.py — YouTube Analytics API & Data API v3 연동 라이브러리

유튜브 쇼츠 영상의 실시간 성과 지표(조회수, 완주율, 구독 전환, 트래픽 소스)와
초 단위 시청 유지율 곡선(Audience Retention Curve)을 수집하고 캐싱합니다.

인증 방식:
  1. 프로젝트 루트의 `client_secrets.json` (Google Cloud Console OAuth 2.0 클라이언트)
  2. 첫 실행 시 로컬 브라우저 인증을 거쳐 `.token.json`에 토큰 자동 저장/갱신
  3. API 키가 없거나 테스트 시 `--mock` 플래그로 실측 형태 시뮬레이션 지원
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
import webbrowser
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parents[1]
TOKEN_PATH = ROOT / ".token.json"
CLIENT_SECRETS_PATH = ROOT / "client_secrets.json"

AUTH_URI = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URI = "https://oauth2.googleapis.com/token"
ANALYTICS_API_BASE = "https://youtubeanalytics.googleapis.com/v2/reports"
DATA_API_BASE = "https://www.googleapis.com/youtube/v3"

SCOPES = [
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.readonly",
]


@dataclass
class VideoMetrics:
    video_id: str
    views: int = 0
    estimated_minutes_watched: float = 0.0
    average_view_duration_sec: float = 0.0
    average_view_percentage: float = 0.0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    subscribers_gained: int = 0
    subscribers_lost: int = 0
    thumbnail_ctr: float = 0.0
    traffic_sources: list[dict[str, Any]] = field(default_factory=list)
    retention_curve: list[dict[str, float]] = field(default_factory=list)
    is_mock: bool = False


# ============================================================
# OAuth 2.0 인증 & 토큰 관리
# ============================================================
class _OAuthCallbackHandler(BaseHTTPRequestHandler):
    auth_code: str | None = None

    def do_GET(self):
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        if "code" in params:
            _OAuthCallbackHandler.auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html = """
            <html><body style="font-family:sans-serif; text-align:center; padding-top:50px;">
            <h2>✅ 유튜브 인증 완료</h2>
            <p>브라우저 창을 닫고 터미널로 돌아가셔도 좋습니다.</p>
            </body></html>
            """
            self.wfile.write(html.encode("utf-8"))
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Auth failed or code not found.")

    def log_message(self, format, *args):
        pass


def _load_client_secrets() -> tuple[str, str]:
    """client_secrets.json 또는 .env 에서 client_id / client_secret 로드"""
    if CLIENT_SECRETS_PATH.is_file():
        try:
            data = json.loads(CLIENT_SECRETS_PATH.read_text(encoding="utf-8"))
            installed = data.get("installed") or data.get("web") or {}
            cid = installed.get("client_id", "")
            secret = installed.get("client_secret", "")
            if cid and secret:
                return cid, secret
        except Exception:
            pass

    # 환경 변수 폴백
    cid = os.environ.get("YOUTUBE_CLIENT_ID", "")
    secret = os.environ.get("YOUTUBE_CLIENT_SECRET", "")
    return cid, secret


def _refresh_access_token(client_id: str, client_secret: str, refresh_token: str) -> dict | None:
    """리프레시 토큰으로 새 액세스 토큰 발급"""
    try:
        import requests
        resp = requests.post(TOKEN_URI, data={
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }, timeout=10)
        if resp.status_code == 200:
            token_data = resp.json()
            token_data["refresh_token"] = refresh_token
            token_data["expires_at"] = time.time() + token_data.get("expires_in", 3600) - 60
            TOKEN_PATH.write_text(json.dumps(token_data, ensure_ascii=False, indent=2), encoding="utf-8")
            return token_data
    except Exception as e:
        print(f"[WARN] 토큰 갱신 실패: {e}", file=sys.stderr)
    return None


def get_access_token(interactive: bool = True) -> str | None:
    """저장된 토큰을 읽거나 없으면 OAuth 2.0 브라우저 인증을 진행합니다."""
    client_id, client_secret = _load_client_secrets()
    if not client_id or not client_secret:
        return None

    # 기존 캐시된 토큰 확인
    if TOKEN_PATH.is_file():
        try:
            token_data = json.loads(TOKEN_PATH.read_text(encoding="utf-8"))
            if token_data.get("expires_at", 0) > time.time():
                return token_data.get("access_token")
            if token_data.get("refresh_token"):
                refreshed = _refresh_access_token(client_id, client_secret, token_data["refresh_token"])
                if refreshed:
                    return refreshed.get("access_token")
        except Exception:
            pass

    if not interactive:
        return None

    # 신규 브라우저 인증 플로우
    redirect_uri = "http://localhost:8080/"
    auth_params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
    }
    auth_url = f"{AUTH_URI}?{urllib.parse.urlencode(auth_params)}"

    print("\n[YouTube OAuth] 브라우저를 열어 YouTube 권한을 승인합니다...")
    print(f"인증 URL: {auth_url}\n")
    webbrowser.open(auth_url)

    server = HTTPServer(("localhost", 8080), _OAuthCallbackHandler)
    server.handle_request()

    code = _OAuthCallbackHandler.auth_code
    if not code:
        print("[ERROR] 인증 코드를 수신하지 못했습니다.", file=sys.stderr)
        return None

    try:
        import requests
        resp = requests.post(TOKEN_URI, data={
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }, timeout=15)
        if resp.status_code == 200:
            token_data = resp.json()
            token_data["expires_at"] = time.time() + token_data.get("expires_in", 3600) - 60
            TOKEN_PATH.write_text(json.dumps(token_data, ensure_ascii=False, indent=2), encoding="utf-8")
            print("[INFO] ✅ 유튜브 인증 토큰이 안전하게 저장되었습니다 (.token.json)")
            return token_data.get("access_token")
        else:
            print(f"[ERROR] 토큰 발급 실패: {resp.text}", file=sys.stderr)
    except Exception as e:
        print(f"[ERROR] 토큰 요청 중 오류: {e}", file=sys.stderr)

    return None


# ============================================================
# API 쿼리 및 데이터 정제
# ============================================================
def fetch_video_analytics(video_id: str, start_date: str = "2024-01-01", end_date: str = "2030-12-31") -> VideoMetrics | None:
    """YouTube Analytics API를 호출해 동영상의 성과 지표와 유지율 곡선을 수집합니다."""
    token = get_access_token(interactive=False)
    if not token:
        return None

    try:
        import requests
        headers = {"Authorization": f"Bearer {token}"}

        # 1. 핵심 지표 쿼리
        params_metrics = {
            "ids": "channel==MINE",
            "startDate": start_date,
            "endDate": end_date,
            "metrics": "views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,likes,comments,shares,subscribersGained,subscribersLost",
            "filters": f"video=={video_id}",
        }
        res_m = requests.get(ANALYTICS_API_BASE, headers=headers, params=params_metrics, timeout=10)
        res_m.raise_for_status()
        data_m = res_m.json()

        rows = data_m.get("rows", [])
        if not rows:
            return None

        r = rows[0]
        metrics = VideoMetrics(
            video_id=video_id,
            views=int(r[0]),
            estimated_minutes_watched=float(r[1]),
            average_view_duration_sec=float(r[2]),
            average_view_percentage=float(r[3]),
            likes=int(r[4]),
            comments=int(r[5]),
            shares=int(r[6]),
            subscribers_gained=int(r[7]),
            subscribers_lost=int(r[8]),
        )

        # 2. 시청 유지율 곡선 쿼리 (0% ~ 100% 진행 구간별 유지율)
        params_retention = {
            "ids": "channel==MINE",
            "startDate": start_date,
            "endDate": end_date,
            "metrics": "audienceWatchRatio,relativeRetentionPerformance",
            "dimensions": "elapsedVideoTimeRatio",
            "filters": f"video=={video_id}",
        }
        res_r = requests.get(ANALYTICS_API_BASE, headers=headers, params=params_retention, timeout=10)
        if res_r.status_code == 200:
            data_r = res_r.json()
            # rows: [ [ratio, watchRatio, relativeRatio], ... ]
            ret_curve = []
            for row in data_r.get("rows", []):
                ret_curve.append({
                    "elapsed_ratio": float(row[0]),
                    "retention_pct": float(row[1]) * 100.0,
                    "relative_performance": float(row[2]) if len(row) > 2 else 1.0,
                })
            metrics.retention_curve = ret_curve

        # 3. 트래픽 소스 쿼리
        params_traffic = {
            "ids": "channel==MINE",
            "startDate": start_date,
            "endDate": end_date,
            "metrics": "views,estimatedMinutesWatched",
            "dimensions": "insightTrafficSourceType",
            "filters": f"video=={video_id}",
            "sort": "-views",
        }
        res_t = requests.get(ANALYTICS_API_BASE, headers=headers, params=params_traffic, timeout=10)
        if res_t.status_code == 200:
            data_t = res_t.json()
            sources = []
            for row in data_t.get("rows", []):
                sources.append({
                    "source_type": row[0],
                    "views": int(row[1]),
                    "watch_minutes": float(row[2]),
                })
            metrics.traffic_sources = sources

        return metrics
    except Exception as e:
        print(f"[WARN] YouTube API 조회 실패 ({video_id}): {e}", file=sys.stderr)
        return None


# ============================================================
# Mock 시뮬레이터 (개발/테스트 및 사전 검증용)
# ============================================================
def get_mock_metrics(video_id: str = "MOCK_EP012", duration_sec: float = 40.0) -> VideoMetrics:
    """실제 유튜브 쇼츠 통계 패턴을 반영한 정밀 시뮬레이션 지표 생성"""
    import math

    # 전형적인 쇼츠 이탈 곡선 시뮬레이션:
    # 0~10%: 스와이프 이탈 (100% -> 88%)
    # 10~50%: 안정적인 인과 서사 진행 (88% -> 76%)
    # 50~70%: 중간 도해 구간 약간의 이탈 (76% -> 67%)
    # 70~95%: 결론 및 반전 클라이맥스 (67% -> 62%)
    # 95~100%: 엔딩/루프 전환 (62% -> 58%)
    ret_curve = []
    for step in range(101):
        ratio = step / 100.0
        if ratio <= 0.08:
            ret = 100.0 - (ratio / 0.08) * 12.0
        elif ratio <= 0.45:
            ret = 88.0 - ((ratio - 0.08) / 0.37) * 11.0
        elif ratio <= 0.65:
            # 도해 구간 살짝 빠른 이탈 시뮬레이션
            ret = 77.0 - ((ratio - 0.45) / 0.20) * 10.0
        elif ratio <= 0.90:
            ret = 67.0 - ((ratio - 0.65) / 0.25) * 5.0
        else:
            ret = 62.0 - ((ratio - 0.90) / 0.10) * 5.0

        # 자연스러운 미세 노이즈
        noise = math.sin(ratio * 30.0) * 0.4
        ret_curve.append({
            "elapsed_ratio": round(ratio, 3),
            "retention_pct": round(max(10.0, min(100.0, ret + noise)), 2),
            "relative_performance": round(1.0 + math.cos(ratio * 10) * 0.15, 2),
        })

    return VideoMetrics(
        video_id=video_id,
        views=18450,
        estimated_minutes_watched=8850.0,
        average_view_duration_sec=round(duration_sec * 0.74, 1),
        average_view_percentage=74.2,
        likes=842,
        comments=63,
        shares=129,
        subscribers_gained=87,
        subscribers_lost=4,
        thumbnail_ctr=8.4,
        traffic_sources=[
            {"source_type": "SHORTS", "views": 15680, "watch_minutes": 7520.0},
            {"source_type": "YT_SEARCH", "views": 1620, "watch_minutes": 810.0},
            {"source_type": "RELATED_VIDEO", "views": 850, "watch_minutes": 380.0},
            {"source_type": "CHANNEL", "views": 300, "watch_minutes": 140.0},
        ],
        retention_curve=ret_curve,
        is_mock=True,
    )
