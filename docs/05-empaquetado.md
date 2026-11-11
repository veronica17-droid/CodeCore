# Fase 5 — Empaquetado

**Estado:** preparado, **no ejecutado**
**Fecha:** 2026-11-11

> El `.exe` **no se ha generado**. Este documento deja listo el proceso y el
> comando exacto; la generación se hará solo cuando se autorice explícitamente.

## 1. Objetivo

Producir `dist\CodeCore.exe`: un único archivo ejecutable para Windows que incluya
Python, tkinter, el contenido JSON, la biblioteca y el icono. El usuario final no
instala nada y no ve una consola.

## 2. Requisitos del equipo de build

| Requisito | Valor probado |
|-----------|---------------|
| Sistema | Windows 10/11 x64 |
| Python | 3.12.10 (`%LOCALAPPDATA%\Programs\Python\Python312\python.exe`) |
| tkinter | 8.6 (incluido en el instalador de python.org) |
| PyInstaller | **pendiente de instalar** |
| Conexión | Solo para instalar PyInstaller y verificar URLs |

El usuario final **no necesita** ninguno de estos requisitos.

## 3. Instalar PyInstaller (una sola vez)

```powershell
$py = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
& $py -m pip install --upgrade pyinstaller
& $py -m PyInstaller --version
```

La versión exacta no se fija en el repositorio: se usa la última estable. Si se
quiere reproducibilidad total, anotar la versión instalada en el commit del build.

## 4. Comando exacto

Desde la raíz del repositorio:

```powershell
pyinstaller --noconfirm --clean --onefile --windowed --name CodeCore --icon resources\assets\codecore.ico --add-data "resources;resources" src\main.py
```

Equivalente usando el Python concreto (recomendado en este equipo):

```powershell
$py = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
& $py -m PyInstaller --noconfirm --clean --onefile --windowed --name CodeCore --icon resources\assets\codecore.ico --add-data "resources;resources" src\main.py
```

### 4.1 Qué hace cada opción

| Opción | Efecto |
|--------|--------|
| `--noconfirm` | No pregunta si debe borrar `build/` y `dist/` anteriores. |
| `--clean` | Limpia la caché de PyInstaller antes de compilar. |
| `--onefile` | Un solo `.exe`; los datos se extraen a una carpeta temporal al arrancar. |
| `--windowed` | Sin ventana de consola (equivalente a `--noconsole`). |
| `--name CodeCore` | Nombre del ejecutable y de la carpeta de trabajo. |
| `--icon resources\assets\codecore.ico` | Icono del `.exe` y de la ventana. |
| `--add-data "resources;resources"` | Copia `resources/` dentro del paquete (separador `;` en Windows). |
| `src\main.py` | Punto de entrada. |

### 4.2 Cómo encuentra la app sus recursos

`core/paths.py` resuelve las rutas así:

```python
base = Path(getattr(sys, "_MEIPASS", project_root()))
return base / "resources" / ...
```

- En desarrollo: `<repo>/resources/...`
- Empaquetado: `<carpeta temporal de --onefile>/resources/...`

Por eso `--add-data` debe conservar el nombre `resources`. Si se cambia, la app
arranca pero no encuentra el contenido y muestra un error legible.

## 5. Script de build

`tools/build_exe.ps1` automatiza el proceso **sin ejecutarse solo**:

```powershell
.\tools\build_exe.ps1
```

Pasos internos:

1. Localiza Python y comprueba que `tkinter` importa.
2. Comprueba que PyInstaller está instalado; si no, explica cómo instalarlo.
3. Ejecuta `tools/verify_content.py` (contenido y referencias).
4. Ejecuta las 51 pruebas (`unittest`).
5. Genera el icono si falta.
6. Lanza PyInstaller con el comando exacto.
7. Comprueba que `dist\CodeCore.exe` existe y muestra su tamaño.

Opciones:

```powershell
.\tools\build_exe.ps1 -SkipTests   # no recomendado: solo para depurar el empaquetado
.\tools\build_exe.ps1 -NoClean     # reutiliza la caché de PyInstaller
```

Si cualquier comprobación falla, el script se detiene y **no** genera el `.exe`.

Comprobado el 2026-11-11: sin PyInstaller instalado, el script se detiene con un
mensaje claro y no crea la carpeta `dist\`. Para ejecutar todas las comprobaciones
sin empaquetar existe `tools\check_all.ps1` (compilación, contenido, 51 pruebas y
smoke test); sale con código 0 solo si todo pasa.

## 6. Resultado esperado

```
dist\
  CodeCore.exe        ← único archivo a distribuir
build\                ← temporal, no se distribuye
CodeCore.spec         ← generado por PyInstaller, no se versiona
```

- El tamaño típico de un `--onefile` con tkinter ronda **10–20 MB**; el valor exacto
  depende de la versión de PyInstaller y de Python.
- `build/`, `dist/` y `*.spec` están en `.gitignore`.

## 7. Pruebas después de empaquetar

### 7.1 En el equipo de build

```powershell
.\dist\CodeCore.exe
```

- [ ] Abre sin consola y muestra la pantalla de inicio.
- [ ] El icono aparece en la barra de tareas y en la ventana.
- [ ] Las 3 rutas, las 13 lecciones y los 15 recursos están disponibles.
- [ ] Se puede completar una lección y el progreso se guarda.
- [ ] Cerrar y reabrir conserva el progreso.

Comprobación automática del ejecutable:

```powershell
.\dist\CodeCore.exe --selftest
```

Genera `CodeCore-selftest.txt` en el directorio actual (porque un `.exe` con
`--windowed` no tiene consola) con el resultado de cargar contenido y progreso.
Debe terminar en `SELFTEST OK`.

### 7.2 En una máquina limpia (sin Python)

- [ ] Copiar solo `CodeCore.exe` a una carpeta cualquiera.
- [ ] Ejecutar con doble clic.
- [ ] Comprobar que no pide instalar Python ni Visual C++.
- [ ] Comprobar que el progreso se crea en
      `%APPDATA%\CodeCore\progress.json`.
- [ ] Probar una lección de cada tipo: `code`, `choice` y `short`.
- [ ] Abrir un recurso de la biblioteca (requiere navegador e internet).
- [ ] Cerrar, reabrir y verificar que el progreso sigue ahí.

## 8. Avisos de Windows y antivirus

Un `.exe` de PyInstaller **sin firma digital** puede:

- mostrar **SmartScreen** («Windows protegió tu PC»): *Más información → Ejecutar de
  todas formas*;
- ser marcado por algún antivirus como falso positivo, porque el arranque de
  `--onefile` extrae un ejecutable a una carpeta temporal.

Opciones, de menor a mayor esfuerzo:

1. Distribuirlo con una nota clara sobre el aviso (suficiente para un prototipo).
2. Comprimir en `.zip` y publicar el hash SHA-256 junto al archivo.
3. Firmar el ejecutable con un certificado de código (de pago).

No se recomienda desactivar el antivirus ni pedir al usuario que lo haga.

## 9. Arranque lento en `--onefile`

Cada ejecución descomprime Python y los recursos en
`%TEMP%\_MEIxxxxx\`. El primer arranque puede tardar **1–3 segundos**. Es normal.
Si molestara, la alternativa es `--onedir` (carpeta con varios archivos), que
arranca más rápido pero deja de ser un único archivo.

## 10. Desinstalación

1. Borrar `CodeCore.exe`.
2. Borrar la carpeta `%APPDATA%\CodeCore\` (contiene `progress.json` y posibles
   copias `progress.corrupt-*.json`).

No se escribe nada en el registro de Windows ni se instalan servicios.

## 11. Solución de problemas

| Síntoma | Causa probable | Solución |
|---------|----------------|----------|
| `No module named PyInstaller` | No está instalado | `& $py -m pip install --upgrade pyinstaller` |
| `No module named tkinter` | Python sin tkinter | Reinstalar desde python.org marcando «tcl/tk» |
| El `.exe` arranca y cierra | Error de contenido o de arranque | Ejecutar `dist\CodeCore.exe --selftest` y revisar el `.txt` |
| «No se pudo iniciar CodeCore» | Falta `resources/` en el paquete | Revisar `--add-data "resources;resources"` |
| SmartScreen bloquea | Ejecutable sin firma | *Más información → Ejecutar de todas formas* |
| Antivirus lo pone en cuarentena | Falso positivo de PyInstaller | Restaurar y añadir exclusión; valorar firma |
| El icono no aparece | `.ico` inválido o ruta incorrecta | Regenerar con `tools\make_icon.py` |

## 12. Qué queda pendiente

- **Autorización para generar el `.exe`** y ejecutar las pruebas de la sección 7.
- Instalar PyInstaller en este equipo.
- Anotar la versión de PyInstaller usada y el hash del `.exe` en la entrega.
- Valorar metadatos de versión de Windows (`--version-file`) para que el archivo
  muestre nombre y versión en sus propiedades.
- Valorar firma digital si el prototipo se distribuye fuera del equipo.
