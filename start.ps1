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

    $hostsToTry = @($ServerHost)
    if ($ServerHost -in @("localhost", "127.0.0.1", "::1")) {
        $hostsToTry = @($ServerHost, "127.0.0.1", "localhost", "::1") | Select-Object -Unique
    }

    foreach ($hostName in $hostsToTry) {
        $client = $null
        try {
            $client = [System.Net.Sockets.TcpClient]::new()
            $connectTask = $client.ConnectAsync($hostName, $Port)
            if (-not $connectTask.Wait(1000)) {
                continue
            }
            return $client.Connected
        } catch {
            continue
        } finally {
            if ($client) {
                $client.Dispose()
            }
        }
    }

    return $false
}

function Test-FileWritable {
    param([string]$Path)

    if (-not $Path) {
        return $false
    }

    $parentDir = Split-Path -Parent $Path
    if (-not $parentDir) {
        return $false
    }

    try {
        New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
    } catch {
        return $false
    }

    $created = -not (Test-Path -LiteralPath $Path)
    try {
        $stream = [System.IO.File]::Open($Path, [System.IO.FileMode]::OpenOrCreate, [System.IO.FileAccess]::Write, [System.IO.FileShare]::ReadWrite)
        $stream.Dispose()
        if ($created) {
            Remove-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue
        }
        return $true
    } catch {
        return $false
    }
}

function Resolve-PostgresLogFile {
    param(
        [string]$ConfiguredLogFile,
        [string]$DataDir
    )

    $fallbackLogFile = Join-Path $DataDir "pg_ctl-start.log"
    if ($ConfiguredLogFile -and (Test-FileWritable -Path $ConfiguredLogFile)) {
        return $ConfiguredLogFile
    }

    if ($ConfiguredLogFile) {
        Write-Host "Configured PostgreSQL log file is not writable: $ConfiguredLogFile" -ForegroundColor Yellow
        Write-Host "Falling back to $fallbackLogFile" -ForegroundColor Yellow
    }

    return $fallbackLogFile
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
        [string]$PgRoot,
        [string]$DataDir,
        [string]$LogFile,
        [int]$StartTimeout = 30,
        [bool]$AutoStart = $true
    )

    if ($ServerHost -notin @("localhost", "127.0.0.1", "::1")) {
        return $true
    }

    if (Test-TcpPort -ServerHost $ServerHost -Port $Port) {
        Write-Host "PostgreSQL is already listening on $ServerHost`:$Port." -ForegroundColor Green
        return $true
    }

    if (-not $AutoStart) {
        Write-Host "Local PostgreSQL auto-start is disabled." -ForegroundColor Yellow
        return $false
    }

    $dataDir = if ($DataDir) { $DataDir } else { Join-Path $PgRoot "data" }
    $pgCtl = Join-Path $PgRoot "bin\pg_ctl.exe"
    $pidFile = Join-Path $dataDir "postmaster.pid"
    $logFile = Resolve-PostgresLogFile -ConfiguredLogFile $LogFile -DataDir $dataDir

    if (-not (Test-Path $pgCtl) -or -not (Test-Path $dataDir)) {
        Write-Host "Local PostgreSQL instance not found at $PgRoot." -ForegroundColor Yellow
        return $false
    }

    $logDir = Split-Path -Parent $logFile
    if ($logDir) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }

    if (Test-Path $pidFile) {
        $postgresPid = $null
        $firstLine = Get-Content -LiteralPath $pidFile | Select-Object -First 1
        if ($firstLine -match '^\d+$') {
            $postgresPid = [int]$firstLine
        }

        $processExists = $false
        if ($postgresPid -ne $null) {
            $postgresProcess = Get-Process -Id $postgresPid -ErrorAction SilentlyContinue
            $processExists = [bool]($postgresProcess -and $postgresProcess.ProcessName -ieq "postgres")
        }

        if (Test-TcpPort -ServerHost $ServerHost -Port $Port) {
            Write-Host "PostgreSQL is already listening on $ServerHost`:$Port." -ForegroundColor Green
            return $true
        }

        if (-not $processExists) {
            Write-Host "Removing stale PostgreSQL pid file..." -ForegroundColor Yellow
            Remove-Item -LiteralPath $pidFile -Force
        }
    }

    Write-Host "Starting local PostgreSQL instance on port $Port..." -ForegroundColor Cyan
    $startOutput = & $pgCtl start -D $dataDir -l $logFile 2>&1
    if ($LASTEXITCODE -ne 0 -and -not (Test-TcpPort -ServerHost $ServerHost -Port $Port)) {
        Write-Host "Failed to start local PostgreSQL instance." -ForegroundColor Red
        if ($startOutput) {
            Write-Host (($startOutput | Select-Object -Last 1).ToString()) -ForegroundColor Red
        }
        return $false
    }

    for ($attempt = 1; $attempt -le $StartTimeout; $attempt++) {
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
$PG_ROOT = Get-EnvValue -Content $envContent -Name "LOCAL_PG_INSTALL_DIR" -Default (Get-EnvValue -Content $envContent -Name "PG_ROOT" -Default "W:\DB\PostgreSQL")
$LOCAL_PG_DATA_DIR = Get-EnvValue -Content $envContent -Name "LOCAL_PG_DATA_DIR" -Default (Join-Path $PG_ROOT "data")
$LOCAL_PG_LOG_FILE = Get-EnvValue -Content $envContent -Name "LOCAL_PG_LOG_FILE" -Default (Join-Path $PG_ROOT "pg_ctl-start.log")
$LOCAL_PG_START_TIMEOUT = [int](Get-EnvValue -Content $envContent -Name "LOCAL_PG_START_TIMEOUT" -Default "30")
$LOCAL_PG_AUTO_START = (Get-EnvValue -Content $envContent -Name "LOCAL_PG_AUTO_START" -Default "1").Trim().ToLower() -notin @("0", "false", "no", "off")

$dbReady = Ensure-LocalPostgres -ServerHost $DB_HOST -Port $DB_PORT -PgRoot $PG_ROOT -DataDir $LOCAL_PG_DATA_DIR -LogFile $LOCAL_PG_LOG_FILE -StartTimeout $LOCAL_PG_START_TIMEOUT -AutoStart $LOCAL_PG_AUTO_START

$sqlFile = Join-Path $scriptPath "db\requirements_db.sql"
$sqlPatchFile = Join-Path $scriptPath "db\requirements_db_constraints_patch.sql"
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

        if (Test-Path $sqlPatchFile) {
            Write-Host "Applying schema constraints patch..." -ForegroundColor Cyan
            $patchResult = & $psqlPath -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f $sqlPatchFile 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Schema constraints patch applied successfully." -ForegroundColor Green
            } else {
                Write-Host "Schema constraints patch warning: $patchResult" -ForegroundColor Yellow
            }
        }
    } else {
        Write-Host "psql not found. Skipping schema initialization." -ForegroundColor Yellow
    }
} elseif (-not $dbReady) {
    Write-Host "Skipping schema initialization because PostgreSQL is not ready." -ForegroundColor Yellow
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
