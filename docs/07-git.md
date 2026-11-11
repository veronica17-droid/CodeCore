# Fase 6 — Git y publicación

**Estado:** completada
**Fecha:** 2026-11-11
**Repositorio:** <https://github.com/veronica17-droid/CodeCore>

## 1. Qué se hizo

- Se trabajó sobre una rama única, `main`, con **un commit por fase**.
- Se configuró la identidad **solo en este repositorio** (no global).
- Se versionaron el código, el contenido JSON, los recursos, las pruebas, las
  herramientas y la documentación.
- Se excluyeron los artefactos de build, los datos de usuario y los archivos
  temporales mediante `.gitignore`.
- Se normalizaron los finales de línea con `.gitattributes` para que el repositorio
  se comporte igual en Windows, Linux y macOS.
- Se publicó el historial completo en GitHub y se comprobó que la referencia
  remota coincide exactamente con el `HEAD` local.

## 2. Identidad y remoto

```powershell
git config user.name  "VERO"
git config user.email "veronicacarvajalcardona17@gmail.com"
```

| Elemento | Valor |
|----------|-------|
| Remoto | `origin` → `https://github.com/veronica17-droid/CodeCore.git` |
| Rama principal | `main` |
| Seguimiento | `main` → `origin/main` |
| Autenticación | Git Credential Manager (una vez, en el navegador) |

La identidad es **local al repositorio**: no se modificó la configuración global de
Git del equipo. Para replicarla en otro clon:

```powershell
git config user.name  "VERO"
git config user.email "veronicacarvajalcardona17@gmail.com"
```

## 3. Historial de fases

| Fase | Commit | Mensaje |
|------|--------|---------|
| 0 | `d82d5e2` | `fase-0: estructura del proyecto, gitignore y documentacion de arquitectura` |
| 1 | `05c42d0` | `fase-1: modelo de datos y contenido de los tres niveles` |
| 2 | `9cc5351` | `fase-2: nucleo de contenido, evaluacion, progreso y busqueda con pruebas` |
| 3 | `70acbd1` | `fase-3: interfaz tkinter, editor, biblioteca, progreso e icono` |
| 4 | `ae892bd` | `fase-4: biblioteca de 15 recursos verificados y validador de URLs` |
| 5 | `934da70` | `fase-5: documentacion de empaquetado, pruebas de seguridad y scripts de verificacion` |
| 6 | este commit | `fase-6: documentacion de Git y publicacion en GitHub` |

Cada commit incluye **su documentación de fase** en `docs/`, de modo que el
historial cuenta la misma historia que la carpeta `docs/`.

## 4. Convención de commits

```
fase-N: resumen en español, en minúsculas y sin punto final
```

- Un commit por fase, no uno por archivo.
- El resumen dice **qué se entrega**, no «cambios varios».
- Si una fase necesita contexto, se añade un cuerpo breve explicando decisiones.
- Antes de commitear se ejecuta `tools\check_all.ps1`; no se commitea en rojo.
- No se commitean artefactos generados (`build/`, `dist/`, `*.spec`).
- No se reescribe el historial ya publicado (`rebase`, `amend` o `push --force`)
  salvo que sea imprescindible y esté acordado.

## 5. Qué se versiona y qué no

| Se versiona | No se versiona |
|-------------|----------------|
| `src/` (código y GUI) | `build/`, `dist/`, `*.spec` |
| `resources/` (JSON e icono) | `__pycache__/`, `*.pyc` |
| `tests/` | `.venv/`, `venv/` |
| `tools/` (scripts reproducibles) | `progress.json` y copias locales |
| `docs/`, `README.md` | `*.log`, `*.tmp` |
| `.gitignore`, `.gitattributes` | `.vscode/`, `.idea/` |

El progreso del usuario vive en `%APPDATA%\CodeCore\progress.json` y **nunca** se
sube al repositorio: es dato personal y de máquina.

## 6. Cómo se verifica

```powershell
cd CodeCore

# 1. El árbol de trabajo está limpio y en la rama correcta.
git status --short --branch

# 2. El historial tiene un commit por fase.
git log --oneline --decorate

# 3. La rama remota apunta al mismo commit que el HEAD local.
git ls-remote --heads origin
git rev-parse HEAD
```

Resultado esperado: `git status` muestra `## main...origin/main` sin cambios, y el
hash de `refs/heads/main` coincide con `git rev-parse HEAD`.

Comprobación del 2026-11-11 tras la primera publicación:

```
934da70dd106f34bd70408179daed0b8e2d8949e    refs/heads/main
934da70dd106f34bd70408179daed0b8e2d8949e    (HEAD local)
```

## 7. Primera publicación

```powershell
git push -u origin main
```

- Git Credential Manager abre el navegador **una sola vez** para autorizar la
  cuenta; después reutiliza la credencial.
- No hace falta `gh` (GitHub CLI): no está instalado en este equipo y no es un
  requisito del proyecto.
- En entornos automatizados conviene `$env:GIT_TERMINAL_PROMPT = "0"` para que Git
  falle con un mensaje claro en vez de quedarse esperando una contraseña.

## 8. Flujo para las siguientes fases

```powershell
# 1. Verificar antes de commitear.
.\tools\check_all.ps1

# 2. Revisar qué entra en el commit.
git status --short

# 3. Añadir solo lo que corresponde a la fase.
git add src resources tests tools docs README.md

# 4. Commit con el formato acordado.
git commit -m "fase-N: resumen breve"

# 5. Publicar y verificar.
git push
git status --short --branch
```

## 9. Incidencias encontradas

| Incidencia | Causa | Solución |
|------------|-------|----------|
| Aviso «LF will be replaced by CRLF» en los `.ps1` | `.gitattributes` fuerza CRLF en PowerShell | Es el comportamiento deseado; se ignora el aviso. |
| `check_all.ps1` salía con código 1 aunque todo pasaba | PowerShell interpretaba el stderr de `unittest` como error fatal | Se decide el resultado con `$LASTEXITCODE` y se filtra la salida nativa. |
| `git ls-remote` sin salida | El repositorio remoto aún no tenía ramas | Es normal antes de la primera publicación; el código de salida era 0. |
| `gh` no disponible | GitHub CLI no está instalado | Se usa Git + Git Credential Manager; `gh` es opcional. |

## 10. Qué queda pendiente

- **Publicar el `.exe` como *release* de GitHub**, no como archivo versionado. Se
  generará solo cuando se autorice (ver `docs/05-empaquetado.md`) y se adjuntará
  junto a su hash SHA-256.
- **Proteger `main`** (requerir *pull request* o al menos revisión) si el proyecto
  pasa a tener más de una persona.
- **Integración continua** (por ejemplo, GitHub Actions en Windows) para ejecutar
  `tools\check_all.ps1` en cada push. Hoy las comprobaciones son locales.
- **Etiquetas de versión** (`v0.1.0`, `v0.2.0`…) cuando exista una entrega estable.
- **Firma de commits** si se quiere verificar la autoría; no es necesaria para el
  prototipo.
