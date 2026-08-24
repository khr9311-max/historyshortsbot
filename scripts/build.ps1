# ============================================================
#  역사 인과 쇼츠 조립 파이프라인 (래퍼)
#  사용법: .\scripts\build.ps1 EP007
#
#  실제 로직은 scripts/build.py. build.sh 와 같은 것을 실행한다.
# ============================================================
param(
    [Parameter(Mandatory = $true, Position = 0)][string]$Episode,
    [Parameter(ValueFromRemainingArguments = $true)][string[]]$Rest
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot

# ffmpeg 가 PATH 에 없는 설치(winget 등)를 위해 보정
$wingetLinks = Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Links'
if ((Test-Path $wingetLinks) -and ($env:PATH -notlike "*$wingetLinks*")) {
    $env:PATH = "$wingetLinks;$env:PATH"
}

python (Join-Path $root 'scripts\build.py') $Episode @Rest
exit $LASTEXITCODE
