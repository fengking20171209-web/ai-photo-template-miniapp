$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$envPath = Join-Path $root ".env"
$values = @{}

if (Test-Path $envPath) {
  Get-Content $envPath -Encoding utf8 | ForEach-Object {
    $line = $_.Trim()
    if (-not $line -or $line.StartsWith("#")) {
      return
    }

    $separator = $line.IndexOf("=")
    if ($separator -lt 0) {
      return
    }

    $key = $line.Substring(0, $separator).Trim()
    $value = $line.Substring($separator + 1).Trim().Trim('"').Trim("'")
    $values[$key] = $value
  }
}

$provider = if ($values.ContainsKey("AI_IMAGE_PROVIDER")) { $values["AI_IMAGE_PROVIDER"] } else { "mock" }
$dryRunValue = if ($values.ContainsKey("AI_IMAGE_DRY_RUN")) { $values["AI_IMAGE_DRY_RUN"] } else { "true" }
$dryRun = @("1", "true", "yes", "on") -contains $dryRunValue.ToLowerInvariant()
$apiUrl = if ($values.ContainsKey("AI_IMAGE_API_URL")) { $values["AI_IMAGE_API_URL"] } else { "" }
$apiKey = if ($values.ContainsKey("AI_IMAGE_API_KEY")) { $values["AI_IMAGE_API_KEY"] } else { "" }

$errors = New-Object System.Collections.Generic.List[string]

if ($provider -notin @("mock", "http")) {
  $errors.Add("AI_IMAGE_PROVIDER must be mock or http")
}

if (-not $dryRun -and $provider -eq "http" -and [string]::IsNullOrWhiteSpace($apiUrl)) {
  $errors.Add("AI_IMAGE_API_URL is required when AI_IMAGE_PROVIDER=http and AI_IMAGE_DRY_RUN=false")
}

if (-not $dryRun -and $provider -eq "http" -and [string]::IsNullOrWhiteSpace($apiKey)) {
  Write-Warning "AI_IMAGE_API_KEY is empty. This is only OK if your provider does not require a key."
}

$result = [ordered]@{
  env_file = $envPath
  env_file_exists = Test-Path $envPath
  provider = $provider
  dry_run = $dryRun
  api_url_set = -not [string]::IsNullOrWhiteSpace($apiUrl)
  api_key_set = -not [string]::IsNullOrWhiteSpace($apiKey)
  errors = @($errors)
}

$result | ConvertTo-Json -Depth 5

if ($errors.Count -gt 0) {
  exit 1
}
