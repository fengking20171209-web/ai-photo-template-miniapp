---
name: kimi-photo-template-tools
description: Tools for the AI photo template miniapp. Use when you need to list templates, validate template JSON files, check image API environment settings, or regenerate the template catalog.
---

# Kimi Photo Template Tools

This plugin provides local tools for `D:\Projects\ai-photo-template-miniapp`.

Available tools:

- `list_templates`: list `templates/*.json`
- `smoke_test_templates`: validate template structure and mock image task payloads
- `check_image_env`: inspect `.env` image API settings without exposing secrets
- `generate_template_catalog`: regenerate `docs/template_catalog.md`

Default behavior is safe:

- no real image API calls
- no API keys printed
- no destructive file operations

Use these tools together with the project skill:

- `/skill:ai-photo-template-workflow`
