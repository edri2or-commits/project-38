# ============================================================================
# Railway Zero-Touch Deployment Script
# Project 38 - Dify Infrastructure Automation
# ============================================================================
# This script automates the entire Railway deployment process:
# 1. Checks and installs Railway CLI if needed
# 2. Initializes Railway project
# 3. Injects environment variables from .env.production
# 4. Deploys the Dify infrastructure
#
# Usage: .\deploy_railway.ps1
# Prerequisites: .env.production file in infrastructure/ directory
# ============================================================================

param(
    [string]$EnvFile = "infrastructure\.env.production",
    [switch]$SkipInstallCheck,
    [switch]$DryRun
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

# ============================================================================
# STEP 1: Environment Check - Railway CLI Installation
# ============================================================================
function Test-RailwayCLI {
    Write-Step "1/5" "Checking Railway CLI Installation"
    
    try {
        $railwayVersion = railway --version 2>$null
        if ($railwayVersion) {
            Write-Success "Railway CLI is installed: $railwayVersion"
            return $true
        }
    } catch {
        Write-Info "Railway CLI not found"
        return $false
    }
    return $false
}

function Install-RailwayCLI {
    Write-Step "1/5" "Installing Railway CLI"
    
    # Check for Scoop first (preferred method)
    try {
        $scoopVersion = scoop --version 2>$null
        if ($scoopVersion) {
            Write-Info "Installing Railway CLI via Scoop..."
            scoop install railway
            
            if (Test-RailwayCLI) {
                Write-Success "Railway CLI installed successfully via Scoop"
                return $true
            }
        }
    } catch {
        Write-Info "Scoop not available, trying npm..."
    }
    
    # Fallback to npm
    try {
        $npmVersion = npm --version 2>$null
        if ($npmVersion) {
            Write-Info "Installing Railway CLI via npm..."
            npm install -g @railway/cli
            
            # Refresh PATH
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
            
            if (Test-RailwayCLI) {
                Write-Success "Railway CLI installed successfully via npm"
                return $true
            }
        }
    } catch {
        Write-Error "npm not available"
    }
    
    # Manual installation instructions
    Write-Error "Unable to install Railway CLI automatically"
    Write-Warning "Please install Railway CLI manually:"
    Write-Host ""
    Write-Host "Option 1 (Scoop - Recommended):"
    Write-Host "  scoop install railway" -ForegroundColor White
    Write-Host ""
    Write-Host "Option 2 (npm):"
    Write-Host "  npm install -g @railway/cli" -ForegroundColor White
    Write-Host ""
    Write-Host "Option 3 (Direct download):"
    Write-Host "  https://docs.railway.app/develop/cli" -ForegroundColor White
    
    exit 1
}

# ============================================================================
# STEP 2: Project Initialization
# ============================================================================
function Initialize-RailwayProject {
    Write-Step "2/5" "Railway Project Initialization"
    
    # Check if already linked to a Railway project
    if (Test-Path ".railway") {
        Write-Success "Railway project already initialized (.railway directory found)"
        
        # Show current project info
        try {
            $projectInfo = railway status 2>$null
            Write-Info "Current project status:"
            Write-Host $projectInfo -ForegroundColor Gray
        } catch {
            Write-Warning "Could not retrieve project status"
        }
        
        $response = Read-Host "Do you want to reinitialize? (y/N)"
        if ($response -ne "y" -and $response -ne "Y") {
            Write-Info "Skipping reinitialization"
            return $true
        }
    }
    
    # Initialize new project
    Write-Info "Initializing new Railway project..."
    Write-Warning "This will open Railway login in your browser"
    Write-Host ""
    
    if ($DryRun) {
        Write-Info "[DRY RUN] Would execute: railway init"
        return $true
    }
    
    try {
        railway login
        railway init
        
        if (Test-Path ".railway") {
            Write-Success "Railway project initialized successfully"
            return $true
        } else {
            Write-Error "Railway initialization failed - .railway directory not created"
            return $false
        }
    } catch {
        Write-Error "Railway initialization failed: $_"
        return $false
    }
}

# ============================================================================
# STEP 3: Environment File Validation
# ============================================================================
function Test-EnvironmentFile {
    param([string]$FilePath)
    
    Write-Step "3/5" "Environment File Validation"
    
    if (-not (Test-Path $FilePath)) {
        Write-Error "Environment file not found: $FilePath"
        Write-Warning "Please create the file from template:"
        Write-Host "  1. Copy infrastructure\.env.template to infrastructure\.env.production" -ForegroundColor White
        Write-Host "  2. Fill in all required values" -ForegroundColor White
        Write-Host "  3. Run this script again" -ForegroundColor White
        exit 1
    }
    
    Write-Success "Environment file found: $FilePath"
    
    # Parse and validate required variables
    $envContent = Get-Content $FilePath | Where-Object { $_ -match '^[A-Z_]+=.+' }
    $variables = @{}
    
    foreach ($line in $envContent) {
        if ($line -match '^([A-Z_]+)=(.*)$') {
            $key = $matches[1]
            $value = $matches[2].Trim()
            
            if ($value) {
                $variables[$key] = $value
            }
        }
    }
    
    # Required variables check
    $requiredVars = @(
        'POSTGRES_USER',
        'POSTGRES_PASSWORD',
        'POSTGRES_DB',
        'REDIS_PASSWORD',
        'SECRET_KEY'
    )
    
    $missingVars = @()
    foreach ($var in $requiredVars) {
        if (-not $variables.ContainsKey($var) -or -not $variables[$var]) {
            $missingVars += $var
        }
    }
    
    # Check for at least one LLM provider
    $hasLLMProvider = $variables.ContainsKey('OPENAI_API_KEY') -or 
                      $variables.ContainsKey('ANTHROPIC_API_KEY') -or
                      $variables.ContainsKey('GOOGLE_API_KEY') -or
                      $variables.ContainsKey('AZURE_OPENAI_API_KEY')
    
    if (-not $hasLLMProvider) {
        $missingVars += "At least one LLM API Key (OPENAI_API_KEY or ANTHROPIC_API_KEY)"
    }
    
    if ($missingVars.Count -gt 0) {
        Write-Error "Missing required environment variables:"
        foreach ($var in $missingVars) {
            Write-Host "  - $var" -ForegroundColor Red
        }
        exit 1
    }
    
    Write-Success "All required environment variables present"
    Write-Info "Found $($variables.Count) environment variables to inject"
    
    return $variables
}

# ============================================================================
# STEP 4: Variable Injection
# ============================================================================
function Set-RailwayVariables {
    param([hashtable]$Variables)
    
    Write-Step "4/5" "Injecting Environment Variables to Railway"
    
    $successCount = 0
    $failCount = 0
    $total = $Variables.Count
    
    Write-Info "Processing $total environment variables..."
    Write-Host ""
    
    foreach ($key in $Variables.Keys) {
        $value = $Variables[$key]
        
        # Mask sensitive values in output
        $displayValue = if ($key -match '(PASSWORD|SECRET|KEY|TOKEN)') {
            "***" + $value.Substring([Math]::Max(0, $value.Length - 4))
        } else {
            $value
        }
        
        Write-Host "  Setting $key = $displayValue" -ForegroundColor Gray -NoNewline
        
        if ($DryRun) {
            Write-Host " [DRY RUN]" -ForegroundColor Yellow
            $successCount++
            continue
        }
        
        try {
            # Railway CLI command to set variable
            $output = railway variables --set "$key=$value" 2>&1
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host " ✓" -ForegroundColor Green
                $successCount++
            } else {
                Write-Host " ✗" -ForegroundColor Red
                Write-Warning "Failed to set $key : $output"
                $failCount++
            }
        } catch {
            Write-Host " ✗" -ForegroundColor Red
            Write-Warning "Exception setting $key : $_"
            $failCount++
        }
        
        Start-Sleep -Milliseconds 100  # Rate limiting
    }
    
    Write-Host ""
    Write-Success "Variable injection complete: $successCount/$total succeeded"
    
    if ($failCount -gt 0) {
        Write-Warning "$failCount variables failed to set"
        $response = Read-Host "Continue with deployment? (y/N)"
        if ($response -ne "y" -and $response -ne "Y") {
            Write-Error "Deployment cancelled by user"
            exit 1
        }
    }
    
    return $successCount -eq $total
}

# ============================================================================
# STEP 5: Deployment Launch
# ============================================================================
function Start-RailwayDeployment {
    Write-Step "5/5" "Launching Railway Deployment"
    
    Write-Info "Deploying Dify infrastructure to Railway..."
    Write-Warning "This may take 5-10 minutes for initial deployment"
    Write-Host ""
    
    if ($DryRun) {
        Write-Info "[DRY RUN] Would execute: railway up --detach"
        Write-Success "DRY RUN COMPLETED - No actual deployment performed"
        return $true
    }
    
    try {
        # Deploy with detached mode
        railway up --detach
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Deployment initiated successfully!"
            Write-Host ""
            Write-Info "Monitor deployment status:"
            Write-Host "  railway status" -ForegroundColor White
            Write-Host ""
            Write-Info "View logs:"
            Write-Host "  railway logs" -ForegroundColor White
            Write-Host ""
            Write-Info "Open Railway dashboard:"
            Write-Host "  railway open" -ForegroundColor White
            
            return $true
        } else {
            Write-Error "Deployment command failed"
            return $false
        }
    } catch {
        Write-Error "Deployment exception: $_"
        return $false
    }
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================
function Main {
    Write-Host ""
    Write-Host "=============================================" -ForegroundColor Magenta
    Write-Host "  Railway Zero-Touch Deployment" -ForegroundColor Magenta
    Write-Host "  Project 38 - Dify Infrastructure" -ForegroundColor Magenta
    Write-Host "=============================================" -ForegroundColor Magenta
    Write-Host ""
    
    if ($DryRun) {
        Write-Warning "DRY RUN MODE - No changes will be made"
        Write-Host ""
    }
    
    # Step 1: Check/Install Railway CLI
    if (-not $SkipInstallCheck) {
        if (-not (Test-RailwayCLI)) {
            Install-RailwayCLI
        }
    }
    
    # Step 2: Initialize Railway Project
    if (-not (Initialize-RailwayProject)) {
        Write-Error "Project initialization failed"
        exit 1
    }
    
    # Step 3: Validate Environment File
    $variables = Test-EnvironmentFile -FilePath $EnvFile
    
    # Step 4: Inject Variables
    if (-not (Set-RailwayVariables -Variables $variables)) {
        Write-Warning "Some variables failed to set, but continuing..."
    }
    
    # Step 5: Deploy
    if (-not (Start-RailwayDeployment)) {
        Write-Error "Deployment failed"
        exit 1
    }
    
    # Success Summary
    Write-Host ""
    Write-Host "=============================================" -ForegroundColor Green
    Write-Host "  DEPLOYMENT COMPLETE!" -ForegroundColor Green
    Write-Host "=============================================" -ForegroundColor Green
    Write-Host ""
    Write-Success "Dify infrastructure deployed to Railway"
    Write-Info "Next steps:"
    Write-Host "  1. Monitor deployment: railway status" -ForegroundColor White
    Write-Host "  2. View logs: railway logs" -ForegroundColor White
    Write-Host "  3. Open dashboard: railway open" -ForegroundColor White
    Write-Host "  4. Get service URL: railway domain" -ForegroundColor White
    Write-Host ""
}

# Run main function
Main
