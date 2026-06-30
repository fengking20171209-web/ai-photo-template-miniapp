$ErrorActionPreference = "Continue"

Write-Host "== Proxy environment =="
Get-ChildItem Env:HTTP_PROXY,Env:HTTPS_PROXY,Env:ALL_PROXY,Env:NO_PROXY -ErrorAction SilentlyContinue |
  Select-Object Name,Value |
  Format-Table -AutoSize

Write-Host "`n== Windows proxy =="
netsh winhttp show proxy
Get-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings" |
  Select-Object ProxyEnable,ProxyServer,AutoConfigURL |
  Format-Table -AutoSize

Write-Host "`n== Common local proxy ports =="
foreach ($port in @(7890, 7897, 10808, 10809, 10813)) {
  $result = Test-NetConnection 127.0.0.1 -Port $port -InformationLevel Quiet
  Write-Host "127.0.0.1:$port`t$result"
}

Write-Host "`n== GitHub via recommended proxy =="
Measure-Command {
  git -c http.sslbackend=openssl -c http.proxy=socks5h://127.0.0.1:10808 ls-remote --heads https://github.com/ZeroLu/awesome-gpt-image.git | Out-Null
} | Select-Object TotalSeconds | Format-Table -AutoSize

Write-Host "`n== GitHub direct =="
Measure-Command {
  git -c http.sslbackend=openssl ls-remote --heads https://github.com/ZeroLu/awesome-gpt-image.git | Out-Null
} | Select-Object TotalSeconds | Format-Table -AutoSize
