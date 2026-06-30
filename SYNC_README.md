# Sync Info — 百度网盘同步说明

## 项目路径

| 位置 | 路径 |
|---|---|
| 工作区（源） | D:\Projects\ai-photo-template-miniapp |
| 百度网盘同步（目标） | E:\BaiduNetdiskDownload\百度网盘同步文件\BaiduSyncdisk\个人资料\2025年12月海南自贸岛封关（Hermes）\Codex生图小程序开发项目\ai-photo-template-miniapp |

## 同步方式

百度网盘同步空间自动同步，本地修改后等待百度网盘客户端上传即可。

手动同步命令（PowerShell）：

`powershell
# 全量同步（排除 node_modules / __pycache__）
 = "D:\Projects\ai-photo-template-miniapp"
 = "E:\BaiduNetdiskDownload\百度网盘同步文件\BaiduSyncdisk\个人资料\2025年12月海南自贸岛封关（Hermes）\Codex生图小程序开发项目\ai-photo-template-miniapp"

Get-ChildItem  -Recurse -File | Where-Object {
    .DirectoryName -notmatch "node_modules|__pycache__|\.git"
} | ForEach-Object {
     = .FullName.Substring(.Length + 1)
     = Join-Path  
     = Split-Path  -Parent
    if (-not (Test-Path )) { New-Item -ItemType Directory -Path  -Force | Out-Null }
    Copy-Item .FullName  -Force
}
`

## 完整性检查

`powershell
 = "D:\Projects\ai-photo-template-miniapp"
 = "E:\...\ai-photo-template-miniapp"  # 替换为实际路径

 = Get-ChildItem  -Recurse -File | Where-Object { \.DirectoryName -notmatch "node_modules|__pycache__|\.git" }
 = Get-ChildItem  -Recurse -File | Where-Object { \.DirectoryName -notmatch "node_modules|__pycache__|\.git" }

Write-Output "源: \0 | 目标: \0"
if (.Count -eq .Count) { Write-Output "一致" }
else { Write-Output "不一致" }
`

## 注意事项

- 百度网盘同步空间是单向同步，修改 D 盘文件后会自动上传
- .env 含密钥，已同步到百度网盘，注意不要公开分享
- node_modules 和 __pycache__ 不参与同步（体积大、可重新生成）
