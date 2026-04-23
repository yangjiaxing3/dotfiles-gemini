<#
.SYNOPSIS
  Gemini CLI BeforeTool Safety Hook
#>

if ($MyInvocation.ExpectingInput) {
    $inputJson = $input | Out-String
} else {
    $inputJson = [Console]::In.ReadToEnd()
}

try {
    $data = $inputJson | ConvertFrom-Json
    $command = ""
    if ($data.tool_input.command) { $command = $data.tool_input.command }
    elseif ($data.tool_input.CommandLine) { $command = $data.tool_input.CommandLine }
    elseif ($data.tool_input.content) { $command = $data.tool_input.content }
    elseif ($data.tool_input.new_string) { $command = $data.tool_input.new_string }
} catch {
    # Fail-Closed
    $fallbackResult = @{
        decision = "deny"
        reason = "Safety-Guard Blocked: Invalid JSON format. Fail-Closed triggered."
        systemMessage = "Safety Guard Rejected: Invalid format or payload. Fail-Closed protection triggered."
    } | ConvertTo-Json -Compress
    Write-Output $fallbackResult
    exit 0
}

$dangerousPatterns = @(
    'rm\s+-rf',
    'rmdir\s+/s',
    'Remove-Item.*-Recurse.*-Force',
    'del\s+/[fq]',
    'git\s+reset\s+--hard',
    'git\s+clean\s+-[fd]',
    'git\s+push\s+.*--force',
    'DROP\s+TABLE',
    'DROP\s+DATABASE',
    'DELETE\s+FROM\s+\w+\s*$',
    'TRUNCATE\s+TABLE',
    'curl.*(-d|--data).*[Aa][Pp][Ii][_-]?[Kk][Ee][Yy]',
    'Invoke-WebRequest.*-Body.*[Ss]ecret',
    'curl.*(-d|--data).*[Pp]assword',
    'Send-MailMessage',
    'sendmail',
    'npm\s+publish',
    'pip\s+upload',
    'twine\s+upload',
    'docker\s+push',
    'pip\s+install\s+(?!-r\s)',
    'Set-ExecutionPolicy\s+Unrestricted',
    'Format-Volume',
    'Clear-Disk'
)

$secretPatterns = @(
    '[Aa][Pp][Ii][_-]?[Kk][Ee][Yy]\s*[=:]\s*["\x27]?[A-Za-z0-9_\-]{20,}',
    '[Ss][Ee][Cc][Rr][Ee][Tt][_-]?[Kk][Ee][Yy]\s*[=:]\s*["\x27]?[A-Za-z0-9_\-]{20,}',
    '[Pp][Aa][Ss][Ss][Ww][Oo][Rr][Dd]\s*[=:]\s*["\x27]?[^\s"'']{8,}',
    'sk-[A-Za-z0-9]{20,}',
    'AIza[A-Za-z0-9_\-]{35}',
    'ghp_[A-Za-z0-9]{36}',
    'gho_[A-Za-z0-9]{36}',
    'AKIA[A-Z0-9]{16}'
)

$blocked = $false
$reason = ""

foreach ($pattern in $dangerousPatterns) {
    if ($command -match $pattern) {
        $blocked = $true
        $reason = "Dangerous command pattern detected: $pattern"
        break
    }
}

if (-not $blocked) {
    foreach ($pattern in $secretPatterns) {
        if ($command -match $pattern) {
            $blocked = $true
            $reason = "Secret leak detected: Possible API Key / Password"
            break
        }
    }
}

if ($blocked) {
    $result = @{
        decision = "deny"
        reason = $reason
        systemMessage = "Safety Guard Rejected: This operation is blocked. Please confirm with the user."
    } | ConvertTo-Json -Compress
    Write-Output $result
    exit 0
}

Write-Output '{}'
exit 0
