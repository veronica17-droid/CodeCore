# Fase 5 — Pruebas

**Estado:** completada (pruebas de desarrollo)
**Fecha:** 2026-11-11

## 1. Estrategia

CodeCore se prueba en cuatro capas, de más rápida a más lenta:

| Capa | Herramienta | Qué demuestra |
|------|-------------|----------------|
| 1. Unidad | `unittest` (51 pruebas) | Contenido, evaluación, progreso, búsqueda y seguridad. |
| 2. Contenido | `tools/verify_content.py` | Esquema, referencias y URLs reales. |
| 3. Interfaz | `tools/smoke_gui.py` | La app arranca, navega y evalúa las 13 lecciones. |
| 4. Manual | Checklist | Legibilidad, atajos y comportamiento real de Windows. |

La capa 4 se completa cuando se genere el `.exe` (ver `docs/05-empaquetado.md`).

## 2. Cómo ejecutar todo

```powershell
cd CodeCore
.\tools\check_all.ps1
```

El script compila, valida el contenido, ejecuta las pruebas y lanza el smoke test.
Sale con código 0 solo si todo pasa.

Comandos individuales:

```powershell
$py = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"

& $py -m compileall -q src tools tests
& $py -X utf8 -m unittest discover -s tests -v
& $py -X utf8 tools\verify_content.py
& $py -X utf8 tools\verify_content.py --check-urls
& $py -X utf8 tools\smoke_gui.py
```

## 3. Pruebas de unidad (51)

| Archivo | Pruebas | Cobertura |
|---------|---------|-----------|
| `tests/test_content.py` | 14 | Carga, orden de niveles, rutas, ids únicos, navegación, biblioteca, recursos por lección, JSON inválido y duplicados. |
| `tests/test_feedback.py` | 17 | Aciertos, fallos, sintaxis, `count`, `regex`, `ast`, elección, respuesta corta y pistas por nivel. |
| `tests/test_progress.py` | 9 | Estado inicial, intentos, mejor puntaje, round-trip, corrupción, `schema_version` futuro, resumen y reinicio. |
| `tests/test_search.py` | 9 | Acentos, mayúsculas, filtros por tipo/lenguaje/nivel, orden y combinación. |
| `tests/test_security.py` | 2 | `feedback.py` no usa `eval`/`exec`/`subprocess`; código malicioso no se ejecuta. |

Resultado esperado:

```
Ran 51 tests in 0.08s
OK
```

### 3.1 Casos límite cubiertos

- **Lista vacía** en el ejercicio de promedio (guarda antes de dividir).
- **Sintaxis inválida**: puntaje 0 y mensaje con línea y columna.
- **Respuesta vacía**: no se registra como intento desde la interfaz; el núcleo la
  rechaza con un mensaje.
- **Umbral 70**: 3 de 4 checks (75) aprueban; 2 de 3 (67) no.
- **`ast` con `max: 0`**: prohíbe un nodo (por ejemplo, `while` en recursión).
- **Pistas**: en avanzado no aparecen antes del segundo intento; nunca se desbordan.
- **Solución**: solo se revela a partir del tercer intento.
- **Progreso corrupto**: se renombra a `progress.corrupt-AAAAMMDD-HHMMSS.json` y se
  empieza limpio sin borrar la evidencia.
- **`schema_version` futuro**: mismo tratamiento que un archivo corrupto.
- **Acentos**: `depuracion` encuentra `Depuración`.
- **Escritura atómica**: no queda `progress.json.tmp` tras guardar.

### 3.2 Contenido como prueba

Además de las pruebas de unidad, se valida que **cada solución de ejemplo supera
sus propios checks**. Esta prueba encontró un fallo real en `beg_01_orden` (la
regex esperaba `cierr` y la solución dice `Cerrar`) y evita que vuelva a ocurrir.

## 4. Validación de contenido y URLs

```powershell
& $py -X utf8 tools\verify_content.py --check-urls
```

Comprueba:

- 3 niveles, 13 lecciones y 15 recursos;
- todos los `resource_ids` existen;
- tipos de ejercicio y de recurso válidos;
- una sola opción correcta en `choice`;
- `min_words`/`min_keywords` coherentes en `short`;
- cada URL responde (200). Usa `HEAD` y reintenta con `GET` si el servidor rechaza
  `HEAD` con 403/405.

Resultado del 2026-11-11: **15/15 URLs con HTTP 200**.

## 5. Smoke test de interfaz

```powershell
& $py -X utf8 tools\smoke_gui.py
```

Qué demuestra:

1. Las 13 soluciones de ejemplo pasan sus checks.
2. `CodeCoreApp` se instancia con un progreso temporal (no toca el real).
3. Se recorren Inicio, las 3 rutas, Biblioteca, Progreso y Acerca de.
4. Se abre cada lección, se recorren sus 4 pasos y se evalúa la respuesta correcta.

Resultado esperado:

```
Soluciones comprobadas: 13 | fallos: 0
Vistas y lecciones recorridas sin errores: 13 lecciones
```

Este test detecta errores de Tkinter (opciones inválidas, widgets destruidos,
`after` pendientes) sin necesidad de una persona mirando la pantalla.

## 6. Checklist manual (desarrollo)

Ejecutar `.\tools\run_dev.ps1` y comprobar:

### 6.1 Arranque y navegación

- [ ] La ventana abre centrada, sin consola, con el icono de CodeCore.
- [ ] Inicio pregunta el nivel y muestra tres tarjetas.
- [ ] Elegir nivel abre su ruta y actualiza la barra lateral.
- [ ] `Ctrl+1…5` cambia entre las cinco vistas.
- [ ] La barra lateral muestra el porcentaje global correcto.

### 6.2 Lección

- [ ] Problema muestra escenario, pregunta, restricciones y reflexión.
- [ ] Guía muestra modelo mental, pasos, preguntas y errores comunes.
- [ ] Ejercicio muestra el editor, opciones o caja de texto según el tipo.
- [ ] `Tab` inserta 4 espacios y no cambia el foco.
- [ ] `Enter` tras `:` añade sangría.
- [ ] `Ctrl+Z` deshace y `Ctrl+Y` rehace.
- [ ] «Ver pista» revela una pista cada vez.
- [ ] «Comprobar respuesta» muestra puntaje, checks y pista.
- [ ] Un envío vacío avisa y no cuenta como intento.
- [ ] Tras 3 intentos aparece «Ver una solución posible».
- [ ] Al aprobar, «Siguiente lección» avanza y el progreso se guarda.

### 6.3 Biblioteca

- [ ] Muestra «15 recursos» sin filtros.
- [ ] Buscar `depuracion` encuentra «Think Python».
- [ ] Buscar `cobol` muestra el estado vacío.
- [ ] Los filtros de tipo, lenguaje y nivel se combinan.
- [ ] «Abrir ↗» lanza el navegador con la URL correcta.
- [ ] Real Python no muestra la insignia «Gratis».

### 6.4 Progreso y persistencia

- [ ] El detalle lista las 13 lecciones con intentos y mejor puntaje.
- [ ] Reiniciar un nivel conserva los otros niveles.
- [ ] Borrar todo pide confirmación y vuelve al inicio.
- [ ] Cerrar y reabrir conserva nivel, última lección y respuestas.

### 6.5 Resiliencia

- [ ] Renombrar `progress.json` mientras la app está cerrada no impide arrancar.
- [ ] Un `progress.json` corrupto genera una copia y la app sigue.
- [ ] Abrir «Acerca de → Abrir carpeta» abre `%APPDATA%\CodeCore`.
- [ ] Con la ventana pequeña (960×640) no hay controles inaccesibles.

## 7. Seguridad

- El código del usuario **nunca se ejecuta**: `ast.parse` + checks declarativos.
- `tests/test_security.py` verifica por AST que `feedback.py` no llama a
  `eval`, `exec`, `compile` ni `__import__`, y que no importa `subprocess`.
- Una respuesta maliciosa se analiza, no se ejecuta; la prueba comprueba que no
  crea un archivo marcador.
- No hay red en tiempo de ejecución salvo cuando el usuario pulsa «Abrir ↗».
- No se recogen datos personales; el progreso es local.

## 8. Criterios de aceptación del prototipo

| Criterio | Estado |
|----------|--------|
| Pregunta el nivel al arrancar y adapta pistas/contenido | ✅ |
| Tres rutas con 13 lecciones y ejercicios evaluables | ✅ |
| Estructura problema → guía → ejercicio → feedback | ✅ |
| Biblioteca local con búsqueda y 15 recursos reales | ✅ |
| Progreso persistente y visible, con reinicio por nivel | ✅ |
| Editor con validación sin ejecutar código | ✅ |
| Retroalimentación específica por check | ✅ |
| Un único `.exe` sin dependencias para el usuario final | ⏳ preparado, sin generar |
| Documentación por fase en `docs/` | ✅ |

## 9. Limitaciones conocidas

- **No se ejecuta el código**: no se detectan errores lógicos que casualmente
  cumplan los checks. Es una decisión de seguridad y de instalación.
- **La evaluación de respuestas cortas** mide longitud y palabras clave, no la
  calidad de la argumentación. El feedback lo asume y no penaliza el estilo.
- **La biblioteca no guarda copias**: sin internet no se pueden leer los recursos,
  aunque sí buscarlos.
- **Sin pruebas de interfaz con capturas**: el smoke test detecta errores de
  ejecución, no regresiones visuales.
- **Sin firma digital**: puede aparecer SmartScreen o un falso positivo.

## 10. Qué queda pendiente

- Ejecutar el checklist de la sección 7 de `docs/05-empaquetado.md` sobre el `.exe`
  real, en una máquina sin Python.
- Añadir pruebas de interfaz con capturas si el proyecto crece (requiere una
  dependencia externa).
- Automatizar la revisión periódica de URLs en cada entrega.
- Valorar pruebas de rendimiento con listas grandes en los ejercicios (hoy el
  contenido es pequeño y no es un riesgo).
