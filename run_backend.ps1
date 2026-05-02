param(
    [string]$BindHost = "127.0.0.1",
    [int]$Port = 8000,
    [switch]$NoReload
)

$python = Join-Path $PSScriptRoot "venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Error "Virtual environment not found at $python"
    exit 1
}

$portInUse = [System.Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties().
    GetActiveTcpListeners() |
    Where-Object { $_.Port -eq $Port }

if ($portInUse) {
    Write-Error "Port $Port is already in use. Stop the existing server first or run .\\run_backend.ps1 -Port 8002"
    exit 1
}

$arguments = @(
    "-m",
    "uvicorn",
    "backend.main:app",
    "--host",
    $BindHost,
    "--port",
    $Port.ToString()
)

if (-not $NoReload) {
    $arguments += "--reload"
}

& $python @arguments
