<#
.SYNOPSIS
    Genera CodeCore.exe con PyInstaller y lo deja en tu carpeta de trabajo.

.DESCRIPTION
    Comprueba el entorno, valida el contenido, ejecuta las pruebas y empaqueta.
    El ejecutable queda en dist\CodeCore.exe y tambien se copia a la carpeta
    desde donde lanzaste el script (tu carpeta actual), para que lo encuentres
    facilmente. No se ejecuta solo: hay que invocarlo explicitamente.

.EXAMPLE
    .\tools\build_exe.ps1

.EXAMPLE
    .\tools\build_exe.ps1 -SkipTests

.NOTES
    Las herramientas nativas (python) escriben progreso en stderr. Con
    ErrorActionPreference = Stop eso se convierte en un error falso, asi que el
    resultado se decide siempre con $LASTEXITCODE.
#>
[CmdletBinding()]
param(
    [switch]$SkipTests,
    [switch]$NoClean
)

$ErrorActionPreference = "Continue"
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
} catch {
    # Consola sin soporte de UTF-8: se continua con la codificacion por defecto.
}

$root = Split-Path -Parent $PSScriptRoot
$ubicacionOrigen = Get-Location
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

    & $python -c "import tkinter" 2>&1 | Write-CommandOutput
    if ($LASTEXITCODE -ne 0) {
        throw "tkinter no esta disponible en este Python. Instala Python desde python.org (incluye tkinter)."
    }

    & $python -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('PyInstaller') else 1)" 2>&1 | Write-CommandOutput
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller no esta instalado. Ejecuta: & `"$python`" -m pip install --upgrade pyinstaller"
    }

    if (-not $SkipTests) {
        Write-Host "Validando contenido..." -ForegroundColor Cyan
        & $python -X utf8 tools\verify_content.py 2>&1 | Write-CommandOutput
        if ($LASTEXITCODE -ne 0) {
            throw "El contenido no paso la validacion."
        }

        Write-Host "Ejecutando pruebas..." -ForegroundColor Cyan
        & $python -X utf8 -m unittest discover -s tests 2>&1 | Write-CommandOutput
        if ($LASTEXITCODE -ne 0) {
            throw "Las pruebas fallaron. No se genera el ejecutable."
        }
    }

    if (-not (Test-Path "resources\assets\codecore.ico")) {
        Write-Host "Generando icono..." -ForegroundColor Cyan
        & $python -X utf8 tools\make_icon.py 2>&1 | Write-CommandOutput
        if ($LASTEXITCODE -ne 0) {
            throw "No se pudo generar el icono."
        }
    }

    $pyInstallerArgs = @(
        "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name", "CodeCore",
        "--icon", "resources\assets\codecore.ico",
        "--add-data", "resources;resources"
    )
    if (-not $NoClean) {
        $pyInstallerArgs += "--clean"
    }
    $pyInstallerArgs += "src\main.py"

    Write-Host "Empaquetando con PyInstaller..." -ForegroundColor Cyan
    & $python @pyInstallerArgs 2>&1 | Write-CommandOutput
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller termino con error."
    }

    $exe = Join-Path $root "dist\CodeCore.exe"
    if (-not (Test-Path $exe)) {
        throw "No se genero el ejecutable esperado: $exe"
    }

    $sizeMb = [math]::Round((Get-Item $exe).Length / 1MB, 1)
    Write-Host "Listo: $exe ($sizeMb MB)" -ForegroundColor Green
    Write-Host "Prueba el .exe en una maquina sin Python y revisa docs\05-empaquetado.md." -ForegroundColor Green

    # Deja una copia en la carpeta donde se ejecuto el script (tu carpeta actual).
    $destino = Join-Path $ubicacionOrigen "CodeCore.exe"
    Copy-Item $exe $destino -Force
    $sizeMbDest = [math]::Round((Get-Item $destino).Length / 1MB, 1)
    Write-Host "Tambien queda aqui: $destino ($sizeMbDest MB)" -ForegroundColor Green
}
finally {
    Pop-Location
}
