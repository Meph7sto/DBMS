$scriptPath = $PSScriptRoot

function Get-EnvValue {
    param(
        [string]$Content,
        [string]$Name,
        [string]$Default
    )

    $pattern = "(?m)^\s*$([regex]::Escape($Name))=(.+?)\s*$"
    if ($Content -match $pattern) {
        return $matches[1]
    }
    return $Default
}

function Test-TcpPort {
    param(
        [string]$ServerHost,
        [int]$Port
    )

    try {
        $result = Test-NetConnection -ComputerName $ServerHost -Port $Port -WarningAction SilentlyContinue
        return [bool]$result.TcpTestSucceeded
    } catch {
        return $false
    }
}

function Get-PsqlPath {
    param([string]$PgRoot)

    $localPsql = Join-Path $PgRoot "bin\psql.exe"
    if (Test-Path $localPsql) {
        return $localPsql
    }

    $command = Get-Command psql -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    return $null
}

function Ensure-LocalPostgres {
    param(
        [string]$ServerHost,
        [int]$Port,
        [string]$PgRoot
    )

    if ($ServerHost -notin @("localhost", "127.0.0.1", "::1")) {
        return $true
    }

    if (Test-TcpPort -ServerHost $ServerHost -Port $Port) {
        Write-Host "PostgreSQL is already listening on $ServerHost`:$Port." -ForegroundColor Green
        return $true
    }

    $dataDir = Join-Path $PgRoot "data"
    $pgCtl = Join-Path $PgRoot "bin\pg_ctl.exe"
    $pidFile = Join-Path $dataDir "postmaster.pid"
    $logFile = Join-Path $dataDir "log\manual-start.log"

    if (-not (Test-Path $pgCtl) -or -not (Test-Path $dataDir)) {
        Write-Host "Local PostgreSQL instance not found at $PgRoot." -ForegroundColor Yellow
        return $false
    }

    if (Test-Path $pidFile) {
        $pid = $null
        $firstLine = Get-Content $pidFile | Select-Object -First 1
        if ($firstLine -match '^\d+$') {
            $pid = [int]$firstLine
        }

        & $pgCtl status -D $dataDir *> $null
        $hasRunningServer = $LASTEXITCODE -eq 0
        $processExists = $false
        if ($pid) {
            $processExists = [bool](Get-Process -Id $pid -ErrorAction SilentlyContinue)
        }

        if (-not $hasRunningServer -and -not $processExists) {
            Write-Host "Removing stale PostgreSQL pid file..." -ForegroundColor Yellow
            Remove-Item -LiteralPath $pidFile -Force
        }
    }

    Write-Host "Starting local PostgreSQL instance on port $Port..." -ForegroundColor Cyan
    & $pgCtl start -D $dataDir -l $logFile -w
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to start local PostgreSQL instance." -ForegroundColor Red
        return $false
    }

    for ($attempt = 1; $attempt -le 10; $attempt++) {
        if (Test-TcpPort -ServerHost $ServerHost -Port $Port) {
            Write-Host "PostgreSQL started successfully on $ServerHost`:$Port." -ForegroundColor Green
            return $true
        }
        Start-Sleep -Seconds 1
    }

    Write-Host "PostgreSQL process started, but port $Port did not become reachable." -ForegroundColor Red
    return $false
}

function Test-CoreSchemaExists {
    param(
        [string]$PsqlPath,
        [string]$ServerHost,
        [int]$Port,
        [string]$User,
        [string]$Database
    )

    $result = & $PsqlPath -h $ServerHost -p $Port -U $User -d $Database -t -A -c "SELECT to_regclass('public.manage_products') IS NOT NULL;"
    return ($LASTEXITCODE -eq 0 -and $result.Trim() -eq "t")
}

$stopScript = Join-Path $scriptPath "stop.ps1"
if (Test-Path $stopScript) {
    Write-Host "Cleaning up previous instances..." -ForegroundColor Yellow
    & $stopScript
}

Write-Host "Starting DBMS Project..." -ForegroundColor Green

$backendDir = Join-Path $scriptPath "backend"
$envPath = Join-Path $backendDir ".env"
$envExamplePath = Join-Path $backendDir ".env.example"
if ((Test-Path $backendDir) -and -not (Test-Path $envPath) -and (Test-Path $envExamplePath)) {
    Write-Host "Initializing .env file from .env.example..." -ForegroundColor Yellow
    Copy-Item $envExamplePath $envPath
}

$envContent = if (Test-Path $envPath) { Get-Content $envPath -Raw } else { "" }
$DB_HOST = Get-EnvValue -Content $envContent -Name "DB_HOST" -Default "localhost"
$DB_PORT = [int](Get-EnvValue -Content $envContent -Name "DB_PORT" -Default "5438")
$DB_USER = Get-EnvValue -Content $envContent -Name "DB_USER" -Default "postgres"
$DB_PASSWORD = Get-EnvValue -Content $envContent -Name "DB_PASSWORD" -Default "postgres"
$DB_NAME = Get-EnvValue -Content $envContent -Name "DB_NAME" -Default "postgres"
$PG_ROOT = Get-EnvValue -Content $envContent -Name "PG_ROOT" -Default "W:\DB\PostgreSQL"

$dbReady = Ensure-LocalPostgres -ServerHost $DB_HOST -Port $DB_PORT -PgRoot $PG_ROOT

$sqlFile = Join-Path $scriptPath "db\requirements_db.sql"
if ($dbReady -and (Test-Path $sqlFile)) {
    $psqlPath = Get-PsqlPath -PgRoot $PG_ROOT
    if ($psqlPath) {
        Write-Host "Checking database schema..." -ForegroundColor Cyan
        $env:PGPASSWORD = $DB_PASSWORD
        if (Test-CoreSchemaExists -PsqlPath $psqlPath -ServerHost $DB_HOST -Port $DB_PORT -User $DB_USER -Database $DB_NAME) {
            Write-Host "Core tables already exist. Skipping schema initialization." -ForegroundColor Green
        } else {
            Write-Host "Initializing database tables..." -ForegroundColor Cyan
            $result = & $psqlPath -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f $sqlFile 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Database tables initialized successfully." -ForegroundColor Green
            } else {
                Write-Host "Database initialization warning: $result" -ForegroundColor Yellow
            }
        }
    } else {
        Write-Host "psql not found. Skipping schema initialization." -ForegroundColor Yellow
    }
}

if (Test-Path $backendDir) {
    Write-Host "Starting Backend Service (uv)..." -ForegroundColor Cyan
    $backendCmd = "cd '$backendDir'; uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000"
    Start-Process powershell -ArgumentList "-NoProfile", "-Command", $backendCmd
} else {
    Write-Host "Backend directory not found!" -ForegroundColor Red
}

$frontendDir = Join-Path $scriptPath "frontend"
if (Test-Path $frontendDir) {
    Write-Host "Starting Frontend Service (Vite)..." -ForegroundColor Cyan
    $frontendCmd = "cd '$frontendDir'; npm run dev"
    Start-Process powershell -ArgumentList "-NoProfile", "-Command", $frontendCmd
} else {
    Write-Host "Frontend directory not found!" -ForegroundColor Red
}

Write-Host "Done! Two new windows should appear." -ForegroundColor Green
