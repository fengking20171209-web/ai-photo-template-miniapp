# import_face_gen.ps1
param(
    [switch]$DryRun,
    [string]$Series = "",
    [string]$InputDir = "",
    [switch]$NonInteractive,
    [switch]$NoThumb,
    [switch]$KeepOriginals,
    [switch]$SyncOneDrive,
    [switch]$Watcher
)
$ScriptDir = Split-Path -Parent $PSCommandPath
$ProjectDir = Split-Path -Parent $ScriptDir
$FaceDir = if ($InputDir) { $InputDir } else { Join-Path $ProjectDir "face" }
$PyScript = Join-Path $ScriptDir "import_face_gen.py"
if (-not (Test-Path $PyScript)) { exit 1 }
if (-not (Test-Path $FaceDir)) { exit 1 }
function Run-Import {
    $a = @()
    if ($DryRun) { $a += "--dry-run" }
    if ($Series) { $a += "--series"; $a += $Series }
    if ($NonInteractive) { $a += "--non-interactive" }
    if ($NoThumb) { $a += "--no-thumb" }
    if ($KeepOriginals) { $a += "--keep-originals" }
    if ($InputDir) { $a += "--input-dir"; $a += $InputDir }
    if ($SyncOneDrive) { $a += "--sync-onedrive" }
    Write-Host "[info]  face: $FaceDir" -ForegroundColor Yellow
    if ($DryRun) { Write-Host "[info]  DRY RUN" -ForegroundColor Magenta }
    if ($SyncOneDrive) { Write-Host "[info]  +OneDrive" -ForegroundColor Green }
    $fc = (Get-ChildItem $FaceDir -Recurse -File | Where-Object {
        $_.Extension -match '\\.(png|jpg|jpeg|webp|bmp)$' -and $_.DirectoryName -notmatch '\\.processed'
    }).Count
    if ($fc -eq 0) { Write-Host "[camera]  empty" -ForegroundColor Yellow; return }
    Write-Host "[camera]  $fc images" -ForegroundColor Green
    python $PyScript @a
    if ($LASTEXITCODE -eq 0) { Write-Host "[done]  OK" -ForegroundColor Green } else { Write-Host "[err]  failed" -ForegroundColor Red }
}
if ($Watcher) {
    $w = New-Object System.IO.FileSystemWatcher
    $w.Path = $FaceDir; $w.IncludeSubdirectories = $true; $w.EnableRaisingEvents = $true
    $act = {
        $p = $Event.SourceEventArgs.FullPath
        $e = [System.IO.Path]::GetExtension($p).ToLower()
        if (@('.png','.jpg','.jpeg','.webp','.bmp') -contains $e) {
            Start-Sleep 2; python $PyScript --non-interactive --sync-onedrive
        }
    }
    Register-ObjectEvent $w "Created" -Action $act > $null
    try { while ($true) { Start-Sleep 5 } } finally { $w.Dispose() }
} else { Run-Import }
