# ============================================================================
# Railway Environment Setup Wizard
# Project 38 - Zero-Touch Configuration
# ============================================================================
# This script automates the entire environment setup process:
# 1. Auto-generates secure passwords (POSTGRES, REDIS, SECRET_KEY)
# 2. Interactively requests LLM API keys from user
# 3. Creates .env.production with all values
# 4. Optionally chains to deploy_railway.ps1
#
# Usage: .\setup_env.ps1
# Requirements: openssl (for password generation) OR PowerShell 5.1+
# ============================================================================

param(
    [switch]$SkipDeploy,
    [switch]$RegenerateAll,
    [string]$EnvFile = "infrastructure\.env.production"
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# ============================================================================
# ANSI Colors for Output
# ============================================================================
function Write-Success { param($Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Info { param($Message) Write-Host "ℹ️  $Message" -ForegroundColor Cyan }
function Write-Warning { param($Message) Write-Host "⚠️  $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "❌ $Message" -ForegroundColor Red }
function Write-Step { param($Step, $Message) Write-Host "`n[$Step] $Message" -ForegroundColor Magenta }
function Write-Secret { param($Message) Write-Host "🔐 $Message" -ForegroundColor Yellow }

# ============================================================================
# Password Generation Functions
# ============================================================================
function Test-OpensslAvailable {
    try {
        $null = openssl version 2>$null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

function New-SecurePassword {
    param(
        [int]$Length = 32,
        [string]$Type = "base64"  # base64 or hex
    )
    
    # Try openssl first (preferred)
    if (Test-OpensslAvailable) {
        try {
            if ($Type -eq "hex") {
                $password = openssl rand -hex ($Length / 2) 2>$null
            } else {
                $password = openssl rand -base64 $Length 2>$null
                $password = $password -replace "`n", "" -replace "`r", ""
                $password = $password.Substring(0, [Math]::Min($Length, $password.Length))
            }
            
            if ($LASTEXITCODE -eq 0 -and $password) {
                return $password.Trim()
            }
        } catch {
            Write-Warning "openssl failed, falling back to PowerShell RNG"
        }
    }
    
    # Fallback: PowerShell SecureRandom
    $bytes = New-Object byte[] ($Length)
    $rng = [System.Security.Cryptography.RNGCryptoServiceProvider]::new()
    $rng.GetBytes($bytes)
    
    if ($Type -eq "hex") {
        return ($bytes | ForEach-Object { $_.ToString("x2") }) -join ""
    } else {
        $base64 = [Convert]::ToBase64String($bytes)
        return ($base64 -replace '[/+=]', '').Substring(0, [Math]::Min($Length, $base64.Length))
    }
}

# ============================================================================
# Input Validation
# ============================================================================
function Test-ApiKey {
    param([string]$Key, [string]$Provider)
    
    if ([string]::IsNullOrWhiteSpace($Key)) {
        return $false
    }
    
    switch ($Provider) {
        "OpenAI" { return $Key -match '^sk-[A-Za-z0-9]{32,}$' }
        "Anthropic" { return $Key -match '^sk-ant-[A-Za-z0-9\-]{90,}$' }
        default { return $Key.Length -gt 10 }
    }
}

# ============================================================================
# STEP 1: Welcome
# ============================================================================
function Show-Welcome {
    Write-Host ""
    Write-Host "=============================================" -ForegroundColor Magenta
    Write-Host "  Railway Environment Setup Wizard" -ForegroundColor Magenta
    Write-Host "  Project 38 - Zero-Touch Configuration" -ForegroundColor Magenta
    Write-Host "=============================================" -ForegroundColor Magenta
    Write-Host ""
    
    Write-Info "This wizard will:"
    Write-Host "  1. Generate secure passwords automatically" -ForegroundColor White
    Write-Host "  2. Request your LLM API key(s)" -ForegroundColor White
    Write-Host "  3. Create .env.production file" -ForegroundColor White
    Write-Host "  4. Optionally deploy to Railway" -ForegroundColor White
    Write-Host ""
    
    if (Test-Path $EnvFile -and -not $RegenerateAll) {
        Write-Warning "Environment file already exists: $EnvFile"
        $response = Read-Host "Overwrite existing file? (y/N)"
        if ($response -ne "y" -and $response -ne "Y") {
            Write-Info "Setup cancelled by user"
            exit 0
        }
    }
}

# ============================================================================
# STEP 2: Generate Passwords
# ============================================================================
function New-DatabasePasswords {
    Write-Step "1/3" "Generating Secure Passwords"
    
    if (Test-OpensslAvailable) {
        Write-Success "openssl available - using cryptographically secure RNG"
    } else {
        Write-Warning "openssl not found - using PowerShell SecureRandom"
    }
    
    Write-Host ""
    Write-Secret "Generating passwords..."
    
    $passwords = @{
        POSTGRES_USER = "dify"
        POSTGRES_DB = "dify"
        POSTGRES_PASSWORD = New-SecurePassword -Length 32 -Type "base64"
        REDIS_PASSWORD = New-SecurePassword -Length 32 -Type "base64"
        SECRET_KEY = New-SecurePassword -Length 64 -Type "hex"
    }
    
    foreach ($key in @("POSTGRES_PASSWORD", "REDIS_PASSWORD", "SECRET_KEY")) {
        if ([string]::IsNullOrWhiteSpace($passwords[$key])) {
            Write-Error "Failed to generate $key"
            exit 1
        }
    }
    
    Write-Success "Generated 3 secure passwords"
    Write-Host "  POSTGRES_PASSWORD: $(($passwords.POSTGRES_PASSWORD.Length)) characters" -ForegroundColor Gray
    Write-Host "  REDIS_PASSWORD:    $(($passwords.REDIS_PASSWORD.Length)) characters" -ForegroundColor Gray
    Write-Host "  SECRET_KEY:        $(($passwords.SECRET_KEY.Length)) characters" -ForegroundColor Gray
    
    return $passwords
}

# ============================================================================
# STEP 3: Request API Keys
# ============================================================================
function Get-ApiKeys {
    Write-Step "2/3" "LLM Provider Configuration"
    
    Write-Info "At least ONE LLM provider API key is required"
    Write-Host ""
    
    $apiKeys = @{}
    $hasProvider = $false
    
    # OpenAI
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    Write-Host "OpenAI (GPT-4, GPT-3.5)" -ForegroundColor Cyan
    Write-Host "Format: sk-... (starts with sk-)" -ForegroundColor Gray
    $openaiKey = Read-Host "OPENAI_API_KEY (press Enter to skip)"
    
    if (-not [string]::IsNullOrWhiteSpace($openaiKey)) {
        if (Test-ApiKey -Key $openaiKey -Provider "OpenAI") {
            $apiKeys["OPENAI_API_KEY"] = $openaiKey
            Write-Success "OpenAI API key validated"
            $hasProvider = $true
        } else {
            Write-Warning "OpenAI key format looks incorrect (expected: sk-...)"
            $continue = Read-Host "Continue anyway? (y/N)"
            if ($continue -eq "y" -or $continue -eq "Y") {
                $apiKeys["OPENAI_API_KEY"] = $openaiKey
                $hasProvider = $true
            }
        }
    }
    
    Write-Host ""
    
    # Anthropic
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    Write-Host "Anthropic (Claude 3.5 Sonnet)" -ForegroundColor Cyan
    Write-Host "Format: sk-ant-... (starts with sk-ant-)" -ForegroundColor Gray
    $anthropicKey = Read-Host "ANTHROPIC_API_KEY (press Enter to skip)"
    
    if (-not [string]::IsNullOrWhiteSpace($anthropicKey)) {
        if (Test-ApiKey -Key $anthropicKey -Provider "Anthropic") {
            $apiKeys["ANTHROPIC_API_KEY"] = $anthropicKey
            Write-Success "Anthropic API key validated"
            $hasProvider = $true
        } else {
            Write-Warning "Anthropic key format looks incorrect (expected: sk-ant-...)"
            $continue = Read-Host "Continue anyway? (y/N)"
            if ($continue -eq "y" -or $continue -eq "Y") {
                $apiKeys["ANTHROPIC_API_KEY"] = $anthropicKey
                $hasProvider = $true
            }
        }
    }
    
    Write-Host ""
    
    if (-not $hasProvider) {
        Write-Error "At least one LLM provider API key is required"
        Write-Info "Get API keys from:"
        Write-Host "  - OpenAI: https://platform.openai.com/api-keys" -ForegroundColor White
        Write-Host "  - Anthropic: https://console.anthropic.com/settings/keys" -ForegroundColor White
        exit 1
    }
    
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    Write-Success "LLM provider configuration complete"
    
    return $apiKeys
}

# ============================================================================
# STEP 4: Create .env.production
# ============================================================================
function New-EnvironmentFile {
    param(
        [hashtable]$Passwords,
        [hashtable]$ApiKeys
    )
    
    Write-Step "3/3" "Creating Environment File"
    
    $infraDir = Split-Path $EnvFile -Parent
    if (-not (Test-Path $infraDir)) {
        New-Item -ItemType Directory -Path $infraDir -Force | Out-Null
    }
    
    $envContent = @"
# Railway Environment Configuration
# Generated by setup_env.ps1 on $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
# DO NOT COMMIT THIS FILE TO GIT!

# =====================================================
# PostgreSQL Configuration
# =====================================================
POSTGRES_USER=$($Passwords.POSTGRES_USER)
POSTGRES_PASSWORD=$($Passwords.POSTGRES_PASSWORD)
POSTGRES_DB=$($Passwords.POSTGRES_DB)

# =====================================================
# Redis Configuration
# =====================================================
REDIS_PASSWORD=$($Passwords.REDIS_PASSWORD)

# =====================================================
# Dify Application Secrets
# =====================================================
SECRET_KEY=$($Passwords.SECRET_KEY)

# =====================================================
# LLM Provider API Keys
# =====================================================
"@

    foreach ($key in $ApiKeys.Keys) {
        $envContent += "`n$key=$($ApiKeys[$key])"
    }
    
    try {
        $envContent | Out-File -FilePath $EnvFile -Encoding utf8 -Force
        Write-Success "Environment file created: $EnvFile"
    } catch {
        Write-Error "Failed to create file: $_"
        exit 1
    }
    
    $fileInfo = Get-Item $EnvFile
    Write-Info "File size: $($fileInfo.Length) bytes"
    Write-Info "Variables: $($Passwords.Count + $ApiKeys.Count) total"
    
    return $true
}

# ============================================================================
# STEP 5: Summary
# ============================================================================
function Show-Summary {
    param([hashtable]$Passwords, [hashtable]$ApiKeys)
    
    Write-Host ""
    Write-Host "=============================================" -ForegroundColor Green
    Write-Host "  Setup Complete!" -ForegroundColor Green
    Write-Host "=============================================" -ForegroundColor Green
    Write-Host ""
    
    Write-Success "Environment file ready: $EnvFile"
    Write-Host ""
    
    Write-Info "Configuration Summary:"
    Write-Host "  Database User:     $($Passwords.POSTGRES_USER)" -ForegroundColor Gray
    Write-Host "  Database Name:     $($Passwords.POSTGRES_DB)" -ForegroundColor Gray
    Write-Host "  Database Password: ***$($Passwords.POSTGRES_PASSWORD.Substring([Math]::Max(0, $Passwords.POSTGRES_PASSWORD.Length - 4)))" -ForegroundColor Gray
    Write-Host "  Redis Password:    ***$($Passwords.REDIS_PASSWORD.Substring([Math]::Max(0, $Passwords.REDIS_PASSWORD.Length - 4)))" -ForegroundColor Gray
    Write-Host "  Secret Key:        ***$($Passwords.SECRET_KEY.Substring([Math]::Max(0, $Passwords.SECRET_KEY.Length - 8)))" -ForegroundColor Gray
    Write-Host ""
    
    Write-Info "LLM Providers:"
    foreach ($key in $apiKeys.Keys) {
        $provider = $key -replace '_API_KEY$', ''
        $maskedKey = "***" + $apiKeys[$key].Substring([Math]::Max(0, $apiKeys[$key].Length - 6))
        Write-Host "  $provider`: $maskedKey" -ForegroundColor Gray
    }
    Write-Host ""
}

# ============================================================================
# STEP 6: Chain to Deployment
# ============================================================================
function Invoke-DeploymentChain {
    if ($SkipDeploy) {
        Write-Info "Deployment skipped (--SkipDeploy flag)"
        return
    }
    
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    Write-Host ""
    $response = Read-Host "Deploy to Railway now? (Y/n)"
    
    if ($response -eq "n" -or $response -eq "N") {
        Write-Info "Deployment skipped"
        Write-Host ""
        Write-Info "To deploy later, run:"
        Write-Host "  .\scripts\deployment\deploy_railway.ps1" -ForegroundColor White
        Write-Host ""
        return
    }
    
    $deployScript = "scripts\deployment\deploy_railway.ps1"
    if (-not (Test-Path $deployScript)) {
        Write-Warning "Deployment script not found: $deployScript"
        return
    }
    
    Write-Host ""
    Write-Info "Launching Railway deployment..."
    Write-Host ""
    
    try {
        & ".\$deployScript" -EnvFile $EnvFile
    } catch {
        Write-Error "Deployment failed: $_"
        Write-Info "You can retry manually:"
        Write-Host "  .\scripts\deployment\deploy_railway.ps1" -ForegroundColor White
    }
}

# ============================================================================
# MAIN
# ============================================================================
function Main {
    Show-Welcome
    $passwords = New-DatabasePasswords
    $apiKeys = Get-ApiKeys
    $success = New-EnvironmentFile -Passwords $passwords -ApiKeys $apiKeys
    
    if (-not $success) {
        Write-Error "Setup failed"
        exit 1
    }
    
    Show-Summary -Passwords $passwords -ApiKeys $apiKeys
    Invoke-DeploymentChain
    
    Write-Host ""
    Write-Success "Setup wizard complete!"
    Write-Host ""
}

Main
