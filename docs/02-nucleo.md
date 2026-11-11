# Fase 2 — Núcleo

**Estado:** completada
**Fecha:** 2026-11-11

## 1. Qué se hizo

Se implementó toda la lógica de CodeCore **sin tkinter**, de modo que pueda probarse
sin abrir una ventana. La GUI de la Fase 3 solo consume estas APIs.

| Módulo | Responsabilidad |
|--------|-----------------|
| `src/config.py` | Constantes: versión, umbral de aprobación (70), tamaño de ventana, límites. |
| `src/core/paths.py` | Rutas en desarrollo vs. `sys._MEIPASS`; carpeta de progreso en `%APPDATA%`. |
| `src/core/models.py` | Dataclasses de contenido y progreso; serialización del progreso. |
| `src/core/content.py` | Carga y **validación estricta** de niveles, lecciones y biblioteca. |
| `src/core/feedback.py` | Evaluación de ejercicios `code`, `choice` y `short`. |
| `src/core/progress.py` | Persistencia atómica, recuperación, resumen y reinicio. |
| `src/core/search.py` | Búsqueda local normalizada y filtros combinables. |
| `tools/verify_content.py` | Validador de contenido por línea de comandos. |

## 2. API pública (resumen)

```python
repo = ContentRepository()          # carga resources/content/*.json
repo.levels                         # tuple[Level, ...] ordenada
repo.lessons_for_level("beginner")  # tuple[Lesson, ...] en orden de ruta
repo.get_lesson("beg_02_variables")
repo.next_lesson(lesson_id)
repo.search_resources("python", resource_type="video", level="beginner")

evaluation = evaluate(lesson.exercise, answer, attempt=1, level_id=lesson.level_id)
evaluation.score        # 0..100
evaluation.passed       # score >= 70
evaluation.outcomes     # mensajes por comprobación
evaluation.syntax_error # texto con línea/columna o None
evaluation.next_hint    # pista progresiva según nivel e intento

store = ProgressStore()             # %APPDATA%/CodeCore/progress.json
progress = store.load()
store.set_level(progress, "beginner")
store.record_attempt(progress, lesson_id, 100, True, answer, next_lesson_id)
store.save(progress)
store.summary(progress, repo.levels)
```

## 3. Decisiones clave

### 3.1 El código del usuario no se ejecuta

`feedback.py` usa `ast.parse()` y comprobaciones declarativas. No hay `eval`, `exec`,
`subprocess` ni importación del código del usuario.

- **Seguridad:** el texto puede venir de cualquier persona; nunca se ejecuta.
- **Instalación:** no hace falta un intérprete embebido ni permisos especiales.
- **Antivirus:** un `.exe` que lanza procesos hijos es más sospechoso.
- **Determinismo:** el resultado no depende de la máquina ni del tiempo de ejecución.

La limitación (no detectar errores lógicos que casualmente cumplan los checks) se
compensa con comprobaciones estructurales (`ast`), de orden (`regex`) y de ausencia
(`not_contains`). Está documentada en `docs/00-arquitectura.md` y `docs/06-pruebas.md`.

### 3.2 Puntaje parcial y umbral

- Puntaje = `checks superados / checks totales × 100` (redondeado).
- Se aprueba con **≥ 70**. Con 4 checks, 3 aciertos (75) aprueban; con 3 checks,
  2 aciertos (67) no.
- El mejor puntaje se conserva; los intentos se acumulan.
- Una lección completada **no se desmarca** al fallar un intento posterior.

### 3.3 Pistas adaptadas al nivel

| Nivel | Comportamiento |
|-------|----------------|
| Principiante | La primera pista está disponible desde el primer intento. |
| Intermedio | Igual, pero la GUI las revela de una en una. |
| Avanzado | La primera pista aparece tras el segundo intento fallido. |

La solución completa se ofrece a partir del **tercer intento**, nunca antes.

### 3.4 Persistencia robusta

- Escritura en `progress.json.tmp` + `os.replace()` → nunca queda un JSON a medias.
- JSON corrupto o `schema_version` futuro → se renombra a
  `progress.corrupt-AAAAMMDD-HHMMSS.json` y se empieza limpio, sin borrar evidencia.
- `last_answer` permite retomar el ejercicio tal como se dejó.
- No se guardan nombres, correos ni datos personales.

### 3.5 Validación de contenido

`ContentRepository` falla con `ContentError` y un mensaje accionable si:

- falta un campo obligatorio o un texto está vacío;
- un id de lección o recurso está duplicado;
- un nivel referencia una lección inexistente o de otro nivel;
- un ejercicio `choice` no tiene exactamente una opción correcta;
- un ejercicio `code` no tiene checks;
- una respuesta corta no define `min_words`/`min_keywords` cohecentes;
- una URL no empieza por `http(s)://`;
- el `schema_version` no coincide.

Esto convierte un error de contenido en un mensaje claro al arrancar, en lugar de
una pantalla rota.

## 4. Cómo se verifica

```powershell
cd CodeCore
$py = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"

# 1. Pruebas del núcleo (sin GUI)
& $py -X utf8 -m unittest discover -s tests -v

# 2. Validación del contenido
& $py -X utf8 tools\verify_content.py

# 3. Comprobación rápida de sintaxis de todos los módulos
& $py -m compileall -q src tools tests
```

Resultado esperado al terminar la fase:

```
Ran 45 tests in 0.07s
OK
Niveles:    3
Lecciones:  13
Recursos:   0
  - Principiante: 5 lecciones
  - Intermedio: 4 lecciones
  - Avanzado: 4 lecciones
AVISO: la biblioteca todavía no está creada (Fase 4)...
Contenido OK
```

Cobertura funcional de las pruebas:

| Archivo | Qué comprueba |
|---------|---------------|
| `test_content.py` | Carga, orden, navegación, ids únicos, JSON inválido, duplicados. |
| `test_feedback.py` | Aciertos, fallos, sintaxis, `count`, `regex`, `ast`, elección, respuesta corta, pistas. |
| `test_progress.py` | Estado inicial, intentos, mejor puntaje, round-trip, corrupción, resumen, reinicio. |
| `test_search.py` | Acentos, mayúsculas, filtros por tipo/lenguaje/nivel, orden y combinación. |

## 5. Qué queda pendiente

- Construir la GUI y el editor (Fase 3).
- Crear la biblioteca real; hasta entonces `verify_content.py` avisa pero no falla
  por los 15 ids referenciados (Fase 4).
- Empaquetar y probar el `.exe` (Fase 5, solo con autorización).
- Añadir pruebas de integración de la GUI (opcional; requiere pantalla).
- Valorar un modo portable que guarde el progreso junto al `.exe`.
