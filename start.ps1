$scriptPath = $PSScriptRoot

$stopScript = Join-Path $scriptPath "stop.ps1"
if (Test-Path $stopScript) {
    Write-Host "Cleaning up previous instances..." -ForegroundColor Yellow
    & $stopScript
}

Write-Host "Starting DBMS Project..." -ForegroundColor Green

# Initialize database tables
$sqlFile = Join-Path $scriptPath "db\requirements_db.sql"
if (Test-Path $sqlFile) {
    Write-Host "Initializing database tables..." -ForegroundColor Cyan
    $envPath = Join-Path $scriptPath "backend\.env"
    if (Test-Path $envPath) {
        $envContent = Get-Content $envPath -Raw
        $DB_HOST = if ($envContent -match 'DB_HOST=(\S+)') { $matches[1] } else { "localhost" }
        $DB_PORT = if ($envContent -match 'DB_PORT=(\S+)') { $matches[1] } else { "5432" }
        $DB_USER = if ($envContent -match 'DB_USER=(\S+)') { $matches[1] } else { "postgres" }
        $DB_PASSWORD = if ($envContent -match 'DB_PASSWORD=(\S+)') { $matches[1] } else { "postgres" }
        $DB_NAME = if ($envContent -match 'DB_NAME=(\S+)') { $matches[1] } else { "postgres" }

        $env:PGPASSWORD = $DB_PASSWORD
        $psqlCmd = "psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f `"$sqlFile`" 2>&1"
        $result = Invoke-Expression $psqlCmd
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Database tables initialized successfully." -ForegroundColor Green
        } else {
            Write-Host "Database initialization warning: $result" -ForegroundColor Yellow
        }
    }
}

$backendDir = Join-Path $scriptPath "backend"
if (Test-Path $backendDir) {
    $envPath = Join-Path $backendDir ".env"
    $envExamplePath = Join-Path $backendDir ".env.example"
    if (-not (Test-Path $envPath) -and (Test-Path $envExamplePath)) {
        Write-Host "Initializing .env file from .env.example..." -ForegroundColor Yellow
        Copy-Item $envExamplePath $envPath
    }

    Write-Host "Starting Backend Service (uv)..." -ForegroundColor Cyan
    $backendCmd = "cd '$backendDir'; uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd
} else {
    Write-Host "Backend directory not found!" -ForegroundColor Red
}

$frontendDir = Join-Path $scriptPath "frontend"
if (Test-Path $frontendDir) {
    Write-Host "Starting Frontend Service (Vite)..." -ForegroundColor Cyan
    $frontendCmd = "cd '$frontendDir'; npm run dev"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd
} else {
    Write-Host "Frontend directory not found!" -ForegroundColor Red
}

Write-Host "Done! Two new windows should appear." -ForegroundColor Green
