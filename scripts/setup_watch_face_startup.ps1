# setup_watch_face_startup.ps1 — 安装 watch_face 到开机自启（免管理员）
$ProjectDir = "D:\Projects\ai-photo-template-miniapp"
$VbsPath = Join-Path $ProjectDir "scripts\watch_face_launcher.vbs"
$StartupDir = [Environment]::GetFolderPath("Startup")
$ShortcutPath = Join-Path $StartupDir "AIPhoto-watch-face.lnk"

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($ShortcutPath)
$shortcut.TargetPath = "wscript.exe"
$shortcut.Arguments = """""""$VbsPath"""""""
$shortcut.WorkingDirectory = "$ProjectDir"
$shortcut.Description = "AI Photo watch_face 后台守护"
$shortcut.WindowStyle = 7
$shortcut.Save()

Write-Host "[ok]  开机自启已添加" -ForegroundColor Green
Write-Host "[info]  路径: $ShortcutPath" -ForegroundColor Cyan
Write-Host "[info]  下次登录自动启动 watch_face" -ForegroundColor Cyan
Write-Host "[info]  手动启动: wscript.exe "$VbsPath"" -ForegroundColor Cyan
Write-Host "[info]  删除: Remove-Item "$ShortcutPath"" -ForegroundColor Cyan
Write-Host "[info]  查看状态: python scripts\watch_face.py --status" -ForegroundColor Cyan
