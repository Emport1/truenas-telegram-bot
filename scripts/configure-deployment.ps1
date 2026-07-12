$ErrorActionPreference = 'Stop'

function Read-Secret([string]$Prompt) {
    $secure = Read-Host $Prompt -AsSecureString
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try {
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
    }
}

$userId = (Read-Host 'Your numeric Telegram user ID').Trim()
if ($userId -notmatch '^\d+$') {
    throw 'Telegram user ID must contain digits only.'
}

$telegramToken = Read-Secret 'Telegram bot token (input is hidden)'
$authToken = Read-Secret 'X auth_token cookie value (input is hidden)'
$ct0 = Read-Secret 'X ct0 cookie value (input is hidden)'

foreach ($entry in @(
    @{ Name = 'Telegram token'; Value = $telegramToken },
    @{ Name = 'X auth_token'; Value = $authToken },
    @{ Name = 'X ct0'; Value = $ct0 }
)) {
    if ([string]::IsNullOrWhiteSpace($entry.Value)) {
        throw "$($entry.Name) cannot be empty."
    }
    if ($entry.Value -match '[\x00-\x1F\x7F"\\]') {
        throw "$($entry.Name) contains a character that cannot be placed safely in this YAML."
    }
}

if ($telegramToken -notmatch '^\d+:[A-Za-z0-9_-]+$') {
    throw 'Telegram token has an invalid format. In Windows PowerShell, paste hidden input with right-click or Ctrl+Shift+V, not plain Ctrl+V.'
}
if ($authToken -notmatch '^[A-Za-z0-9_-]+$' -or $ct0 -notmatch '^[A-Za-z0-9_-]+$') {
    throw 'An X cookie has an invalid format. Copy only the cookie Value and paste with right-click or Ctrl+Shift+V.'
}

$root = Split-Path -Parent $PSScriptRoot
$template = Get-Content -LiteralPath (Join-Path $root 'truenas-compose.yaml') -Raw
$configured = $template.Replace('REPLACE_TELEGRAM_TOKEN', $telegramToken)
$configured = $configured.Replace('REPLACE_NUMERIC_USER_ID', $userId)
$configured = $configured.Replace('REPLACE_X_AUTH_TOKEN_COOKIE', $authToken)
$configured = $configured.Replace('REPLACE_X_CT0_COOKIE', $ct0)
$destination = Join-Path $root 'truenas-compose.private.yaml'
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[IO.File]::WriteAllText($destination, $configured, $utf8NoBom)

$telegramToken = $authToken = $ct0 = $configured = $null
Write-Host "Created $destination"
Write-Host 'This file contains live credentials and is excluded from Git.'
