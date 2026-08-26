# ============================================================
#  발행 전 자동 검사
#  사용법: .\scripts\qc.ps1 EP001
#
#  이전 판이 놓쳤던 것들을 검사 항목으로 넣었다.
#   - 컷 렌더 길이와 scenes.tsv 선언 길이의 불일치 (드리프트 → 자막 어긋남)
#   - 최종 길이 < 나레이션 길이 (마지막 문장 잘림)
#   - 루프 이음매 (첫 프레임 ↔ 끝 프레임 색 차이)
#   - 지정 폰트 설치 여부
#   - dur 을 [int] 로 읽어 6.6 을 6 으로 세던 버그
# ============================================================
param(
    [Parameter(Mandatory = $true, Position = 0)][string]$Episode
)

$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent $PSScriptRoot
$dir = Join-Path $root "episodes\$Episode"
if (-not (Test-Path $dir)) { Write-Error "디렉토리 없음: $dir"; exit 1 }

$wingetLinks = Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Links'
if ((Test-Path $wingetLinks) -and ($env:PATH -notlike "*$wingetLinks*")) {
    $env:PATH = "$wingetLinks;$env:PATH"
}

$errors = 0; $warnings = 0
function Fail($m) { Write-Host "FAIL  $m" -ForegroundColor Red; $script:errors++ }
function Warn($m) { Write-Host "WARN  $m" -ForegroundColor Yellow; $script:warnings++ }
function Pass($m) { Write-Host "PASS  $m" -ForegroundColor Green }

function VideoDuration($p) {
    if (-not (Test-Path $p)) { return $null }
    $d = & ffprobe -v error -show_entries format=duration -of csv=p=0 $p 2>$null
    if ($d) { return [double]$d } else { return $null }
}

Write-Host "=== QC: $Episode ===" -ForegroundColor Cyan

# ---------- 1. 출처 ----------
Write-Host "`n[1] 출처" -ForegroundColor Cyan
$sourcesPath = Join-Path $dir 'sources.md'
if (-not (Test-Path $sourcesPath)) {
    Fail "sources.md 없음 — 발행 금지"
} elseif ((Get-Content $sourcesPath -Raw) -match '\|\s*\|\s*\|\s*\|\s*\|') {
    Fail "sources.md 에 빈 항목 — 발행 금지"
} else {
    Pass "sources.md 채워짐"
}

# ---------- 1b. scenes.json 구조 ----------
Write-Host "`n[1b] scenes.json" -ForegroundColor Cyan
$check = & python (Join-Path $PSScriptRoot 'check_scenes.py') $Episode 2>&1
if ($LASTEXITCODE -eq 2) {
    Warn "scenes.json 없음 — 구 방식 에피소드 (EP001~003)"
} elseif (-not $check) {
    Pass "구조·비트 길이 검증 통과"
} else {
    foreach ($line in $check) {
        $text = [string]$line
        if ($text.StartsWith('FAIL ')) { Fail $text.Substring(5) }
        elseif ($text.StartsWith('WARN ')) { Warn $text.Substring(5) }
        else { Write-Host "      $text" }
    }
}

# ---------- 2. 씬 매니페스트 ----------
Write-Host "`n[2] 씬 매니페스트" -ForegroundColor Cyan
$tsvPath = Join-Path $dir 'scenes.tsv'
$scenes = $null
if (-not (Test-Path $tsvPath)) {
    Fail "scenes.tsv 없음"
} else {
    $scenes = @(Import-Csv -Path $tsvPath -Delimiter "`t")
    if ($scenes.Count -eq 0) {
        Fail "scenes.tsv 가 비어 있음"
    } else {
        if ($scenes[0].kind -ne 'ai_hero') { Fail "1번 씬은 ai_hero 여야 함 (현재 $($scenes[0].kind))" }
        if ($scenes[-1].kind -ne 'diagram') { Fail "마지막 씬은 diagram 이어야 함 (현재 $($scenes[-1].kind))" }

        # dur 은 소수다. [int] 로 읽으면 6.6 이 6 이 된다.
        $totalDur = ($scenes | Measure-Object -Property dur -Sum).Sum
        $hero = ($scenes | Where-Object kind -eq 'ai_hero').Count
        $still = ($scenes | Where-Object kind -eq 'ai_still').Count
        $diag = ($scenes | Where-Object kind -eq 'diagram').Count
        Pass ("{0} 컷 / {1:N2}s  (hero {2} · still {3} · diagram {4})" -f $scenes.Count, $totalDur, $hero, $still, $diag)

        if ($totalDur -lt 45 -or $totalDur -gt 55) { Warn ("총 길이 {0:N1}s 가 목표 45~55s 밖" -f $totalDur) }

        # diagram 3연속 금지 (바이블 §7)
        $run = 0
        foreach ($s in $scenes) {
            if ($s.kind -eq 'diagram') { $run++; if ($run -ge 3) { Fail "diagram 컷 3개 연속 — 도표 피로"; break } }
            else { $run = 0 }
        }
    }
}

# ---------- 3. 도해 코드 ↔ 렌더 길이 ----------
Write-Host "`n[3] 도해" -ForegroundColor Cyan
if ($scenes) {
    foreach ($s in ($scenes | Where-Object kind -eq 'diagram')) {
        $py = Join-Path $dir "diagrams\$($s.scene).py"
        $clip = Join-Path $dir "assets\clips\$($s.scene).mp4"
        if (-not (Test-Path $py)) { Fail "$($s.scene): diagrams\$($s.scene).py 없음"; continue }
        if (-not (Test-Path $clip)) { Warn "$($s.scene): 렌더 결과 없음 (build 시 자동 렌더됨)"; continue }
        if ((Get-Item $py).LastWriteTime -gt (Get-Item $clip).LastWriteTime) {
            Warn "$($s.scene): .py 가 렌더보다 새로움 (build 시 자동 재렌더됨)"
        }
        $d = VideoDuration $clip
        $want = [double]$s.dur
        # 1프레임(0.04s) 이상 어긋나면 자막이 밀린다
        if ($d -ne $null -and [Math]::Abs($d - $want) -gt 0.05) {
            Fail ("{0}: 렌더 {1:N2}s vs 선언 {2:N2}s ({3:+0.00;-0.00}s) — 타임라인이 밀림" -f $s.scene, $d, $want, ($d - $want))
        }
    }
    if ($errors -eq 0) { Pass "도해 코드·렌더 길이 정합" }
}

# ---------- 4. 에셋 ----------
Write-Host "`n[4] 에셋" -ForegroundColor Cyan
foreach ($f in @('assets\vo\vo.wav', 'sub.ass', 'timing.json')) {
    if (-not (Test-Path (Join-Path $dir $f))) { Fail "$f 없음" }
}
foreach ($f in @('assets\bgm\bgm.mp3', 'assets\bgm\amb.wav')) {
    if (-not (Test-Path (Join-Path $dir $f))) { Warn "$f 없음 — 분위기 레이어가 빠짐" }
}
if ($scenes) {
    $shotMap = @{}
    $timingPath = Join-Path $dir 'timing.json'
    if (Test-Path $timingPath) {
        $tj = Get-Content $timingPath -Raw -Encoding UTF8 | ConvertFrom-Json
        foreach ($item in $tj.scenes) {
            $shotMap[$item.scene] = $item.shot
        }
    }

    foreach ($s in $scenes) {
        $shotName = if ($shotMap.ContainsKey($s.scene) -and $shotMap[$s.scene]) { $shotMap[$s.scene] } else { $s.scene }
        if ($s.kind -eq 'ai_still') {
            $img1 = Test-Path (Join-Path $dir "assets\images\$shotName.png")
            $img2 = Test-Path (Join-Path $dir "assets\images\$($s.scene).png")
            if (-not $img1 -and -not $img2) {
                Fail "$($s.scene): images\$shotName.png 없음"
            }
        }
        if ($s.kind -eq 'ai_hero') {
            $c = (Test-Path (Join-Path $dir "assets\clips\$shotName.mp4")) -or (Test-Path (Join-Path $dir "assets\clips\$($s.scene).mp4"))
            $i = (Test-Path (Join-Path $dir "assets\images\$shotName.png")) -or (Test-Path (Join-Path $dir "assets\images\$($s.scene).png"))
            if (-not $c -and -not $i) { Fail "$($s.scene): 클립($shotName.mp4)도 이미지도 없음" }
            elseif (-not $c) { Warn "$($s.scene): i2v 클립 없음 — 정지 컷으로 대체됨" }
        }
    }
}
if ($errors -eq 0) { Pass "필수 에셋 확인" }

# ---------- 5. 자막 ----------
Write-Host "`n[5] 자막" -ForegroundColor Cyan
$assPath = Join-Path $dir 'sub.ass'
if (Test-Path $assPath) {
    $lines = Get-Content $assPath -Encoding UTF8
    $dlg = @($lines | Where-Object { $_ -like 'Dialogue:*' })
    $zero = 0
    foreach ($d in $dlg) {
        $p = $d.Substring(10).Split(',')
        if ($p[0].Trim() -eq $p[1].Trim()) { $zero++ }
    }
    # 이전 판은 튜플 언패킹 실수로 2단 자막의 앞 절반이 항상 0초였다
    if ($zero -gt 0) { Fail "길이 0초인 자막 $zero 줄 — 화면에 안 나옴" }
    else { Pass "$($dlg.Count) 줄 · 0초 자막 없음" }

    $fontLine = $lines | Where-Object { $_ -like 'Style: Default,*' }
    if ($fontLine) {
        $font = $fontLine.Split(',')[1]
        Add-Type -AssemblyName System.Drawing
        $installed = (New-Object System.Drawing.Text.InstalledFontCollection).Families.Name
        if ($installed -notcontains $font) { Fail "자막 폰트 '$font' 미설치 — 폴백 폰트로 렌더됨" }
        else { Pass "자막 폰트 '$font' 설치 확인" }
    }
}

# ---------- 6. 최종 결과물 ----------
Write-Host "`n[6] 최종 결과물" -ForegroundColor Cyan
$final = Join-Path $root "render\$Episode`_final.mp4"
if (-not (Test-Path $final)) {
    Warn "render\$Episode`_final.mp4 없음 — build 를 먼저 실행하세요"
} else {
    $vd = VideoDuration $final
    $vo = VideoDuration (Join-Path $dir 'assets\vo\vo.wav')
    Pass ("길이 {0:N2}s" -f $vd)
    if ($vo -and ($vo - $vd) -gt 0.05) { Fail ("나레이션이 {0:N2}s 잘림 (영상 {1:N2}s < 음성 {2:N2}s)" -f ($vo - $vd), $vd, $vo) }

    $res = & ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x $final 2>$null
    if ($res -ne '1080x1920') { Fail "해상도 $res (1080x1920 이어야 함)" } else { Pass "해상도 1080x1920" }

    # 루프 이음매: 첫 프레임과 끝 프레임의 평균색이 가까워야 반복 재생이 매끄럽다
    $py = @'
import subprocess,sys,tempfile,os
from pathlib import Path
import numpy as np
from PIL import Image
ff=os.environ.get("FFMPEG_BIN","ffmpeg"); v=sys.argv[1]; d=float(sys.argv[2])
def avg(t):
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/"f.png"
        subprocess.run([ff,"-y","-v","error","-ss",str(t),"-i",v,"-frames:v","1",str(p)],check=True)
        return np.asarray(Image.open(p).convert("RGB"),dtype=float).reshape(-1,3).mean(axis=0)
a,b=avg(0.0),avg(d-0.06)
print("%.1f %s %s"%(float(np.abs(a-b).max()),
      "#%02X%02X%02X"%tuple(int(x) for x in a),"#%02X%02X%02X"%tuple(int(x) for x in b)))
'@
    $tmpPy = Join-Path $env:TEMP "qc_loop_$PID.py"
    Set-Content -Path $tmpPy -Value $py -Encoding UTF8
    $env:FFMPEG_BIN = (Get-Command ffmpeg).Source
    $out = python $tmpPy $final $vd 2>$null
    Remove-Item $tmpPy -ErrorAction SilentlyContinue
    if ($out) {
        $parts = $out.Trim().Split(' ')
        $delta = [double]$parts[0]
        if ($delta -le 12) { Pass "루프 이음매 OK — 첫 $($parts[1]) / 끝 $($parts[2]) (최대 채널차 $delta)" }
        elseif ($delta -le 25) { Warn "루프 이음매 다소 튐 — 첫 $($parts[1]) / 끝 $($parts[2]) (차 $delta)" }
        else { Fail "루프 이음매 끊김 — 첫 $($parts[1]) / 끝 $($parts[2]) (차 $delta). 마지막 컷의 LOOP_TAIL 을 확인하세요" }
    } else { Warn "루프 이음매 검사 실패 (PIL/numpy 필요)" }

    $lufs = (& ffmpeg -hide_banner -nostats -i $final -af ebur128=framelog=quiet -f null - 2>&1 |
             Select-String -Pattern '^\s+I:\s+(-?[\d.]+)\s+LUFS' | Select-Object -Last 1)
    if ($lufs -and $lufs.Matches[0].Groups[1].Value) {
        $I = [double]$lufs.Matches[0].Groups[1].Value
        if ([Math]::Abs($I + 14) -le 1.5) { Pass ("라우드니스 {0:N1} LUFS" -f $I) }
        else { Warn ("라우드니스 {0:N1} LUFS (목표 -14)" -f $I) }
    }
}

Write-Host "`n=== 결과: 오류 $errors · 경고 $warnings ===" -ForegroundColor Cyan
if ($errors -eq 0) { exit 0 } else { exit 1 }
