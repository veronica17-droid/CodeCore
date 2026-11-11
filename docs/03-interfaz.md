# Fase 3 — Interfaz gráfica

**Estado:** completada
**Fecha:** 2026-11-11

## 1. Qué se hizo

Se construyó la interfaz completa con **tkinter/ttk** (solo biblioteca estándar).
La GUI no contiene reglas pedagógicas: consume el núcleo de la Fase 2 y se limita a
presentar, capturar respuestas y persistir progreso.

| Archivo | Responsabilidad |
|---------|-----------------|
| `src/main.py` | Punto de entrada, `--version`, `--selftest`, avisos de arranque. |
| `src/app.py` | Ventana principal, barra lateral, navegación y estado compartido. |
| `src/ui/theme.py` | Paleta, tipografía y estilos ttk. |
| `src/ui/widgets.py` | Botones, tarjetas, badges, barras y área desplazable. |
| `src/ui/editor.py` | Editor de código con números de línea, indentación y resaltado. |
| `src/ui/welcome_view.py` | Selección de nivel y tarjeta «continuar donde lo dejaste». |
| `src/ui/path_view.py` | Ruta del nivel, progreso y tarjetas de lección. |
| `src/ui/lesson_view.py` | Flujo problema → guía → ejercicio → feedback. |
| `src/ui/library_view.py` | Biblioteca con búsqueda y filtros combinables. |
| `src/ui/progress_view.py` | Progreso global, por nivel, detalle y reinicio. |
| `src/ui/about_view.py` | Acerca de, ruta del progreso, atajos y limitaciones. |
| `tools/run_dev.ps1` | Lanzador de desarrollo. |
| `tools/make_icon.py` | Genera `resources/assets/codecore.ico` sin dependencias. |
| `tools/smoke_gui.py` | Recorre toda la interfaz y valida las soluciones de ejemplo. |

## 2. Estructura de la ventana

```
┌──────────────┬──────────────────────────────────────────────┐
│  CodeCore    │  contenido de la vista actual                │
│              │                                              │
│  Inicio      │  (scroll vertical cuando hace falta)         │
│  Mi ruta     │                                              │
│  Biblioteca  │                                              │
│  Progreso    │                                              │
│  Acerca de   │                                              │
│              │                                              │
│  PROGRESO    │                                              │
│  42%         │                                              │
│  ▓▓▓▓░░░░    │                                              │
│  5 de 13     │                                              │
└──────────────┴──────────────────────────────────────────────┘
```

- **Barra lateral fija** (240 px): navegación y progreso total siempre visible.
- **Área de contenido** sustituible: una sola vista viva a la vez; al navegar se
  destruye la anterior, de modo que no se acumulan widgets ni callbacks.
- La ventana mide 1180×760, con mínimo de 960×640, y se centra al abrir.

### 2.1 Navegación

| Tecla | Vista |
|-------|-------|
| `Ctrl+1` | Inicio |
| `Ctrl+2` | Mi ruta |
| `Ctrl+3` | Biblioteca |
| `Ctrl+4` | Progreso |
| `Ctrl+5` | Acerca de |

Cada vista se implementa como una subclase de `tk.Frame` que recibe `(parent, app)`.
`CodeCoreApp.navigate()` centraliza la creación y destrucción de vistas.

## 3. Las cuatro pantallas de una lección

La lección no es un muro de texto: se recorre en pasos con un *stepper* clicable.

1. **Problema** — escenario, pregunta destacada, restricciones y una reflexión.
   Un aviso explícito indica que todavía no hay que escribir código.
2. **Guía** — modelo mental, pasos, preguntas socráticas y errores comunes.
   Nunca contiene la solución.
3. **Ejercicio** — editor de código, opciones de elección o respuesta corta,
   pistas progresivas y, solo tras 3 intentos, una solución posible.
4. **Feedback** — puntaje, resumen, comprobaciones una a una con su mensaje,
   error de sintaxis con línea/columna y siguiente pista.

### 3.1 Comportamiento por tipo de ejercicio

| Tipo | Captura | Detalle de interfaz |
|------|---------|---------------------|
| `code` | Editor con resaltado | Números de línea, `Tab` = 4 espacios, `Enter` conserva indentación y la amplía tras `:`. |
| `choice` | Radiobuttons | La opción marcada se conserva al cambiar de paso. |
| `short` | Caja de texto | Contador en vivo de palabras e ideas clave requeridas. |

### 3.2 Pistas y solución

- Las pistas se revelan de una en una con el botón «Ver pista (n/total)».
- En nivel **avanzado** el botón avisa si aún no se han hecho dos intentos.
- La solución solo aparece a partir del **tercer intento**; antes se muestra por qué
  está bloqueada. Esto evita convertir el ejercicio en «copiar y pegar».
- Un envío vacío no cuenta como intento: se avisa y se permanece en el ejercicio.

## 4. Editor de código

`CodeEditor` es un `tk.Text` con una columna de números sincronizada:

- Resaltado por expresiones regulares para **palabras clave, cadenas, comentarios y
  números**. Se reprograma con `after(120)` para no repintar en cada tecla.
- `Tab` inserta cuatro espacios y **no** cambia el foco (evita el error clásico de
  perder el foco en un formulario).
- `Shift+Tab` quita hasta cuatro espacios al inicio de la línea.
- `Enter` mantiene la indentación actual y añade cuatro espacios si la línea termina
  en `:`.
- `Ctrl+Z` / `Ctrl+Y` funcionan gracias a `undo=True`.
- El texto **nunca se ejecuta**: solo se envía a `core.feedback.evaluate`.

## 5. Decisiones de interfaz

### 5.1 Sin dependencias externas

Todo se dibuja con tkinter/ttk y `tk.Canvas`. No se usa Pillow, customtkinter ni
fuentes descargadas. Consecuencias:

- El `.exe` no necesita recursos binarios adicionales (salvo el icono).
- La app funciona en un Windows recién instalado.
- El aspecto es sobrio y consistente, no «nativo» al 100 %.

### 5.2 El progreso se guarda en cada acción relevante

- Al abrir una lección se marca `in_progress`.
- Al comprobar una respuesta se registra el intento y se guarda.
- Al elegir nivel, reiniciar un nivel o borrar todo, se guarda de inmediato.
- Al cerrar la ventana (`WM_DELETE_WINDOW`) se guarda una última vez.

### 5.3 Los errores no cierran la app en silencio

- `report_callback_exception` muestra un `messagebox` con el tipo de error y aclara
  que el progreso guardado sigue intacto.
- Si el contenido JSON está dañado, `main.py` muestra un aviso legible antes de
  crear la ventana principal.
- Si falla el guardado (permisos, disco lleno), se avisa **una sola vez** y la app
  continúa funcionando.

### 5.4 Accesibilidad y legibilidad

- Contraste alto texto/fondo en todas las vistas.
- Tamaños de fuente escalonados (9–26 px) y `wraplength` para evitar líneas largas.
- Los botones tienen estados hover y `cursor="hand2"`.
- Las pantallas largas usan `ScrollFrame` con rueda del ratón propagada a los hijos.

## 6. Icono

`tools/make_icon.py` dibuja el icono con un rasterizador propio (cuadrado redondeado
oscuro y los símbolos `< / >`) y escribe un `.ico` con seis tamaños:
16, 32, 48, 64, 128 y 256 px, con PNG embebido.

```powershell
python tools\make_icon.py
```

Salida esperada:

```
Icono generado: ...\resources\assets\codecore.ico (7687 bytes)
```

`CodeCoreApp._set_icon()` lo carga con `iconbitmap` y **ignora** el fallo si el
archivo no existe, para que la app nunca deje de arrancar por el icono.

## 7. Cómo se verifica

### 7.1 Compilación y pruebas del núcleo

```powershell
cd CodeCore
$py = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
& $py -m compileall -q src tools tests
& $py -X utf8 -m unittest discover -s tests
```

Resultado esperado: `Ran 46 tests ... OK` (45 del núcleo + la comprobación de que
cada solución de ejemplo supera sus propios checks).

### 7.2 Smoke test de la interfaz

```powershell
& $py -X utf8 tools\smoke_gui.py
```

Qué hace:

1. Evalúa la solución de ejemplo de las **13 lecciones** contra sus checks.
2. Instancia `CodeCoreApp` con un archivo de progreso temporal.
3. Recorre Inicio, las tres rutas, Biblioteca, Progreso y Acerca de.
4. Abre cada lección, recorre sus cuatro pasos y comprueba la respuesta correcta.

Resultado esperado:

```
Soluciones comprobadas: 13 | fallos: 0
Vistas y lecciones recorridas sin errores: 13 lecciones
```

> El smoke test usa una sesión gráfica de Windows, pero oculta la ventana con
> `withdraw()`. No modifica el progreso real del usuario.

### 7.3 Comprobación manual

```powershell
.\tools\run_dev.ps1
```

Checklist:

- [ ] Al abrir aparece Inicio con la pregunta de nivel y las tres tarjetas.
- [ ] Elegir un nivel lleva a su ruta y marca la tarjeta como «Nivel actual».
- [ ] Abrir una lección muestra Problema; el *stepper* permite saltar a Guía y Ejercicio.
- [ ] En el editor, `Tab`, `Enter` tras `:` y `Ctrl+Z` se comportan como se describe.
- [ ] «Comprobar respuesta» muestra puntaje, checks y pista.
- [ ] Tras 3 intentos aparece «Ver una solución posible».
- [ ] Biblioteca busca sin acentos y los filtros se combinan.
- [ ] Progreso muestra el porcentaje y el detalle por lección.
- [ ] Cerrar y volver a abrir conserva el progreso y la última lección.
- [ ] `Ctrl+1…5` cambia de vista.

## 8. Incidencias encontradas y corregidas

| Incidencia | Causa | Corrección |
|------------|-------|------------|
| `beg_01_orden` daba 67 % con su propia solución | El check usaba `cierr` y la solución dice `Cerrar` | Regex cambiada a `cerr\w*` |
| El validador de contenido avisaba de 15 recursos | La biblioteca se crea en la Fase 4 | El aviso no falla mientras no exista biblioteca |

La primera incidencia la detectó el smoke test y ahora la cubre una prueba
permanente (`test_every_solution_passes_its_own_checks`).

## 9. Qué queda pendiente

- Crear `resources/library/resources.json` con los 15 recursos referenciados y
  verificar sus URLs (Fase 4).
- Documentar y ejecutar el empaquetado; **no generar el `.exe` hasta autorización**
  (Fase 5).
- Evaluar un tema claro/oscuro conmutable (la paleta ya está centralizada en
  `theme.py`).
- Añadir pruebas de interfaz automatizadas con captura de pantalla (opcional;
  requeriría una dependencia externa y no es imprescindible para el prototipo).
- Revisar el comportamiento con escalado de Windows al 150 %/200 % en una máquina
  física.
