$customKey = [Environment]::GetEnvironmentVariable('PI_OPENAI_CUSTOM_API_KEY','User')
if (-not $customKey) { $customKey = [Environment]::GetEnvironmentVariable('PI_OPENAI_CUSTOM_API_KEY','Machine') }
if (-not $customKey) { throw 'PI_OPENAI_CUSTOM_API_KEY is missing' }
$env:PI_OPENAI_CUSTOM_API_KEY = $customKey
foreach ($v in @('OPENAI_API_KEY','ANTHROPIC_API_KEY','DEEPSEEK_API_KEY','DASHSCOPE_API_KEY','QWEN_API_KEY','XUNFEI_API_KEY','SENSENOVA_API_KEY','GBOX_API_KEY')) {
  Remove-Item "Env:$v" -ErrorAction SilentlyContinue
}
pi @args
