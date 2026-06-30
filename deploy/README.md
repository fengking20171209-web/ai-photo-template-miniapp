# Tencent Cloud Deployment

Current target:

```text
SSH alias: tencent-audiobook-ts
App dir: /opt/ai-photo-template-miniapp
Tailscale URL: http://100.92.38.117:3200/
Service: ai-photo-template-miniapp.service
```

## Deploy

From the local project root:

```powershell
powershell -ExecutionPolicy Bypass -File deploy\deploy-tencent.ps1
```

The script:

- builds a small tarball from source files
- uploads it to Tencent Cloud
- creates a timestamped release under `/opt/ai-photo-template-miniapp/releases`
- runs `npm ci`
- updates `/opt/ai-photo-template-miniapp/current`
- writes `/opt/ai-photo-template-miniapp/shared/env`
- installs/restarts the systemd service
- checks `/health`

## Server Commands

```bash
sudo systemctl status ai-photo-template-miniapp.service --no-pager -l
sudo systemctl restart ai-photo-template-miniapp.service
sudo journalctl -u ai-photo-template-miniapp.service -n 100 --no-pager
```

## Safety Notes

- Current deployment is Tailscale-only on `100.92.38.117:3200`.
- Do not touch existing Docker services on ports 80/443 until reverse proxy ownership is confirmed.
- Default image generation mode is mock:

```text
AI_IMAGE_PROVIDER=mock
AI_IMAGE_DRY_RUN=true
```

## Hermes Watch Report

The first server watch report was saved locally:

```text
output/hermes-reports/ai-photo-template-miniapp-watch.md
```
