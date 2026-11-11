# CodeCore

Aplicación de escritorio para **aprender a programar pensando**, no memorizando.
Se entrega como un único `.exe` para Windows: doble clic, sin instalar Python, sin
terminal y sin configurar variables de entorno.

> Estado: en desarrollo por fases. Consulta [`docs/`](docs/) para el detalle de cada fase.

## Qué hace

- Pregunta tu nivel al arrancar (**principiante / intermedio / avanzado**) y adapta
  el contenido, las pistas y la exigencia de los ejercicios.
- Recorrido de lecciones con estructura fija: **problema → guía de razonamiento →
  ejercicio → retroalimentación**.
- Editor de código integrado con validación de sintaxis (sin ejecutar tu código).
- Biblioteca local de libros, vídeos y documentación oficial, con búsqueda y filtros.
- Progreso persistente en `%APPDATA%\CodeCore\progress.json`.

## Requisitos (solo para desarrollar)

- Windows 10/11 x64
- Python 3.10+ (probado con 3.12) — el instalador oficial de python.org incluye tkinter
- PyInstaller (solo para generar el `.exe`)

El usuario final **no necesita nada de esto**: recibe un `.exe` autocontenido.

## Ejecutar en desarrollo

```powershell
cd CodeCore
.\tools\run_dev.ps1
```

o directamente:

```powershell
python src\main.py
```

## Ejecutar las pruebas

```powershell
python -m unittest discover -s tests -v
```

## Generar el `.exe`

```powershell
.\tools\build_exe.ps1
```

El resultado queda en `dist\CodeCore.exe`. El comando exacto de PyInstaller y las
pruebas en una máquina limpia están en [`docs/05-empaquetado.md`](docs/05-empaquetado.md).

## Estructura

```
src/        código fuente (core sin GUI + ui con tkinter)
resources/  lecciones y biblioteca en JSON + icono
tests/      pruebas automatizadas con unittest
tools/      scripts de desarrollo y empaquetado
docs/       documentación de cada fase
```

## Documentación por fase

| Fase | Documento |
|------|-----------|
| 0 | [Arquitectura y estructura](docs/00-arquitectura.md) |
| 1 | [Diseño y modelo de datos](docs/01-diseno.md) |
| 2 | [Núcleo](docs/02-nucleo.md) |
| 3 | [Interfaz](docs/03-interfaz.md) |
| 4 | [Recursos](docs/04-recursos.md) |
| 5 | [Empaquetado](docs/05-empaquetado.md) · [Pruebas](docs/06-pruebas.md) |
| 6 | [Git](docs/07-git.md) |

## Limitaciones conocidas

- El código del usuario **no se ejecuta**: se valida sintaxis y estructura. Es una
  decisión de seguridad y de instalación (ver `docs/00-arquitectura.md`).
- Un `.exe` sin firma digital puede provocar un falso positivo de antivirus o un
  aviso de SmartScreen. Detalle y solución en `docs/05-empaquetado.md`.
