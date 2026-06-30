# sync-baidudisk.ps1
# 工作区 → 百度网盘单向同步脚本
# 用法: powershell -ExecutionPolicy Bypass -File scripts/sync-baidudisk.ps1

$ErrorActionPreference = "Stop"

$Src = "D:\Projects\ai-photo-template-miniapp"
$Dst = "E:\BaiduNetdiskDownload\百度网盘同步文件\BaiduSyncdisk\个人资料\2025年12月海南自贸岛封关（Hermes）\Codex生图小程序开发项目\ai-photo-template-miniapp"
$LogDir = "D:\Projects\ai-photo-template-miniapp\logs"
$Ts = Get-Date -Format "yyyyMMdd-HHmmss"

# 确保目标和日志目录存在
if (-not (Test-Path $Dst)) { New-Item -ItemType Directory -Force -Path $Dst | Out-Null }
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Force -Path $LogDir | Out-Null }

$LogFile = Join-Path $LogDir "sync-$Ts.log"

Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 开始同步..."
Write-Host "  源: $Src"
Write-Host "  目标: $Dst"

# robocopy 镜像同步，排除大目录和敏感文件
robocopy $Src $Dst /MIR `
    /XD node_modules .git __pycache__ .pytest_cache .kimi .agents `
    /XF .env *.log `
    /NP /NDL /NFL /NJH /NJS /NC /NS `
    /LOG:$LogFile /TEE

$exitCode = $LASTEXITCODE

# robocopy 退出码: 0=无操作, 1=已复制, 2=额外文件, 3=1+2, 8+=错误
switch ($exitCode) {
    0 { Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 无变化，跳过" }
    1 { Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 同步完成（有文件更新）" }
    2 { Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 同步完成（有额外文件）" }
    3 { Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 同步完成（更新+额外文件）" }
    default {
        if ($exitCode -ge 8) {
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 同步出错，退出码: $exitCode"
            Write-Host "  详情见日志: $LogFile"
            exit 1
        }
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 同步完成（退出码: $exitCode）"
    }
}

# 统计结果
$srcCount = (Get-ChildItem $Src -Recurse -File | Where-Object {
    $_.FullName -notlike "*node_modules*" -and
    $_.FullName -notlike "*.git*" -and
    $_.FullName -notlike "*__pycache__*" -and
    $_.FullName -notlike "*.pytest_cache*" -and
    $_.FullName -notlike "*.kimi*" -and
    $_.FullName -notlike "*.agents*"
}).Count

$dstCount = (Get-ChildItem $Dst -Recurse -File | Where-Object {
    $_.FullName -notlike "*node_modules*" -and
    $_.FullName -notlike "*.git*" -and
    $_.FullName -notlike "*__pycache__*"
}).Count

Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 源: $srcCount 文件 | 目标: $dstCount 文件"
Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 日志: $LogFile"