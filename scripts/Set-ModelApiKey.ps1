param(
  [Parameter(Mandatory=$true)]
  [ValidateSet('OPENROUTER_API_KEY','DEEPSEEK_API_KEY','XAI_API_KEY','QWEN_API_KEY','GEMINI_API_KEY','TYPESAFE_API_KEY','OPENAI_API_KEY')]
  [string]$Name
)
$ErrorActionPreference = 'Stop'
$vaultPath = Join-Path $PSScriptRoot 'multi-model-keys.dpapi.xml'
$secureKey = Read-Host -Prompt "輸入 $Name（隱藏輸入，不會寫入命令歷史）" -AsSecureString
$plainKey = [Net.NetworkCredential]::new('', $secureKey).Password
if ([string]::IsNullOrWhiteSpace($plainKey) -or $plainKey.Contains("`n") -or $plainKey.Contains("`r")) { throw '金鑰不可為空或包含換行' }
$text = if(Test-Path -LiteralPath $vaultPath){[Net.NetworkCredential]::new('',(Import-Clixml -LiteralPath $vaultPath)).Password}else{''}
$lines = @($text -split '\r?\n' | Where-Object { $_ -notmatch ('^\s*' + [regex]::Escape($Name) + '\s*=') })
$newText = (($lines + "$Name=$plainKey") -join "`n")
$tempPath = Join-Path $PSScriptRoot ([guid]::NewGuid().ToString('N') + '.dpapi.xml')
ConvertTo-SecureString -String $newText -AsPlainText -Force | Export-Clixml -LiteralPath $tempPath
$verified = [Net.NetworkCredential]::new('',(Import-Clixml -LiteralPath $tempPath)).Password
if ($verified -cne $newText) { throw '加密驗證失敗；原金鑰庫未更改' }
if(Test-Path -LiteralPath $vaultPath){[IO.File]::Replace($tempPath,$vaultPath,$null)}else{[IO.File]::Move($tempPath,$vaultPath)}
# 自動同步至標準 %LOCALAPPDATA% 與 Codex MSIX 沙盒路徑，避免沙盒虛擬化造成金鑰不同步
$canonicalDir = Join-Path $env:USERPROFILE 'AppData\Local\US3C\Secrets'
if ($PSScriptRoot -ne $canonicalDir) {
  New-Item -ItemType Directory -Path $canonicalDir -Force | Out-Null
  Copy-Item -LiteralPath $vaultPath -Destination (Join-Path $canonicalDir 'multi-model-keys.dpapi.xml') -Force
}
$pkgsDir = Join-Path $env:USERPROFILE 'AppData\Local\Packages'
if (Test-Path -LiteralPath $pkgsDir) {
  Get-ChildItem -Path $pkgsDir -Filter 'OpenAI.Codex_*' -Directory -ErrorAction SilentlyContinue | ForEach-Object {
    $msixSecretDir = Join-Path $_.FullName 'LocalCache\Local\US3C\Secrets'
    if ((Test-Path -LiteralPath $msixSecretDir) -and ($PSScriptRoot -ne $msixSecretDir)) {
      Copy-Item -LiteralPath $vaultPath -Destination (Join-Path $msixSecretDir 'multi-model-keys.dpapi.xml') -Force
    }
  }
}
$plainKey=$null; $text=$null; $newText=$null; $verified=$null
Write-Output "$Name 已存入 Windows DPAPI 金鑰庫（已同步標準路徑與 MSIX 沙盒路徑）。"
