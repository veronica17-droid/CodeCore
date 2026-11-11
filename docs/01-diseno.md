# Fase 1 — Diseño de la experiencia y modelo de datos

**Estado:** completada
**Fecha:** 2026-11-11

## 1. Objetivo

Definir **qué aprende** el usuario, **cómo se le evalúa** y **cómo se guardan** los
datos, antes de escribir una sola línea de GUI. El contenido vive en JSON; el código
solo lo interpreta.

## 2. Principios de diseño pedagógico

1. **Primero el problema, después la herramienta.** Cada lección abre con una
   situación concreta y una pregunta; la sintaxis aparece como consecuencia.
2. **Razonamiento visible.** La guía no da la respuesta: da pasos, preguntas
   socráticas y errores comunes para que el usuario se equivoque con criterio.
3. **Un ejercicio por lección, con criterio de éxito explícito.** El usuario sabe
   cuándo terminó y por qué.
4. **La retroalimentación explica, no sentencia.** Cada comprobación fallida tiene
   un mensaje que describe el malentendido, no solo «incorrecto».
5. **El nivel cambia el andamiaje, no solo el texto.** Más pistas y código de
   partida en principiante; más autonomía y justificación en avanzado.

## 3. Entidades

### 3.1 Level

```json
{
  "id": "beginner",
  "name": "Principiante",
  "order": 1,
  "tagline": "Nunca has programado...",
  "description": "Vas a aprender a pensar como una máquina...",
  "outcomes": ["Descomponer un problema...", "..."],
  "estimated_minutes": 75,
  "lesson_ids": ["beg_01_orden", "..."]
}
```

- `id` es estable y se guarda en el progreso. **No se renombra nunca.**
- `order` define el orden de presentación, no el orden del array.
- `lesson_ids` es la ruta recomendada; la app no deduce lecciones por prefijo.

### 3.2 Lesson

```json
{
  "id": "beg_02_variables",
  "level_id": "beginner",
  "order": 2,
  "title": "Variables: dar nombre al estado",
  "concept": "Variables y asignación",
  "minutes": 15,
  "problem": {
    "scenario": "Tienes dos vasos...",
    "question": "¿Cómo intercambias...?",
    "constraints": ["..."],
    "reflection": "El problema no es la sintaxis..."
  },
  "guide": {
    "mental_model": "Una variable es una caja etiquetada...",
    "steps": [{"title": "1. Sigue el estado", "body": "..."}],
    "questions": ["¿Qué valor se pierde?"],
    "common_mistakes": ["..."]
  },
  "exercise": { "...": "ver 3.3" },
  "success_criteria": ["..."],
  "resource_ids": ["res_python_tutorial", "res_think_python"]
}
```

La estructura **problema → guía → ejercicio → criterio** es obligatoria en todas
las lecciones. La GUI puede colapsar secciones, pero no eliminarlas.

### 3.3 Exercise

Tres tipos, para evaluar razonamiento de formas distintas:

| Tipo | Uso | Evaluación |
|------|-----|------------|
| `code` | Aplicar un concepto en Python | Sintaxis con `ast.parse` + checks declarativos |
| `choice` | Elegir y descartar hipótesis | Opción correcta + feedback específico por opción |
| `short` | Explicar una decisión | Cobertura de palabras clave + longitud mínima |

```json
{
  "type": "code",
  "prompt": "Completa el programa...",
  "language": "python",
  "starter_code": "a = 3\nb = 8\n...",
  "checks": [
    {"type": "ast", "value": "assign", "min": 4, "message": "..."},
    {"type": "regex", "value": "temp\\s*=\\s*a", "message": "..."},
    {"type": "count", "value": "print(", "min": 2, "max": 2, "message": "..."},
    {"type": "not_contains", "value": "sum(", "message": "..."},
    {"type": "contains", "value": "return", "message": "..."}
  ],
  "hints": ["...", "...", "..."],
  "solution": "a = 3\n..."
}
```

**Tipos de check soportados:**

| Tipo | Campos | Significado |
|------|--------|-------------|
| `contains` | `value` | El código contiene el texto |
| `not_contains` | `value` | El código **no** contiene el texto |
| `count` | `value`, `min`, `max` | Número de apariciones dentro de un rango |
| `regex` | `value`, `flags` (`i` opcional) | Coincidencia con expresión regular |
| `ast` | `value`, `min`, `max` | Nodos del AST: `assign`, `for`, `while`, `if`, `function`, `return`, `try`, `dict`, `list`, `call` |

Todos los checks son **opcionales en peso**: por defecto valen 1. El puntaje es
`checks_superados / checks_totales * 100`, redondeado. Se aprueba con **≥ 70**.
Los checks se ejecutan en orden y los fallos se muestran juntos, para que el usuario
vea el patrón y no arregle de uno en uno a ciegas.

**Sintaxis inválida:** si `ast.parse` falla, el puntaje es 0 y se muestra el error
con línea y columna. No se ejecutan los checks de contenido: primero hay que poder
leer el programa.

**Elección (`choice`):** exactamente una opción `correct: true`. Cada opción lleva
su propio `feedback`, incluida la incorrecta «tentadora». Elegir mal no resta
intentos al progreso, pero sí cuenta para las estadísticas.

**Respuesta corta (`short`):** se normaliza el texto (minúsculas, sin acentos), se
cuentan palabras y se comprueba la presencia de `keywords`. Se aprueba con
`min_words` y al menos `min_keywords` distintas. El feedback lista las ideas que
faltan, sin penalizar el estilo.

### 3.4 Resource

```json
{
  "id": "res_python_tutorial",
  "title": "The Python Tutorial (documentación oficial)",
  "type": "doc",
  "url": "https://docs.python.org/es/3/tutorial/",
  "level": "todos",
  "language": "python",
  "source": "Python Software Foundation",
  "description": "Recorrido oficial del lenguaje...",
  "free": true
}
```

- `type`: `doc`, `libro`, `video`, `curso`, `herramienta`, `referencia`.
- `level`: `principiante`, `intermedio`, `avanzado` o `todos`.
- `language`: `python`, `javascript`, `web`, `general`, `git`.
- La biblioteca completa se cura y verifica en la Fase 4.

### 3.5 Progress

Archivo local `%APPDATA%\CodeCore\progress.json`:

```json
{
  "schema_version": 1,
  "level": "beginner",
  "lessons": {
    "beg_01_orden": {
      "status": "completed",
      "best_score": 100,
      "attempts": 2,
      "completed_at": "2026-11-11T18:42:10",
      "last_answer": "print(\"Cortar el pan\")..."
    }
  },
  "last_lesson_id": "beg_02_variables",
  "created_at": "2026-11-11T18:30:00",
  "updated_at": "2026-11-11T18:42:10",
  "settings": {"show_hints": true}
}
```

- `status`: `not_started` (implícito si no aparece), `in_progress`, `completed`.
- `best_score` conserva el mejor intento; `attempts` cuenta todos.
- `last_answer` permite retomar donde se dejó, incluso tras cerrar la app.
- `schema_version` habilita migraciones futuras.

## 4. Adaptación por nivel

| Dimensión | Principiante | Intermedio | Avanzado |
|-----------|--------------|------------|----------|
| Longitud de lección | 12–18 min | 18–22 min | 18–20 min |
| Andamiaje | Código de partida casi completo | Firmas de funciones | Enunciado y contrato |
| Pistas | 3 visibles de inmediato | 3, reveladas de una en una | 3, solo tras 2 intentos |
| Ejercicio dominante | `code` guiado | `code` + depuración | `choice`, `short`, `code` |
| Exigencia | ≥ 70 y checks básicos | ≥ 70 y casos límite | ≥ 70 y justificación |
| Biblioteca | Filtrada a «principiante» | «intermedio» | «avanzado» |

El cambio de nivel **no borra progreso**: cada lección pertenece a un nivel y se
conservan todos los registros.

## 5. Mapa de contenido

| Nivel | Lección | Concepto | Ejercicio |
|-------|---------|----------|-----------|
| Principiante | `beg_01_orden` | Secuencia de instrucciones | `code` |
| Principiante | `beg_02_variables` | Variables y asignación | `code` |
| Principiante | `beg_03_decisiones` | Condicionales | `code` |
| Principiante | `beg_04_bucles` | `for` y `range` | `code` |
| Principiante | `beg_05_funciones` | Funciones y `return` | `code` |
| Intermedio | `int_01_listas` | Listas y casos límite | `code` |
| Intermedio | `int_02_diccionarios` | Diccionarios y `.get()` | `code` |
| Intermedio | `int_03_descomponer` | Responsabilidad única | `code` |
| Intermedio | `int_04_depurar` | Off-by-one | `code` |
| Avanzado | `adv_01_recursion` | Caso base y recursión | `code` |
| Avanzado | `adv_02_complejidad` | O(n) vs O(n²) | `choice` |
| Avanzado | `adv_03_errores` | `try/except` específico | `code` |
| Avanzado | `adv_04_diseno` | Efectos secundarios | `short` |

**13 lecciones**, 3 niveles. El recorrido de principiante (5 lecciones) es completable
de principio a fin y desbloquea el certificado visual de nivel.

## 6. Invariantes que se validan en tests

- IDs de lección únicos en todo el proyecto.
- `level_id` de cada lección coincide con el nivel que la referencia.
- `lesson_ids` de cada nivel existen y están en orden.
- `resource_ids` referenciados existen en la biblioteca (Fase 4).
- Ejercicios `choice` con exactamente una opción correcta.
- Ejercicios `code` con al menos un check y `solution` no vacía.
- Todo `message` de check es no vacío.

## 7. Cómo se verifica esta fase

```powershell
$py = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
& $py -X utf8 -c "import json; json.load(open('resources/content/levels.json', encoding='utf-8')); print('levels OK')"
& $py -X utf8 -c "import json,glob; [json.load(open(p, encoding='utf-8')) for p in glob.glob('resources/content/lessons_*.json')]; print('lessons OK')"
```

Comprobación de integridad (sin GUI):

```powershell
& $py -X utf8 tools\verify_content.py
```

> `tools/verify_content.py` se completa en la Fase 2; hasta entonces la validación
> se hace con el script inline documentado en `docs/02-nucleo.md`.

## 8. Qué queda pendiente

- Implementar los cargadores y la evaluación (Fase 2).
- Construir las vistas y el editor (Fase 3).
- Crear `resources/library/resources.json` con los 15 IDs ya referenciados y
  verificar todas las URLs (Fase 4).
- Añadir imágenes o diagramas a las lecciones si se decide ampliar el prototipo.
- Traducir el contenido si se quiere una versión bilingüe.
