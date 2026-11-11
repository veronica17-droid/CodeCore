<#
.SYNOPSIS
    Ejecuta todas las comprobaciones de CodeCore en modo desarrollo.

.DESCRIPTION
    Compila los modulos, valida el contenido, ejecuta las pruebas y (si hay
    sesion grafica) recorre la interfaz con el smoke test.

.NOTES
    Las herramientas nativas (python) escriben progreso en stderr. Con
    ErrorActionPreference = Stop eso se convierte en un error falso, asi que el
    resultado se decide siempre con $LASTEXITCODE.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = "Continue"
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
} catch {
    # Consola sin soporte de UTF-8: se continua con la codificacion por defecto.
}

$root = Split-Path -Parent $PSScriptRoot
Push-Location $root

function Write-CommandOutput {
    process {
        $item = $_
        if ($item -is [System.Management.Automation.ErrorRecord]) {
            Write-Host $item.Exception.Message
        }
        else {
            Write-Host "$item"
        }
    }
}

try {
    $python = Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe"
    if (-not (Test-Path $python)) {
        $python = "python"
    }
    Write-Host "Python: $python" -ForegroundColor Cyan

    $failed = $false

    Write-Host "[1/4] Compilando modulos..." -ForegroundColor Cyan
    & $python -m compileall -q src tools tests 2>&1 | Write-CommandOutput
    if ($LASTEXITCODE -ne 0) { $failed = $true }

    Write-Host "[2/4] Validando contenido..." -ForegroundColor Cyan
    & $python -X utf8 tools\verify_content.py 2>&1 | Write-CommandOutput
    if ($LASTEXITCODE -ne 0) { $failed = $true }

    Write-Host "[3/4] Ejecutando pruebas..." -ForegroundColor Cyan
    & $python -X utf8 -m unittest discover -s tests 2>&1 | Write-CommandOutput
    if ($LASTEXITCODE -ne 0) { $failed = $true }

    Write-Host "[4/4] Smoke test de la interfaz..." -ForegroundColor Cyan
    & $python -X utf8 tools\smoke_gui.py 2>&1 | Write-CommandOutput
    if ($LASTEXITCODE -ne 0) { $failed = $true }

    if ($failed) {
        Write-Host "Hay comprobaciones fallidas." -ForegroundColor Red
        exit 1
    }
    Write-Host "Todo en verde." -ForegroundColor Green
}
finally {
    Pop-Location
}
