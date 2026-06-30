param(
  [string]$HostAlias = "tencent-audiobook-ts",
  [string]$RemoteAppDir = "/opt/ai-photo-template-miniapp",
  [string]$Port = "3200",
  [string]$BindHost = "",
  [switch]$SkipSmoke
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$staging = Join-Path $root "output\deploy-staging"
$archive = Join-Path $root "output\ai-photo-template-miniapp.tgz"

if (Test-Path $staging) {
  Remove-Item -Recurse -Force $staging
}
if (Test-Path $archive) {
  Remove-Item -Force $archive
}

New-Item -ItemType Directory -Force $staging | Out-Null

$dirs = @("src", "scripts", "templates", "prompts", "docs", "backend", "public", "deploy")
foreach ($dir in $dirs) {
  robocopy (Join-Path $root $dir) (Join-Path $staging $dir) /E /XD __pycache__ .pytest_cache | Out-Null
  if ($LASTEXITCODE -gt 7) {
    throw "robocopy failed for $dir with exit code $LASTEXITCODE"
  }
}

$files = @("package.json", "package-lock.json", "tsconfig.json", ".env.example", "README.md")
foreach ($file in $files) {
  Copy-Item (Join-Path $root $file) $staging
}

tar -czf $archive -C $staging .

scp $archive "${HostAlias}:/tmp/ai-photo-template-miniapp.tgz"

$remoteScript = @"
set -e
APP="$RemoteAppDir"
PORT="$Port"
HOST_OVERRIDE="$BindHost"
if [ -z "`$HOST_OVERRIDE" ]; then
  HOST_OVERRIDE=`$(tailscale ip -4 2>/dev/null || echo "127.0.0.1")
fi
RELEASE=`$APP/releases/`$(date +%Y%m%d%H%M%S)
sudo mkdir -p "`$APP/releases" "`$APP/shared/output" "`$APP/shared/uploads"
sudo chown -R ubuntu:ubuntu "`$APP"
mkdir -p "`$RELEASE"
tar -xzf /tmp/ai-photo-template-miniapp.tgz -C "`$RELEASE"
cd "`$RELEASE"
npm ci --silent
ln -sfn "`$RELEASE" "`$APP/current"
cat > "`$APP/shared/env" <<EOF
PORT=`$PORT
HOST=`$HOST_OVERRIDE
AI_IMAGE_PROVIDER=mock
AI_IMAGE_DRY_RUN=true
OUTPUT_DIR=`$APP/shared/output
EOF
sudo cp "`$APP/current/deploy/systemd/ai-photo-template-miniapp.service" /etc/systemd/system/ai-photo-template-miniapp.service
sudo systemctl daemon-reload
sudo systemctl enable ai-photo-template-miniapp.service >/dev/null
sudo systemctl restart ai-photo-template-miniapp.service
sleep 3
systemctl is-active ai-photo-template-miniapp.service
curl -fsS "http://`$HOST_OVERRIDE:`$PORT/health"
"@

$remoteDeployScript = Join-Path $root "output\remote-deploy-ai-photo-template.sh"
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($remoteDeployScript, $remoteScript, $utf8NoBom)
scp $remoteDeployScript "${HostAlias}:/tmp/deploy-ai-photo-template.sh"
ssh $HostAlias "bash /tmp/deploy-ai-photo-template.sh"

if (-not $SkipSmoke) {
  $remoteHost = if ($BindHost) {
    $BindHost
  } else {
    ((ssh $HostAlias "tailscale ip -4 2>/dev/null || echo 127.0.0.1") -split "`r?`n" | Where-Object { $_.Trim() } | Select-Object -First 1).Trim()
  }
  curl.exe --noproxy "*" -fsS "http://${remoteHost}:${Port}/health"
  curl.exe --noproxy "*" -fsS "http://${remoteHost}:${Port}/" -o (Join-Path $root "output\remote-home.html")
  Write-Host "Deployed: http://${remoteHost}:${Port}/"
}
