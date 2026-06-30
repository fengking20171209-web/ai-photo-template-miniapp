$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$templatesDir = Join-Path $root "templates"

Get-ChildItem $templatesDir -Filter "*.json" | Sort-Object Name | ForEach-Object {
  $template = Get-Content $_.FullName -Raw -Encoding utf8 | ConvertFrom-Json

  [pscustomobject]@{
    template_id = $template.template_id
    category = $template.category
    title = $template.title
    ratio = $template.ratio
    style = $template.style
    quality = $template.options.quality
    face_strength = $template.options.face_strength
  }
} | Format-Table -AutoSize
