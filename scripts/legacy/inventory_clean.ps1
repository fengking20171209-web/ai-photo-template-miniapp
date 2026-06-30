$path = "D:\Projects\ai-photo-template-miniapp"
Set-Location $path
Write-Host "--- Directories ---"
(Get-ChildItem -Directory).Name
Write-Host "`n--- Tech Stack / Key Files in Root ---"
(Get-ChildItem -File -Include package.json, requirements.txt, docker-compose.yml, tsconfig.json -Recurse -Depth 1).FullName
