# TABLE//ZERO full project backup + handoff export (PowerShell 7+)
# Usage:  pwsh -File tools/backup_full.ps1 [-Label "short note"]
# - Writes Desktop\TABLE_ZERO_개발현황\ (latest + versioned ZIP, status docs, QA evidence)
# - Never deletes or overwrites a versioned backup
# - Excludes regenerable Unity caches and anything that looks like a secret
# - Re-opens the ZIP and verifies every entry (CRC via full read) + required files
param([string]$Label = "")
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$Desktop = [Environment]::GetFolderPath('Desktop')
$Out = Join-Path $Desktop 'TABLE_ZERO_개발현황'
$Latest = Join-Path $Out '최신_전체백업'
$Versions = Join-Path $Out '버전별_백업'
$Evidence = Join-Path $Out '검증자료'
foreach ($d in @($Out, $Latest, $Versions, "$Evidence\스크린샷", "$Evidence\플레이영상", "$Evidence\테스트로그", "$Evidence\버그리포트")) {
    New-Item -ItemType Directory -Force $d | Out-Null
}

# Free-space check (needs ~3x project size headroom: temp zip + latest + version)
$drive = (Get-Item $Out).PSDrive
$free = (Get-PSDrive $drive.Name).Free

# ---------- collect file list ----------
$excludeDirs = @(
    '\TableZero.Unity\Library\', '\TableZero.Unity\Temp\', '\TableZero.Unity\Obj\', '\TableZero.Unity\obj\',
    '\TableZero.Unity\Logs\', '\TableZero.Unity\UserSettings\', '\TableZero.Unity\.vs\', '\TableZero.Unity\.idea\',
    '\.git\', '\__pycache__\', '\.venv\', '\secrets\', '\server\runtime_state\', '\Builds\_tmp\'
)
$secretName = '^(\.env.*|.*\.pem|.*\.pfx|.*\.key|id_rsa.*|.*secret.*\.json|credentials.*)$'
$files = Get-ChildItem -LiteralPath $Root -Recurse -File -Force | Where-Object {
    $rel = $_.FullName.Substring($Root.Length)
    $skip = $false
    foreach ($x in $excludeDirs) { if ($rel.Contains($x)) { $skip = $true; break } }
    if (-not $skip -and $_.Name -match $secretName) { $skip = $true }
    if (-not $skip -and $_.Extension -in '.blend1', '.blend2', '.tmp') { $skip = $true }
    -not $skip
}
$totalBytes = ($files | Measure-Object Length -Sum).Sum
if ($free -lt ($totalBytes * 3)) {
    throw "디스크 여유 공간 부족: 필요 약 $([math]::Round($totalBytes*3/1GB,2))GB / 남은 $([math]::Round($free/1GB,2))GB. 기존 백업은 삭제하지 않았음"
}

# Scan text files for obvious API keys before packing
$keyPattern = '(sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_\-]{35}|ghp_[A-Za-z0-9]{36})'
$textExt = '.py', '.cs', '.json', '.md', '.txt', '.ps1', '.yaml', '.yml', '.ini', '.cfg', '.toml'
$leaks = $files | Where-Object { $_.Extension -in $textExt -and $_.Length -lt 5MB } |
    Select-String -Pattern $keyPattern -List | Select-Object -ExpandProperty Path
if ($leaks) { throw "비밀 키로 보이는 문자열 발견, 백업 중단: $($leaks -join ', ')" }

# ---------- version number ----------
$existing = Get-ChildItem $Versions -Filter 'TABLE_ZERO_V*_FULL.zip' -ErrorAction SilentlyContinue |
    ForEach-Object { if ($_.Name -match 'TABLE_ZERO_V(\d+)_FULL\.zip') { [int]$Matches[1] } }
$next = if ($existing) { ($existing | Measure-Object -Maximum).Maximum + 1 } else { 1 }
$ver = 'V{0:D3}' -f $next
$verZip = Join-Path $Versions "TABLE_ZERO_${ver}_FULL.zip"
if (Test-Path $verZip) { throw "버전 백업이 이미 존재함: $verZip (덮어쓰지 않음)" }

# ---------- git bundle (history) ----------
$gitInfo = 'git 정보 없음'
$bundle = Join-Path $env:TEMP "tablezero_history_$ver.bundle"
Push-Location $Root
try {
    $branch = (git rev-parse --abbrev-ref HEAD 2>$null)
    $commit = (git log -1 --format='%h %s (%ci)' 2>$null)
    $dirty = (git status --porcelain 2>$null | Measure-Object).Count
    $gitInfo = "브랜치 $branch / 마지막 커밋 $commit / 미커밋 변경 $dirty개"
    git bundle create $bundle --all 2>$null | Out-Null
} finally { Pop-Location }

# ---------- write zip ----------
$tmpZip = Join-Path $env:TEMP "TABLE_ZERO_${ver}_building.zip"
if (Test-Path $tmpZip) { Remove-Item $tmpZip -Force }
$manifestLines = New-Object System.Collections.Generic.List[string]
$zip = [System.IO.Compression.ZipFile]::Open($tmpZip, 'Create', [Text.Encoding]::UTF8)
try {
    foreach ($f in $files) {
        $rel = $f.FullName.Substring($Root.Length + 1).Replace('\', '/')
        $entryName = "TABLE_ZERO/$rel"
        $level = if ($f.Extension -in '.png', '.jpg', '.zip', '.mp4', '.mp3', '.ogg', '.glb') { 'Fastest' } else { 'Optimal' }
        [void][System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, $f.FullName, $entryName, $level)
        $manifestLines.Add("$($f.Length)`t$rel")
    }
    if (Test-Path $bundle) {
        [void][System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, $bundle, 'TABLE_ZERO/_git_history.bundle', 'Fastest')
        $manifestLines.Add("$((Get-Item $bundle).Length)`t_git_history.bundle")
    }
    $info = @"
TABLE//ZERO FULL BACKUP $ver
생성: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
메모: $Label
$gitInfo
파일 수: $($files.Count)  원본 용량: $([math]::Round($totalBytes/1MB,1)) MB
제외: Unity Library/Temp/Obj/Logs/UserSettings, .git(대신 _git_history.bundle 포함), 비밀키 패턴 파일
복원: ZIP 해제 → TABLE_ZERO/TableZero.Unity 를 Unity 6000.6.8f1 로 열기 → 히스토리는 'git clone _git_history.bundle'
"@
    $e = $zip.CreateEntry('TABLE_ZERO/_BACKUP_INFO.txt')
    $w = New-Object IO.StreamWriter($e.Open(), [Text.UTF8Encoding]::new($false)); $w.Write($info); $w.Dispose()
    $e = $zip.CreateEntry('TABLE_ZERO/_BACKUP_FILE_LIST.tsv')
    $w = New-Object IO.StreamWriter($e.Open(), [Text.UTF8Encoding]::new($false)); $w.Write(($manifestLines -join "`n")); $w.Dispose()
} finally { $zip.Dispose() }
if (Test-Path $bundle) { Remove-Item $bundle -Force }

# ---------- verify ----------
$required = @(
    'TABLE_ZERO/TableZero.Unity/ProjectSettings/ProjectVersion.txt',
    'TABLE_ZERO/TableZero.Unity/Packages/manifest.json',
    'TABLE_ZERO/server/api.py',
    'TABLE_ZERO/reference/CASE001_CANON_LOCKED.json',
    'TABLE_ZERO/data/room302_interaction_manifest.json',
    'TABLE_ZERO/references_images/INTERROGATION_TARGET_VISUAL.png',
    'TABLE_ZERO/references_images/SCENE_302_TARGET_VISUAL.png',
    'TABLE_ZERO/docs/status/개발현황.md',
    'TABLE_ZERO/docs/status/다음AI_인계지시서.md',
    'TABLE_ZERO/_BACKUP_INFO.txt'
)
$verify = [System.IO.Compression.ZipFile]::OpenRead($tmpZip)
$bad = 0; $count = 0; $buf = New-Object byte[] 1048576
try {
    $names = @{}
    foreach ($en in $verify.Entries) {
        $names[$en.FullName] = $true; $count++
        $s = $en.Open(); $read = 0L
        try { while (($n = $s.Read($buf, 0, $buf.Length)) -gt 0) { $read += $n } } catch { $bad++ } finally { $s.Dispose() }
        if ($read -ne $en.Length) { $bad++ }
    }
    $missing = $required | Where-Object { -not $names.ContainsKey($_) }
} finally { $verify.Dispose() }
$expected = $files.Count + 2 + $(if ($manifestLines[-1] -like '*_git_history.bundle') { 1 } else { 0 })
if ($bad -gt 0 -or $missing -or $count -ne $expected) {
    throw "ZIP 무결성 검사 실패: 손상 $bad / 누락 $($missing -join ',') / 항목 $count (예상 $expected). 임시 파일: $tmpZip"
}

Copy-Item $tmpZip $verZip
Copy-Item $tmpZip (Join-Path $Latest 'TABLE_ZERO_FULL_LATEST.zip') -Force
Remove-Item $tmpZip -Force
$hash = (Get-FileHash $verZip -Algorithm SHA256).Hash
$latestHash = (Get-FileHash (Join-Path $Latest 'TABLE_ZERO_FULL_LATEST.zip') -Algorithm SHA256).Hash
if ($hash -ne $latestHash) { throw '최신 백업 복사본 해시 불일치' }

# ---------- status docs + evidence ----------
foreach ($doc in '개발현황.md', '다음AI_인계지시서.md', '변경이력.md', '미완성작업.md', '에셋목록_라이선스.md') {
    $src = Join-Path $Root "docs\status\$doc"
    if (Test-Path $src) { Copy-Item $src (Join-Path $Out $doc) -Force }
}
$qa = Join-Path $Root 'qa'
if (Test-Path "$qa\screenshots") { Copy-Item "$qa\screenshots\*" "$Evidence\스크린샷\" -Recurse -Force }
if (Test-Path "$qa\videos") { Copy-Item "$qa\videos\*" "$Evidence\플레이영상\" -Recurse -Force }
if (Test-Path "$qa\logs") { Copy-Item "$qa\logs\*" "$Evidence\테스트로그\" -Recurse -Force }
if (Test-Path "$qa\bugs") { Copy-Item "$qa\bugs\*" "$Evidence\버그리포트\" -Recurse -Force }

$size = (Get-Item $verZip).Length
$line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`t$ver`t$([math]::Round($size/1MB,1))MB`t$count entries`tSHA256 $hash`t$Label"
Add-Content -Path (Join-Path $Out '백업기록.tsv') -Value $line -Encoding utf8
Write-Output "BACKUP_OK $ver"
Write-Output "versioned: $verZip"
Write-Output "latest:    $(Join-Path $Latest 'TABLE_ZERO_FULL_LATEST.zip')"
Write-Output "size: $([math]::Round($size/1MB,1)) MB  entries: $count  sha256: $hash"
Write-Output $gitInfo
