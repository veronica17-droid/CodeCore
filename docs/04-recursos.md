# Fase 4 — Biblioteca de recursos

**Estado:** completada
**Fecha:** 2026-11-11

## 1. Qué se hizo

Se creó `resources/library/resources.json` con **15 recursos reales**, exactamente
los que referencian las 13 lecciones. Todos los enlaces apuntan a documentación,
libros, cursos o herramientas oficiales y **respondieron con HTTP 200** en la
verificación del 2026-11-11.

La biblioteca es local: los metadatos viajan dentro de la app y la búsqueda funciona
sin internet. Solo **abrir** un enlace requiere conexión y un navegador.

## 2. Criterios de curación

1. **Fuente primaria o reconocida.** Documentación oficial, universidades, autores
   de referencia o proyectos con mantenimiento visible.
2. **Gratuito y accesible.** Salvo una excepción marcada explícitamente, todo el
   contenido es gratuito y no exige registro para leer.
3. **En español cuando existe.** La documentación oficial de Python se enlaza en
   español; el resto se elige por calidad, no por idioma.
4. **Un recurso debe poder usarse hoy.** Nada de enlaces a cursos retirados,
   listas de espera o páginas de marketing.
5. **Cada recurso aporta algo distinto.** Se evita duplicar el mismo tutorial con
   otro dominio.

## 3. Catálogo

| ID | Título | Tipo | Nivel | Lenguaje | Fuente |
|----|--------|------|-------|----------|--------|
| `res_python_tutorial` | El tutorial de Python (documentación oficial) | `doc` | todos | Python | Python Software Foundation |
| `res_cs50` | CS50x: Introducción a las ciencias de la computación | `curso` | todos | general | Harvard University |
| `res_think_python` | Think Python (3.ª edición) | `libro` | principiante | Python | Allen B. Downey |
| `res_python_control` | Control de flujo en Python | `doc` | principiante | Python | Python Software Foundation |
| `res_automate` | Automate the Boring Stuff with Python | `libro` | principiante | Python | Al Sweigart |
| `res_freecodecamp_python` | freeCodeCamp: Computación científica con Python | `curso` | principiante | Python | freeCodeCamp |
| `res_python_functions` | Definir funciones (documentación oficial) | `doc` | principiante | Python | Python Software Foundation |
| `res_python_lists` | Listas en Python | `doc` | principiante | Python | Python Software Foundation |
| `res_realpython` | Real Python | `referencia` | intermedio | Python | Real Python |
| `res_python_dict` | Diccionarios (documentación oficial) | `doc` | intermedio | Python | Python Software Foundation |
| `res_python_errors` | Errores y excepciones en Python | `doc` | avanzado | Python | Python Software Foundation |
| `res_python_pep8` | PEP 8: guía de estilo para código Python | `referencia` | intermedio | Python | Python Software Foundation |
| `res_bigocheatsheet` | Big-O Cheat Sheet | `referencia` | avanzado | general | Eric Rowell |
| `res_visualgo` | VisuAlgo | `herramienta` | avanzado | general | VisuAlgo |
| `res_opensource_guide` | Open Source Guides | `doc` | intermedio | Git | GitHub |

### 3.1 URL de cada recurso

```
https://docs.python.org/es/3/tutorial/
https://cs50.harvard.edu/x/
https://allendowney.github.io/ThinkPython/
https://docs.python.org/es/3/tutorial/controlflow.html
https://automatetheboringstuff.com/
https://www.freecodecamp.org/learn/scientific-computing-with-python/
https://docs.python.org/es/3/tutorial/controlflow.html#defining-functions
https://docs.python.org/es/3/tutorial/introduction.html#lists
https://realpython.com/
https://docs.python.org/es/3/tutorial/datastructures.html#dictionaries
https://docs.python.org/es/3/tutorial/errors.html
https://peps.python.org/pep-0008/
https://www.bigocheatsheet.com/
https://visualgo.net/en
https://opensource.guide/es/
```

### 3.2 Sobre `free`

Todos los recursos son gratuitos salvo **Real Python**, marcado con `free: false`
porque una parte del catálogo requiere suscripción. La interfaz muestra la
insignia «Gratis» solo cuando `free` es `true`; el recurso sigue siendo visible y
utilizable en su parte abierta.

## 4. Cómo se integra con la app

### 4.1 En las lecciones

Cada lección declara `resource_ids`. La biblioteca resuelve esos ids y la vista de
lección puede ofrecer lecturas de apoyo sin acoplar el contenido a las URLs.

```python
lesson = repo.get_lesson("beg_01_orden")
repo.resources_for_lesson(lesson)   # tuple[Resource, ...] en el orden declarado
```

### 4.2 En la vista Biblioteca

- **Búsqueda local** por título, descripción, fuente, tipo, lenguaje y nivel.
- Normalización con `unicodedata`: mayúsculas y acentos son irrelevantes
  (`depuracion` encuentra `Depuración`).
- Filtros combinables de **tipo**, **lenguaje** y **nivel**. El filtro de nivel
  incluye los recursos marcados como `todos`.
- Orden: primero los títulos que coinciden con la consulta completa, después el
  resto por orden alfabético.
- Cada tarjeta muestra tipo, nivel, lenguaje, fuente, descripción, insignia de
  gratuidad y un botón «Abrir ↗» que usa `webbrowser.open_new_tab`.

### 4.3 Validación estricta

`ContentRepository` valida cada recurso al arrancar:

- `type` en `doc`, `libro`, `video`, `curso`, `herramienta`, `referencia`;
- `level` en `principiante`, `intermedio`, `avanzado`, `todos`;
- `url` empieza por `http://` o `https://`;
- `id` único, textos no vacíos y `free` booleano.

Además, `verify_content.py` comprueba que **todos los `resource_ids` de las
lecciones existen** en la biblioteca. Ya no queda ninguno pendiente.

## 5. Cómo se verifica

### 5.1 Validación de esquema y referencias

```powershell
cd CodeCore
$py = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
& $py -X utf8 tools\verify_content.py
```

Salida esperada:

```
Niveles:    3
Lecciones:  13
Recursos:   15
  - Principiante: 5 lecciones
  - Intermedio: 4 lecciones
  - Avanzado: 4 lecciones
Contenido OK
```

### 5.2 Comprobación de URLs (requiere internet)

```powershell
& $py -X utf8 tools\verify_content.py --check-urls
```

Salida esperada: una línea `[URL 200]` por recurso y `URLs comprobadas: 15`.
El verificador usa un *User-Agent* de navegador y, si un servidor rechaza `HEAD`
con 403/405, reintenta con `GET` antes de marcar la URL como fallida.

### 5.3 Pruebas automatizadas

```powershell
& $py -X utf8 -m unittest discover -s tests
```

Resultado esperado: `Ran 49 tests ... OK`. Las pruebas nuevas comprueban que:

- no falta ningún `resource_id` referenciado;
- hay 15 recursos con ids únicos;
- `resources_for_lesson` respeta el orden declarado;
- todos los recursos tienen nivel válido, fuente y descripción útil;
- la búsqueda devuelve solo recursos que contienen el término.

### 5.4 Comprobación manual en la app

```powershell
.\tools\run_dev.ps1
```

- [ ] Biblioteca muestra «15 recursos» al abrirse sin filtros.
- [ ] Buscar `depuracion` encuentra «Think Python» (búsqueda sin acentos).
- [ ] Buscar `cobol` muestra el estado vacío con «Limpiar filtros».
- [ ] El filtro de nivel «Avanzado» muestra los recursos avanzados y los «todos».
- [ ] «Abrir ↗» lanza el navegador con la URL correcta.
- [ ] Real Python aparece sin la insignia «Gratis».

## 6. Qué queda pendiente

- **Revisión periódica de enlaces.** Las URLs cambian; conviene ejecutar
  `verify_content.py --check-urls` antes de cada entrega.
- **Contenido en caché.** Hoy la app no guarda copias locales de los recursos; si
  se quiere uso 100 % sin internet habría que empaquetar extractos con permiso.
- **Más recursos por nivel.** La biblioteca cubre el contenido actual; al añadir
  lecciones habrá que ampliarla y volver a validar los ids.
- **Valoración de recursos.** No hay votos ni «favoritos»; sería una mejora de
  producto, no un requisito del prototipo.
