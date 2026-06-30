# Network Optimization Notes

## What Was Slow

The local checks found three separate causes:

- Windows system proxy is disabled.
- Git is configured to use `schannel`, and `curl` / Git can hit `SEC_E_NO_CREDENTIALS` TLS errors.
- The workspace is inside a Baidu Netdisk sync directory, so clone, unzip, and many-small-file writes can be slowed by sync scanning.

## Fastest GitHub Route Found

The local proxy process is running through `v2rayN` / `sing-box`.

Detected useful local port:

```text
127.0.0.1:10808
```

Measured GitHub request speed:

| Mode | Result |
| --- | --- |
| Direct GitHub route | unstable, one lightweight request took about 61 seconds |
| `socks5h://127.0.0.1:10808` | about 2.9 seconds |
| `http://127.0.0.1:10808` | about 6.8 seconds |
| `socks5h://127.0.0.1:10813` | timed out |

Recommended Git options:

```powershell
git -c http.sslbackend=openssl -c http.proxy=socks5h://127.0.0.1:10808 clone <repo-url>
```

## Recommended Daily Setup

For one terminal session:

```powershell
$env:GIT_PROXY = "socks5h://127.0.0.1:10808"
```

Then use project scripts that read `GIT_PROXY`.

For one Git command:

```powershell
git -c http.sslbackend=openssl -c http.proxy=socks5h://127.0.0.1:10808 ls-remote https://github.com/ZeroLu/awesome-gpt-image.git
```

## Optional Global Git Setup

Only do this if you want all GitHub downloads on this machine to go through the local proxy:

```powershell
git config --global http.sslBackend openssl
git config --global http.proxy socks5h://127.0.0.1:10808
```

To undo:

```powershell
git config --global --unset http.proxy
git config --global --unset http.sslBackend
```

## Workspace Speed

Current workspace is under:

```text
BaiduNetdiskDownload/百度网盘同步文件/BaiduSyncdisk
```

For faster development:

- Keep the active code workspace in a normal local folder, such as `D:\Projects`.
- Sync only exported deliverables or backups to Baidu Netdisk.
- If staying in the sync folder, pause Baidu Netdisk sync before large clone, unzip, install, or build tasks.
