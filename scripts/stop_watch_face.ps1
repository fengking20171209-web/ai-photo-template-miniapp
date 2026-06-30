# stop_watch_face.ps1 — 停掉 watch_face 后台进程
$procs = Get-CimInstance -ClassName Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -match "watch_face" }
if ($procs) {
    $procs | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
    Write-Host "[ok]  watch_face 已停止" -ForegroundColor Yellow
} else {
    Write-Host "[info]  watch_face 未运行" -ForegroundColor Cyan
}
