# Fase 0 — Arquitectura y estructura de carpetas

**Estado:** completada
**Fecha:** 2026-11-11

## 1. Objetivo de la fase

Definir una base técnica que permita construir el prototipo por capas, con una
separación clara entre lógica y presentación, y que desemboque en **un único `.exe`
para Windows sin instalación ni configuración**.

## 2. Decisiones tecnológicas

| Área | Decisión | Por qué |
|------|----------|---------|
| Lenguaje | **Python 3.12 x64** | Sintaxis legible para material didáctico, biblioteca estándar muy completa y empaquetado maduro. |
| GUI | **tkinter / ttk** | Incluido en el instalador oficial de Python. Cero dependencias externas en runtime, cero instaladores adicionales para el usuario final. |
| Datos | **JSON en `resources/`** | Contenido editable sin recompilar, validable con tests y fácil de versionar en Git (diffs legibles). |
| Persistencia | **JSON en `%APPDATA%\CodeCore\`** | Directorio de usuario escribible sin permisos de administrador y estable entre actualizaciones del `.exe`. |
| Empaquetado | **PyInstaller `--onefile --windowed`** | Un solo archivo, sin consola negra, sin instalador, sin variables de entorno. |
| Pruebas | **`unittest` (stdlib)** | No añade dependencias; se ejecuta con el mismo Python del proyecto. |
| Red | **Ninguna en runtime** | La app funciona offline; la biblioteca es local y los enlaces se abren en el navegador del sistema. |

### Por qué no otras alternativas

- **Electron:** ~150 MB, runtime de Chromium y un instalador o carpeta con muchos
  archivos. Contradice el requisito de "un `.exe`, doble clic".
- **Tauri:** necesita WebView2 en la máquina y un toolchain de Rust para compilar.
- **.NET WinForms/WPF:** o exige runtime instalado o genera un self-contained de
  ~70 MB; además ata el contenido didáctico a otro ecosistema.
- **Navegador + servidor local:** requiere abrir un puerto y explicar al usuario algo
  más que "doble clic".

## 3. Estructura de carpetas

```
CodeCore/
├── src/
│   ├── main.py                  # punto de entrada; flags --selftest / --version
│   ├── app.py                   # ventana raíz, router de vistas, navegación
│   ├── config.py                # constantes, versión, rutas, colores base
│   ├── core/                    # lógica pura: no importa tkinter
│   │   ├── models.py            # dataclasses del dominio
│   │   ├── content.py           # carga y validación de lecciones/niveles
│   │   ├── progress.py          # persistencia atómica y migraciones
│   │   ├── feedback.py          # evaluación de ejercicios y mensajes
│   │   ├── search.py            # búsqueda local normalizada
│   │   └── paths.py             # recursos en dev vs. sys._MEIPASS
│   └── ui/                      # solo presentación
│       ├── theme.py             # paleta, fuentes, estilos ttk
│       ├── widgets.py           # componentes reutilizables
│       ├── welcome_view.py      # selección de nivel
│       ├── path_view.py         # ruta de aprendizaje
│       ├── lesson_view.py       # problema → guía → ejercicio → feedback
│       ├── editor.py            # editor de código con números de línea
│       ├── library_view.py      # biblioteca con búsqueda y filtros
│       ├── progress_view.py     # panel de progreso
│       └── about_view.py        # información y mantenimiento
├── resources/
│   ├── content/
│   │   ├── levels.json
│   │   ├── lessons_beginner.json
│   │   ├── lessons_intermediate.json
│   │   └── lessons_advanced.json
│   ├── library/resources.json
│   └── assets/codecore.ico
├── tests/                       # unittest, sin GUI
├── tools/
│   ├── run_dev.ps1
│   ├── build_exe.ps1
│   └── verify_content.py
├── docs/                        # esta documentación
├── README.md
├── requirements-dev.txt
├── .gitignore
└── .gitattributes
```

### Regla de dependencias

```
ui/  ──>  core/  ──>  resources/ (JSON)
 │          │
 └──────────┴──>  config.py
```

- `core/` **nunca** importa `tkinter` ni `ui/`. Es lógica testeable sin pantalla.
- `ui/` no lee archivos JSON directamente: pide datos a `core/`.
- `config.py` solo contiene constantes; no depende de nadie.

Esto permite probar la evaluación de ejercicios, la persistencia y la búsqueda sin
abrir una ventana, y cambiar la GUI sin tocar las reglas del juego.

## 4. Flujo de datos

```
main.py
  └─> app.py (crea ventana y router)
        ├─> welcome_view  ──> progress.set_level()
        ├─> path_view     <── content.lessons_for_level()
        ├─> lesson_view   <── content.get_lesson()
        │      └─> feedback.evaluate() ──> progress.record_attempt()
        ├─> library_view  <── content.resources() + search.filter()
        └─> progress_view <── progress.summary()
```

El progreso se guarda tras cada intento y al cerrar la ventana. Si el guardado falla,
la app sigue funcionando y avisa al usuario sin perder la sesión en memoria.

## 5. Resolución de rutas (desarrollo vs. `.exe`)

PyInstaller `--onefile` descomprime los datos en una carpeta temporal expuesta en
`sys._MEIPASS`. `core/paths.py` centraliza la diferencia:

```python
def resource_path(*parts: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
    return base.joinpath("resources", *parts)
```

- En desarrollo: `<repo>/resources/...`
- En el `.exe`: `<temporal>/resources/...` (incluido con `--add-data "resources;resources"`)

Nunca se escribe dentro de esa carpeta: el progreso va siempre a `%APPDATA%`.

## 6. Persistencia

- Ruta: `%APPDATA%\CodeCore\progress.json`
  (fallback: `~/.codecore/progress.json` si `APPDATA` no existe).
- **Escritura atómica:** se escribe `progress.json.tmp` y se reemplaza con
  `os.replace()`, evitando archivos a medio escribir si se corta la luz.
- **Recuperación:** si el JSON está corrupto, se renombra a
  `progress.corrupt-<fecha>.json` y se empieza de cero sin borrar la evidencia.
- **Versionado:** campo `schema_version` para migrar formatos antiguos.
- **Sin datos personales:** no se pide nombre, correo ni conexión a internet.

## 7. Evaluación de ejercicios (sin ejecutar código)

Decisión deliberada: **el código del usuario no se ejecuta**.

1. `ast.parse()` valida sintaxis y señala línea/columna del error.
2. Comprobaciones declarativas en JSON: `contains`, `not_contains`, `regex`,
   `expected_output`, `uses_concept`.
3. Cada check tiene un mensaje de fallo que explica el razonamiento, no solo "mal".
4. Puntaje parcial: 0–100 según checks superados; se guarda el mejor resultado.

Ventajas: determinista, offline, instantáneo y sin riesgo de ejecutar código ajeno.
Limitación documentada: no detecta errores lógicos que produzcan la salida esperada
por casualidad; se compensa con checks estructurales y preguntas de razonamiento.

## 8. Empaquetado (documentado, no ejecutado aún)

```powershell
pyinstaller --noconfirm --clean --onefile --windowed `
  --name CodeCore `
  --icon resources\assets\codecore.ico `
  --add-data "resources;resources" `
  src\main.py
```

- `--onefile`: un único `.exe`.
- `--windowed`: sin consola negra.
- `--add-data "resources;resources"`: contenido y biblioteca dentro del binario.
- `--clean`: evita artefactos viejos de `build/`.

`build/`, `dist/` y `*.spec` están en `.gitignore`; el comando es reproducible y
queda documentado en `docs/05-empaquetado.md`.

## 9. Convenciones

- **Idioma de la UI y del contenido:** español.
- **IDs:** `snake_case` estables (`beg_variables`, `res_python_tutorial`). Nunca se
  renombran una vez publicados, porque el progreso guardado los referencia.
- **JSON:** UTF-8 sin BOM, indentación de 2 espacios, claves en `snake_case`.
- **Errores:** mensajes para el usuario en español; detalles técnicos solo en consola
  de desarrollo (`--debug`), nunca en la UI final.
- **Commits:** `fase-N: descripción` (ver `docs/07-git.md`).

## 10. Cómo se verifica esta fase

```powershell
# 1. La estructura existe
Get-ChildItem CodeCore -Directory | Select-Object Name

# 2. El .gitignore cubre los artefactos de build
Select-String -Path CodeCore\.gitignore -Pattern 'build/','dist/','\*.spec'

# 3. Git no ve basura (cuando exista el repo)
git -C CodeCore status --short

# 4. La documentación está enlazada
Get-ChildItem CodeCore\docs
```

Checklist:

- [x] `src/`, `docs/`, `resources/`, `tests/`, `tools/` creados.
- [x] `.gitignore` excluye `build/`, `dist/`, `*.spec`, `__pycache__/`, `.venv/`.
- [x] `.gitattributes` normaliza finales de línea.
- [x] `README.md` explica qué es, cómo ejecutar y cómo compilar.
- [x] Regla de dependencias `ui → core → resources` documentada.

## 11. Qué queda pendiente

- Crear `levels.json` y el esquema de lecciones (Fase 1).
- Implementar `core/` y sus tests (Fase 2).
- Construir la GUI (Fase 3).
- Curar la biblioteca y verificar las URLs (Fase 4).
- Instalar PyInstaller y generar el `.exe` **solo cuando el usuario lo autorice** (Fase 5).
- Inicializar el repositorio, configurar identidad y subir a `main` (Fase 6).
