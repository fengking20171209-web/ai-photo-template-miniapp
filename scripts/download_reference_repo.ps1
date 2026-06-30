$ErrorActionPreference = "Stop"

$repoUrl = "https://github.com/EvoLinkAI/awesome-gpt-image-2-API-and-Prompts.git"
$zipUrl = "https://github.com/EvoLinkAI/awesome-gpt-image-2-API-and-Prompts/archive/refs/heads/main.zip"
$root = Split-Path -Parent $PSScriptRoot
$referenceDir = Join-Path $root "references"
$targetDir = Join-Path $referenceDir "awesome-gpt-image-2-API-and-Prompts"
$zipFile = Join-Path $referenceDir "awesome-gpt-image-2-API-and-Prompts.zip"
$gitProxy = if ($env:GIT_PROXY) { $env:GIT_PROXY } else { "socks5h://127.0.0.1:10808" }

New-Item -ItemType Directory -Force -Path $referenceDir | Out-Null

if (Get-Command git -ErrorAction SilentlyContinue) {
  if (Test-Path (Join-Path $targetDir ".git")) {
    git -c http.sslbackend=openssl -c http.proxy=$gitProxy -C $targetDir pull
  } else {
    if (Test-Path $targetDir) {
      Remove-Item -Recurse -Force $targetDir
    }
    git -c http.sslbackend=openssl -c http.proxy=$gitProxy clone $repoUrl $targetDir
  }
  exit 0
}

Invoke-WebRequest -Uri $zipUrl -OutFile $zipFile

if (Test-Path $targetDir) {
  Remove-Item -Recurse -Force $targetDir
}

Expand-Archive -Path $zipFile -DestinationPath $referenceDir -Force
$expandedDir = Join-Path $referenceDir "awesome-gpt-image-2-API-and-Prompts-main"
Move-Item -Path $expandedDir -Destination $targetDir
