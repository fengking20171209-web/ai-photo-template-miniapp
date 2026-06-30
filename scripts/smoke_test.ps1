param(
  [string]$TemplateId = ""
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$templatesDir = Join-Path $root "templates"
$outputDir = Join-Path $root "output\test-runs"

New-Item -ItemType Directory -Force -Path $outputDir | Out-Null

$requiredTop = @(
  "template_id",
  "category",
  "title",
  "version",
  "ratio",
  "face_lock",
  "style",
  "scene",
  "clothing",
  "prompt_blocks",
  "options",
  "negative_prompt"
)

$requiredBlocks = @(
  "subject",
  "face",
  "clothing",
  "scene",
  "lighting",
  "camera",
  "quality",
  "commercial_use"
)

$allowedCategories = @'
[
  "\u53e4\u98ce\u7f8e\u5973",
  "\u804c\u4e1a\u5f62\u8c61",
  "\u5f62\u8c61\u5206\u6790",
  "\u6f2b\u753b\u89d2\u8272",
  "\u4ea7\u54c1\u6d77\u62a5",
  "\u6a21\u7279\u5927\u8d5b"
]
'@ | ConvertFrom-Json
$allowedQuality = @("draft", "standard", "high")
$results = @()
$seenIds = @{}

$templateFiles = Get-ChildItem $templatesDir -Filter "*.json" | Sort-Object Name
if (-not [string]::IsNullOrWhiteSpace($TemplateId)) {
  $templateFiles = @($templateFiles | Where-Object { [System.IO.Path]::GetFileNameWithoutExtension($_.Name) -eq $TemplateId })
  if ($templateFiles.Count -eq 0) {
    throw "Template not found: $TemplateId"
  }
}

$templateFiles | ForEach-Object {
  $errors = New-Object System.Collections.Generic.List[string]
  $template = Get-Content $_.FullName -Raw -Encoding utf8 | ConvertFrom-Json
  $templateIdFromFile = [System.IO.Path]::GetFileNameWithoutExtension($_.Name)

  foreach ($key in $requiredTop) {
    if (-not ($template.PSObject.Properties.Name -contains $key)) {
      $errors.Add("missing $key")
    }
  }

  foreach ($key in $requiredBlocks) {
    if (-not $template.prompt_blocks -or -not ($template.prompt_blocks.PSObject.Properties.Name -contains $key) -or [string]::IsNullOrWhiteSpace($template.prompt_blocks.$key)) {
      $errors.Add("missing prompt_blocks.$key")
    }
  }

  if ($template.template_id -ne $templateIdFromFile) {
    $errors.Add("template_id must match file name")
  }

  if ($seenIds.ContainsKey($template.template_id)) {
    $errors.Add("duplicate template_id: $($template.template_id)")
  } else {
    $seenIds[$template.template_id] = $true
  }

  if ($template.category -notin $allowedCategories) {
    $errors.Add("unsupported category: $($template.category)")
  }

  if ($template.options.quality -notin $allowedQuality) {
    $errors.Add("unsupported quality: $($template.options.quality)")
  }

  if ($template.options.face_strength -lt 0 -or $template.options.face_strength -gt 1) {
    $errors.Add("face_strength must be between 0 and 1")
  }

  if ($template.options.output_count -lt 1 -or $template.options.output_count -gt 9) {
    $errors.Add("output_count must be between 1 and 9")
  }

  if (-not $template.negative_prompt -or $template.negative_prompt.Count -eq 0) {
    $errors.Add("negative_prompt must not be empty")
  }

  $negativePrompt = ($template.negative_prompt -join ", ")
  $blocks = $template.prompt_blocks
  $prompt = @"
【模板名称】
$($template.title)

【分类】
$($template.category)

【画幅】
$($template.ratio)

【风格】
$($template.style)

【生成目标】
$($blocks.subject)

【脸部保真】
$($blocks.face)

【服装造型】
$($blocks.clothing)

【场景环境】
$($blocks.scene)

【光影氛围】
$($blocks.lighting)

【镜头构图】
$($blocks.camera)

【画质要求】
$($blocks.quality)

【商业用途】
$($blocks.commercial_use)

【安全与品质要求】
保留用户真实五官、脸型、肤色，不要过度磨皮，不要低俗，不要裸露，不要生成夸张身体比例，服装完整得体，整体高级、干净、商业可用。

【负面提示】
$negativePrompt
"@.Trim()

  $task = [ordered]@{
    task_id = "test_$($template.template_id)"
    status = $(if ($errors.Count -eq 0) { "completed" } else { "failed" })
    template = [ordered]@{
      template_id = $template.template_id
      category = $template.category
      title = $template.title
      ratio = $template.ratio
      style = $template.style
    }
    image_request = [ordered]@{
      provider = "mock"
      dry_run = $true
      request_body = [ordered]@{
        prompt = $prompt
        negative_prompt = $negativePrompt
        ratio = $template.ratio
        quality = $template.options.quality
        face_strength = $template.options.face_strength
        output_count = $template.options.output_count
      }
    }
    image_response = [ordered]@{
      provider_task_id = "mock_$($template.template_id)"
      image_urls = @()
      raw = [ordered]@{
        mode = "mock"
        message = "No real image API was called."
      }
    }
    errors = @($errors)
  }

  $taskPath = Join-Path $outputDir "$($template.template_id).json"
  $task | ConvertTo-Json -Depth 10 | Set-Content -Path $taskPath -Encoding utf8

  $results += [ordered]@{
    file = $_.Name
    template_id = $template.template_id
    status = $task.status
    errors = $errors.Count
    prompt_chars = $prompt.Length
  }
}

$summary = [ordered]@{
  total = $results.Count
  passed = @($results | Where-Object { $_.status -eq "completed" }).Count
  failed = @($results | Where-Object { $_.status -ne "completed" }).Count
  results = $results
}

$summaryPath = Join-Path $outputDir "summary.json"
$summary | ConvertTo-Json -Depth 10 | Set-Content -Path $summaryPath -Encoding utf8

$summary | ConvertTo-Json -Depth 10

if ($summary.failed -gt 0) {
  exit 1
}
