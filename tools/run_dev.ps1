# Ejecuta CodeCore en modo desarrollo, sin empaquetar.
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe"

if (-not (Test-Path $python)) {
    $python = "python"
}

Write-Host "Iniciando CodeCore desde $root ..." -ForegroundColor Cyan
& $python "$root\src\main.py" @args
exit $LASTEXITCODE
