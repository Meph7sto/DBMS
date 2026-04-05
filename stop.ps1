Write-Host "Stopping DBMS Services..." -ForegroundColor Yellow

function Kill-ProcessByPort {
    param([int]$Port, [string]$ServiceName)
    Write-Host "Checking for $ServiceName on port $Port..."
    
    $netstatOutput = netstat -ano | Select-String ":$Port "
    
    if ($netstatOutput) {
        $pidsToKill = @()
        foreach ($line in $netstatOutput) {
            # Extract PID from corresponding netstat output
            $parts = $line.ToString().Trim() -split '\s+'
            if ($parts.Count -ge 5 -and $parts[1] -match ":$Port$") {
                $pidValue = $parts[-1]
                if ($pidValue -ne "0" -and $pidsToKill -notcontains $pidValue) {
                    $pidsToKill += $pidValue
                }
            }
        }
        
        if ($pidsToKill.Count -gt 0) {
            foreach ($processId in $pidsToKill) {
                Write-Host "Stopping $ServiceName (PID: $processId)..." -ForegroundColor Cyan
                # Use taskkill to cleanly stop the process tree
                taskkill /PID $processId /T /F 2>&1 | Out-Null
            }
            Write-Host "$ServiceName stopped." -ForegroundColor Green
        }
    } else {
        Write-Host "No process found running on port $Port ($ServiceName)." -ForegroundColor Gray
    }
}

# Stop backend on port 8000
Kill-ProcessByPort -Port 8000 -ServiceName "Backend Service (uv/uvicorn)"

# Stop frontend on port 5173
Kill-ProcessByPort -Port 5173 -ServiceName "Frontend Service (Vite)"

Write-Host "All specified services have been stopped." -ForegroundColor Green
