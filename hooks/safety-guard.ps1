<#
.SYNOPSIS
  Gemini CLI BeforeTool 安全攔截腳本
.DESCRIPTION
  偵測高風險 shell 指令並阻擋執行。
  只將 JSON 輸出到 stdout，除錯訊息寫入 stderr。
#>

# 從 stdin 讀取 JSON 輸入
$input = [Console]::In.ReadToEnd()

try {
    $data = $input | ConvertFrom-Json
    # 取得指令內容（相容不同 tool_input 結構）
    $command = ""
    if ($data.tool_input.command) { $command = $data.tool_input.command }
    elseif ($data.tool_input.CommandLine) { $command = $data.tool_input.CommandLine }
    elseif ($data.tool_input.content) { $command = $data.tool_input.content }
    elseif ($data.tool_input.new_string) { $command = $data.tool_input.new_string }
} catch {
    # 解析失敗，放行
    Write-Output '{}'
    exit 0
}

# === 危險指令模式清單 ===
$dangerousPatterns = @(
    # 破壞性刪除
    'rm\s+-rf',
    'rmdir\s+/s',
    'Remove-Item.*-Recurse.*-Force',
    'del\s+/[fq]',
    'git\s+reset\s+--hard',
    'git\s+clean\s+-[fd]',
    'git\s+push\s+.*--force',
    'DROP\s+TABLE',
    'DROP\s+DATABASE',
    'DELETE\s+FROM\s+\w+\s*$',  # DELETE 無 WHERE
    'TRUNCATE\s+TABLE',

    # 敏感資訊外洩
    'curl.*(-d|--data).*[Aa][Pp][Ii][_-]?[Kk][Ee][Yy]',
    'Invoke-WebRequest.*-Body.*[Ss]ecret',
    'curl.*(-d|--data).*[Pp]assword',

    # 外部通訊/發布
    'Send-MailMessage',
    'sendmail',
    'npm\s+publish',
    'pip\s+upload',
    'twine\s+upload',
    'docker\s+push',

    # 環境破壞
    'pip\s+install\s+(?!-r\s)',  # pip install 非 requirements.txt
    'Set-ExecutionPolicy\s+Unrestricted',
    'Format-Volume',
    'Clear-Disk'
)

# === 敏感內容偵測 ===
$secretPatterns = @(
    '[Aa][Pp][Ii][_-]?[Kk][Ee][Yy]\s*[=:]\s*["\x27]?[A-Za-z0-9_\-]{20,}',
    '[Ss][Ee][Cc][Rr][Ee][Tt][_-]?[Kk][Ee][Yy]\s*[=:]\s*["\x27]?[A-Za-z0-9_\-]{20,}',
    '[Pp][Aa][Ss][Ss][Ww][Oo][Rr][Dd]\s*[=:]\s*["\x27]?[^\s"'']{8,}',
    'sk-[A-Za-z0-9]{20,}',       # OpenAI API Key
    'AIza[A-Za-z0-9_\-]{35}',    # Google API Key
    'ghp_[A-Za-z0-9]{36}',       # GitHub Token
    'gho_[A-Za-z0-9]{36}',       # GitHub OAuth Token
    'AKIA[A-Z0-9]{16}'           # AWS Access Key
)

$blocked = $false
$reason = ""

# 檢查危險指令
foreach ($pattern in $dangerousPatterns) {
    if ($command -match $pattern) {
        $blocked = $true
        $reason = "危險指令偵測: 符合模式 [$pattern]"
        Write-Error "[safety-guard] BLOCKED: $command (pattern: $pattern)" 2>&1 | Out-Null
        break
    }
}

# 檢查敏感內容
if (-not $blocked) {
    foreach ($pattern in $secretPatterns) {
        if ($command -match $pattern) {
            $blocked = $true
            $reason = "敏感資訊偵測: 指令中可能包含 API Key / 密碼 / Token"
            Write-Error "[safety-guard] SECRET DETECTED in command" 2>&1 | Out-Null
            break
        }
    }
}

if ($blocked) {
    # 輸出 deny JSON 到 stdout
    $result = @{
        decision = "deny"
        reason = $reason
        systemMessage = "⚠️ 安全守衛攔截：此操作已被 safety-guard hook 阻止。請向使用者說明風險並取得明確授權後，再手動執行。"
    } | ConvertTo-Json -Compress
    Write-Output $result
    exit 0
}

# 放行
Write-Output '{}'
exit 0
