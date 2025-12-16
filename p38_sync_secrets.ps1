param(
    [Parameter(Mandatory=$true)]
    [string]$Path
)

$RequiredSecrets = @(
    'telegram-bot-token',
    'openai-api-key',
    'anthropic-api-key',
    'gemini-api-key',
    'github-pat',
    'n8n-encryption-key',
    'postgres-password'
)

Write-Host "=== Project 38 Secret Sync ===" -ForegroundColor Cyan
Write-Host "Reading secrets from: $Path" -ForegroundColor Gray

if (-not (Test-Path $Path)) {
    Write-Host "ERROR: File not found: $Path" -ForegroundColor Red
    exit 1
}

$secrets = @{}
$projectIds = @{}

Get-Content $Path | ForEach-Object {
    $line = $_.Trim()
    if ($line -and -not $line.StartsWith('#')) {
        $parts = $line -split '=', 2
        if ($parts.Length -eq 2) {
            $key = $parts[0].Trim()
            $value = $parts[1].Trim()
            
            if ($key -eq 'GCP_DEV_PROJECT_ID') {
                $projectIds['DEV'] = $value
                Write-Host "Found DEV project: $value" -ForegroundColor Green
            }
            elseif ($key -eq 'GCP_PROD_PROJECT_ID') {
                $projectIds['PROD'] = $value
                Write-Host "Found PROD project: $value" -ForegroundColor Green
            }
            elseif ($key -match '^(DEV|PROD)\.(.+)$') {
                $env = $Matches[1]
                $secretName = $Matches[2]
                
                if (-not $secrets.ContainsKey($env)) {
                    $secrets[$env] = @{}
                }
                $secrets[$env][$secretName] = $value
            }
        }
    }
}

$missing = @()
if (-not $projectIds.ContainsKey('DEV')) { $missing += 'GCP_DEV_PROJECT_ID' }
if (-not $projectIds.ContainsKey('PROD')) { $missing += 'GCP_PROD_PROJECT_ID' }

if ($missing.Count -gt 0) {
    Write-Host "`nMISSING_REQUIRED_CONFIG:" -ForegroundColor Red
    $missing | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
    exit 1
}

foreach ($env in @('DEV', 'PROD')) {
    $missingSecrets = @()
    foreach ($reqSecret in $RequiredSecrets) {
        if (-not $secrets[$env].ContainsKey($reqSecret)) {
            $missingSecrets += "$env.$reqSecret"
        }
    }
    
    if ($missingSecrets.Count -gt 0) {
        if ($missing.Count -eq 0) {
            Write-Host "`nMISSING_REQUIRED_SECRETS:" -ForegroundColor Red
        }
        $missingSecrets | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
        $missing += $missingSecrets
    }
}

if ($missing.Count -gt 0) {
    exit 1
}

Write-Host "`n=== Syncing Secrets to GCP ===" -ForegroundColor Cyan

$syncResults = @{}

foreach ($env in @('DEV', 'PROD')) {
    $projectId = $projectIds[$env]
    $syncResults[$env] = @{}
    
    Write-Host "`nProcessing $env environment (project: $projectId)..." -ForegroundColor Cyan
    
    foreach ($secretName in $secrets[$env].Keys) {
        $secretValue = $secrets[$env][$secretName]
        
        $tempFile = [System.IO.Path]::GetTempFileName()
        try {
            $utf8NoBom = New-Object System.Text.UTF8Encoding $false
            [System.IO.File]::WriteAllText($tempFile, $secretValue, $utf8NoBom)
            
            $existsCheck = gcloud secrets describe $secretName --project=$projectId 2>&1 | Out-String
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  Updating: $secretName" -ForegroundColor Yellow
                $result = gcloud secrets versions add $secretName --data-file=$tempFile --project=$projectId 2>&1 | Out-String
                
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "    ✓ Version added" -ForegroundColor Green
                    $syncResults[$env][$secretName] = 'updated'
                } else {
                    Write-Host "    ✗ Failed" -ForegroundColor Red
                    $syncResults[$env][$secretName] = 'failed'
                }
            } else {
                Write-Host "  Creating: $secretName" -ForegroundColor Green
                $result = gcloud secrets create $secretName --data-file=$tempFile --replication-policy=automatic --project=$projectId 2>&1 | Out-String
                
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "    ✓ Created" -ForegroundColor Green
                    $syncResults[$env][$secretName] = 'created'
                } else {
                    Write-Host "    ✗ Failed" -ForegroundColor Red
                    $syncResults[$env][$secretName] = 'failed'
                }
            }
        } finally {
            if (Test-Path $tempFile) {
                Remove-Item $tempFile -Force
            }
        }
    }
}

Write-Host "`n=== Verification ===" -ForegroundColor Cyan

$verificationResults = @{}

foreach ($env in @('DEV', 'PROD')) {
    $projectId = $projectIds[$env]
    $verificationResults[$env] = @{}
    
    Write-Host "`nVerifying $env environment..." -ForegroundColor Cyan
    
    foreach ($secretName in $secrets[$env].Keys) {
        $versions = gcloud secrets versions list $secretName --project=$projectId --format="value(name)" 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            $versionCount = ($versions | Measure-Object).Count
            $verificationResults[$env][$secretName] = $versionCount
            Write-Host "  ✓ $secretName : $versionCount version(s)" -ForegroundColor Green
        } else {
            Write-Host "  ✗ $secretName : verification failed" -ForegroundColor Red
            $verificationResults[$env][$secretName] = 0
        }
    }
}

Write-Host "`n=== SYNC_OK ===" -ForegroundColor Green
Write-Host "`nSummary:" -ForegroundColor Cyan

foreach ($env in @('DEV', 'PROD')) {
    $projectId = $projectIds[$env]
    Write-Host "`n$env ($projectId):" -ForegroundColor Yellow
    
    foreach ($secretName in ($verificationResults[$env].Keys | Sort-Object)) {
        $versions = $verificationResults[$env][$secretName]
        Write-Host "  - $secretName (versions: $versions)" -ForegroundColor Gray
    }
}

Write-Host "`n✓ All secrets synced successfully" -ForegroundColor Green
