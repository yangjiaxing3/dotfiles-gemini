<#
.SYNOPSIS
  Gemini CLI BeforeTool Safety Hook
.NOTES
  無互動視窗 (CreateNoWindow) 呼叫 powershell.exe -File 時建議搭配 -InputFormat None，避免 PS 5.1 預設 Host 搶佔 stdin。
#>

try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
} catch {}
$OutputEncoding = [System.Text.Encoding]::UTF8

$inputJson = ""
if ($MyInvocation.ExpectingInput) {
    $inputJson = $input | Out-String
}
$isTopLevelScript = ((Get-PSCallStack).Count -le 1)
if ([string]::IsNullOrWhiteSpace($inputJson) -and $isTopLevelScript) {
    if ([Console]::IsInputRedirected) {
        $reader = New-Object System.IO.StreamReader([Console]::OpenStandardInput(), [System.Text.Encoding]::UTF8, $true)
        $inputJson = $reader.ReadToEnd()
    } elseif (-not $MyInvocation.ExpectingInput) {
        $inputJson = [Console]::In.ReadToEnd()
    }
}

function Get-InputPropertyValue {
    param(
        [object]$Obj,
        [string[]]$Names
    )
    if ($null -eq $Obj) { return "" }
    foreach ($name in $Names) {
        $prop = $Obj.PSObject.Properties | Where-Object { $_.Name -ceq $name } | Select-Object -First 1
        if ($null -eq $prop) {
            $prop = $Obj.PSObject.Properties | Where-Object { $_.Name -ieq $name } | Select-Object -First 1
        }
        if ($null -ne $prop -and $null -ne $prop.Value) {
            $val = [string]$prop.Value
            if ($val.Length -gt 0) {
                return $val
            }
        }
    }
    return ""
}

function Test-IsTestFileName {
    param([string]$FilePath)
    if ([string]::IsNullOrWhiteSpace($FilePath)) { return $false }
    $segments = @($FilePath.Trim() -split '[/\\]' | Where-Object { $_.Length -gt 0 })
    if ($segments.Count -eq 0) { return $false }
    $fileName = $segments[-1]
    if ($fileName -imatch '^(test_.*\.py|.*_test\.py|.+\.test\..+|.+\.spec\..+)$') {
        return $true
    }
    if ($segments.Count -ge 2 -and ($fileName -imatch '\.(py|ts|tsx|js|jsx)$')) {
        $dirSegments = $segments[0..($segments.Count - 2)]
        foreach ($seg in $dirSegments) {
            if ($seg -imatch '^(__tests__|tests)$') {
                return $true
            }
        }
    }
    return $false
}

try {
    if ([string]::IsNullOrWhiteSpace($inputJson)) {
        throw "Empty JSON payload."
    }
    $data = $inputJson | ConvertFrom-Json -ErrorAction Stop
    if ($null -eq $data) {
        throw "Parsed JSON payload is null."
    }
    $toolInput = $null
    if ($data.PSObject.Properties['tool_input']) {
        $toolInput = $data.tool_input
    }
    $targetPath = Get-InputPropertyValue -Obj $toolInput -Names @('path', 'Path', 'file_path', 'TargetFile')
    $writeContent = Get-InputPropertyValue -Obj $toolInput -Names @('content', 'new_string', 'Replacement')
    $shellCmd = Get-InputPropertyValue -Obj $toolInput -Names @('command', 'CommandLine')
    $command = Get-InputPropertyValue -Obj $toolInput -Names @('command', 'CommandLine', 'content', 'new_string', 'Replacement')
} catch {
    # Fail-Closed
    $failHint = "請傳入合法的 JSON 格式 tool_input payload 物件後重試。"
    $fallbackResult = @{
        decision = "deny"
        reason = "Safety-Guard Blocked: Invalid JSON format. Fail-Closed triggered. 修復指引: $failHint"
        systemMessage = "Safety Guard Rejected: Invalid format or payload. Fail-Closed protection triggered. 修復指引: $failHint"
    } | ConvertTo-Json -Compress
    Write-Output $fallbackResult
    exit 0
}

$deleteFixHint = "請確認刪除目標路徑範圍非專案根目錄或系統目錄（建議先檢視檔案清單），並取得使用者明確授權。"
$gitFixHint = "請確認目標分支與變更影響範圍（可改用 git stash 或 --force-with-lease），並取得使用者明確授權。"
$sqlFixHint = "請確認目標資料庫與資料表範圍並先完成備份（DELETE 請補上 WHERE 條件），並取得使用者明確授權。"
$exfilFixHint = "請勿透過指令行傳送明文金鑰或密碼，改由伺服器環境變數或 Windows DPAPI (%LOCALAPPDATA%\US3C\Secrets\) 讀取並確認端點合法性。"
$publishFixHint = "對外發信或公開發布套件／映像屬不可逆外部影響，請確認目標版本、收件人與倉庫位置並取得使用者明確授權。"
$pipFixHint = "請改用專案虛擬環境 .venv\Scripts\pip.exe install，或透過 pip install -r requirements.txt 安裝以鎖定依賴。"
$systemFixHint = "請改用最小權限範圍（如 -ExecutionPolicy Bypass -Scope Process）或先確認目標磁碟並取得使用者明確授權。"
$secretFixHint = "嚴禁明文硬編碼或傳輸密鑰／密碼，請改存於 Windows DPAPI (%LOCALAPPDATA%\US3C\Secrets\) 或改由環境變數讀取。"
$testCheatFixHint = "請修復商業邏輯或測試 fixture，嚴禁跳過斷言。"

$dangerousRules = @(
    @{ Pattern = 'rm\s+-rf'; Category = 'Destructive Delete'; FixHint = $deleteFixHint },
    @{ Pattern = 'rmdir\s+/s'; Category = 'Destructive Delete'; FixHint = $deleteFixHint },
    @{ Pattern = 'Remove-Item.*-Recurse.*-Force'; Category = 'Destructive Delete'; FixHint = $deleteFixHint },
    @{ Pattern = 'del\s+/[fq]'; Category = 'Destructive Delete'; FixHint = $deleteFixHint },
    @{ Pattern = 'git\s+reset\s+--hard'; Category = 'Destructive Git'; FixHint = $gitFixHint },
    @{ Pattern = 'git\s+clean\s+-[fd]'; Category = 'Destructive Git'; FixHint = $gitFixHint },
    @{ Pattern = 'git\s+push\s+.*--force'; Category = 'Destructive Git'; FixHint = $gitFixHint },
    @{ Pattern = 'DROP\s+TABLE'; Category = 'Destructive SQL'; FixHint = $sqlFixHint },
    @{ Pattern = 'DROP\s+DATABASE'; Category = 'Destructive SQL'; FixHint = $sqlFixHint },
    @{ Pattern = 'DELETE\s+FROM\s+\w+\s*$'; Category = 'Destructive SQL'; FixHint = $sqlFixHint },
    @{ Pattern = 'TRUNCATE\s+TABLE'; Category = 'Destructive SQL'; FixHint = $sqlFixHint },
    @{ Pattern = 'curl.*(-d|--data).*[Aa][Pp][Ii][_-]?[Kk][Ee][Yy]'; Category = 'Credential Exfiltration'; FixHint = $exfilFixHint },
    @{ Pattern = 'Invoke-WebRequest.*-Body.*[Ss]ecret'; Category = 'Credential Exfiltration'; FixHint = $exfilFixHint },
    @{ Pattern = 'curl.*(-d|--data).*[Pp]assword'; Category = 'Credential Exfiltration'; FixHint = $exfilFixHint },
    @{ Pattern = 'Send-MailMessage'; Category = 'External Dispatch'; FixHint = $publishFixHint },
    @{ Pattern = 'sendmail'; Category = 'External Dispatch'; FixHint = $publishFixHint },
    @{ Pattern = 'npm\s+publish'; Category = 'External Publish'; FixHint = $publishFixHint },
    @{ Pattern = 'pip\s+upload'; Category = 'External Publish'; FixHint = $publishFixHint },
    @{ Pattern = 'twine\s+upload'; Category = 'External Publish'; FixHint = $publishFixHint },
    @{ Pattern = 'docker\s+push'; Category = 'External Publish'; FixHint = $publishFixHint },
    @{ Pattern = '(?:^|\s)pip3?\s+install\s+(?!-r\s*)'; Category = 'Unmanaged Pip Install'; FixHint = $pipFixHint },
    @{ Pattern = 'Set-ExecutionPolicy\s+Unrestricted'; Category = 'System Policy'; FixHint = $systemFixHint },
    @{ Pattern = 'Format-Volume'; Category = 'Disk Wipe'; FixHint = $systemFixHint },
    @{ Pattern = 'Clear-Disk'; Category = 'Disk Wipe'; FixHint = $systemFixHint }
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

$testCheatPatterns = @(
    '\.skip\s*\(',
    'pytest\.mark\.skip',
    '@unittest\.skip'
)

$blocked = $false
$reason = ""
$systemMessage = ""

foreach ($rule in $dangerousRules) {
    if ($command -match $rule.Pattern) {
        $blocked = $true
        $reason = "Dangerous command pattern detected ($($rule.Category)): $($rule.Pattern). 修復指引: $($rule.FixHint)"
        $systemMessage = "Safety Guard Rejected ($($rule.Category)): $($rule.FixHint)"
        break
    }
}

if (-not $blocked) {
    foreach ($pattern in $secretPatterns) {
        if ($command -match $pattern) {
            $blocked = $true
            $reason = "Secret leak detected: Possible API Key / Password. 修復指引: $secretFixHint"
            $systemMessage = "Safety Guard Rejected (Secret Leak): $secretFixHint"
            break
        }
    }
}

if (-not $blocked -and (Test-IsTestFileName -FilePath $targetPath) -and ($writeContent.Length -gt 0)) {
    foreach ($pattern in $testCheatPatterns) {
        if ($writeContent -cmatch $pattern) {
            $blocked = $true
            $fileName = ($targetPath.Trim() -split '[/\\]')[-1]
            $reason = "Test cheating detected in '$fileName': matched '$pattern'. 修復指引: $testCheatFixHint"
            $systemMessage = "Safety Guard Rejected (Test Cheating): $testCheatFixHint"
            break
        }
    }
}

if (-not $blocked -and $shellCmd.Length -gt 0) {
    $commitMatches = [regex]::Matches(
        $shellCmd,
        '(?:^|[;&|\r\n]\s*)git(?:\.exe)?((?:\s+(?:-C\s+(?:"[^"]+"|''[^'']+''|\S+)|-c\s+(?:"[^"]+"|''[^'']+''|\S+)|--no-pager|--bare|--git-dir=\S+|--work-tree=\S+))*)\s+commit\b([^\r\n;&|]*)',
        [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
    )
    $lintScript = Join-Path $HOME ".gemini\scripts\rule_lint.py"
    foreach ($commitMatch in $commitMatches) {
        $globalOpts = $commitMatch.Groups[1].Value
        $commitTail = $commitMatch.Groups[2].Value
        $commitTailNoMsg = [regex]::Replace(
            $commitTail,
            '(?i)(?:^|\s)(?:-m|--message)(?:\s+|=)(?:"(?:\\.|[^"])*"|''[^'']*'')',
            ' '
        )
        if ($commitTailNoMsg -match '(?i)(?:^|\s)(?:--help|-h)(?:\s|$)') {
            continue
        }

        $candidateDir = ""
        $cMatches = [regex]::Matches($globalOpts, '\s-C\s+(?:"([^"]+)"|''([^'']+)''|(\S+))')
        if ($cMatches.Count -gt 0) {
            $lastC = $cMatches[$cMatches.Count - 1]
            if ($lastC.Groups[1].Success) { $candidateDir = $lastC.Groups[1].Value }
            elseif ($lastC.Groups[2].Success) { $candidateDir = $lastC.Groups[2].Value }
            elseif ($lastC.Groups[3].Success) { $candidateDir = $lastC.Groups[3].Value }
        }
        if ([string]::IsNullOrWhiteSpace($candidateDir)) {
            $candidateDir = Get-InputPropertyValue -Obj $toolInput -Names @('cwd', 'Cwd', 'WorkingDirectory')
        }
        if ([string]::IsNullOrWhiteSpace($candidateDir)) {
            $candidateDir = (Get-Location).Path
        }
        $candidateDir = $candidateDir.Trim()

        $repoDir = ""
        if (-not [string]::IsNullOrWhiteSpace($candidateDir)) {
            try {
                $resolvedTop = (& git -C $candidateDir rev-parse --show-toplevel 2>$null | Out-String).Trim()
                if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($resolvedTop)) {
                    $repoDir = $resolvedTop
                }
            } catch {
                $repoDir = ""
            }
        }

        if (-not [string]::IsNullOrWhiteSpace($repoDir) -and (Test-Path -LiteralPath $lintScript)) {
            $hasCommitAll = ($commitTailNoMsg -cmatch '(?:^|\s)-(?:[a-zA-Z]*a[a-zA-Z]*|-all)(?:\s|$)')
            $hasBulkGitAdd = ($shellCmd -imatch '(?:^|[;&|\r\n]\s*)git(?:\.exe)?(?:\s+-C\s+(?:"[^"]+"|''[^'']+''|\S+))?\s+add\s+(?:[^\r\n;&|]*\s)?(?:-A|--all|-u|\.(?:\s|$|[;&|]))')
            $useWorkingTreeDiff = $hasCommitAll -or $hasBulkGitAdd
            $lintArgs = if ($useWorkingTreeDiff) {
                @($lintScript, "--git-diff", "--repo", $repoDir, "--format", "json")
            } else {
                @($lintScript, "--git-diff", "--staged", "--repo", $repoDir, "--format", "json")
            }
            $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
            if ($null -eq $pythonCmd) {
                $pythonCmd = Get-Command python3 -ErrorAction SilentlyContinue
            }
            $ruleLintFixHint = "請先修正違規並執行 python scripts/rule_lint.py --git-diff 確認 0 errors 後再提交。"
            if ($null -eq $pythonCmd) {
                $blocked = $true
                $reason = "Rule-Lint Gate Blocked: Python runtime not found. 修復指引: $ruleLintFixHint"
                $systemMessage = "Rule-Lint Gate Rejected: Python runtime not found. 修復指引: $ruleLintFixHint"
                break
            }
            $prevEncoding = $env:PYTHONIOENCODING
            $env:PYTHONIOENCODING = "utf-8"
            try {
                $lintOut = & $pythonCmd.Source @lintArgs 2>&1 | Out-String
                $lintExit = $LASTEXITCODE
            } finally {
                if ($null -eq $prevEncoding) {
                    Remove-Item Env:PYTHONIOENCODING -ErrorAction SilentlyContinue
                } else {
                    $env:PYTHONIOENCODING = $prevEncoding
                }
            }
            if ($lintExit -ne 0) {
                $summaryParts = @()
                $errCount = 1
                try {
                    $lintReport = $lintOut.Trim() | ConvertFrom-Json -ErrorAction Stop
                    if ($lintReport.error_count) { $errCount = [int]$lintReport.error_count }
                    if ($lintReport.violations) {
                        $summaryParts = @(
                            $lintReport.violations | Select-Object -First 3 | ForEach-Object {
                                "[$($_.rule_id)] $($_.file):$($_.line)"
                            }
                        )
                    } elseif ($lintReport.error) {
                        $summaryParts = @([string]$lintReport.error)
                    }
                } catch {
                    # JSON 解析失敗或 tool exception (exit=2) 時仍強制攔截提交
                    $summaryParts = @("exit=$lintExit")
                }
                $summaryText = if ($summaryParts.Count -gt 0) { $summaryParts -join "; " } else { "rule_lint failed (exit=$lintExit)" }
                $blocked = $true
                $reason = "Rule-Lint Gate Blocked ($errCount errors): $summaryText. 修復指引: $ruleLintFixHint"
                $systemMessage = "Rule-Lint Gate Rejected ($errCount errors): $summaryText. 修復指引: $ruleLintFixHint"
                break
            }
        }
    }
}

if ($blocked) {
    $result = @{
        decision = "deny"
        reason = $reason
        systemMessage = $systemMessage
    } | ConvertTo-Json -Compress
    Write-Output $result
    exit 0
}

Write-Output '{}'
exit 0
