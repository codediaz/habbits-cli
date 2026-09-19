# Tareas — Spec 001 MVP

Referencias: `spec.md` y `plan.md` de esta carpeta. Cada tarea dura como máximo 20–30 minutos y sigue el orden de dependencia. En las tareas de código, primero se escribe el test y después la implementación (principio 5).

## Fase 0 — Preparación

- [x] **T01 · Esqueleto del paquete** — RF: —
  Crear `habits/__init__.py`, `habits/__main__.py` (que llama a `cli.main()`), `core.py`, `storage.py` y `cli.py` vacíos, `tests/` y `pyproject.toml` con `requires-python >= 3.12` y la configuración de pytest.
  Hecho cuando: `python -m habits` se ejecuta sin traceback y `pytest -q` termina con "no tests ran".

- [x] **T02 · Test de imports (RNF-2)** — RF: RNF-2
  `tests/test_nfr.py`: analiza con `ast` los imports de `habits/` y solo permite la biblioteca estándar, sin módulos de red (`socket`, `http`, `urllib`…). Comprueba también que `core.py` no importa `json`, `os`, `pathlib`, `sys`, `datetime.datetime.now`, `input` ni `print`.
  Hecho cuando: el test pasa con el esqueleto y falla si se añade `import requests` a cualquier módulo.

## Fase 1 — Núcleo (`core.py`, sin E/S)

- [x] **T03 · Excepciones de dominio** — RF: RF-10
  `HabitError` como base, con las subclases `InvalidNameError`, `DuplicateHabitError`, `HabitNotFoundError` e `InvalidDateError`. Cada una lleva el texto de su mensaje E-x.
  Hecho cuando: un test comprueba que `str()` de cada excepción coincide con la tabla de mensajes de la spec.

- [x] **T04 · Normalizar nombres** — RF: RF-0
  `normalize_name(raw) -> str`: normaliza a NFC, sustituye cada secuencia de caracteres `Zs` por un espacio y recorta los extremos.
  Hecho cuando: pasan los tests de NBSP, espacios internos repetidos, espacios en los extremos y NFD→NFC, y un tabulador interno se conserva.

- [x] **T05 · Validar nombres** — RF: RF-0
  `validate_name(raw) -> str`: normaliza y rechaza con E-0 un nombre vacío, de más de 50 code points o con caracteres no imprimibles.
  Hecho cuando: pasan los tests de vacío, solo espacios, 50 (válido), 51 (rechazado), tabulador interno, nombre numérico y nombre que empieza por "-" (válido).

- [x] **T06 · Clave de comparación y búsqueda** — RF: RF-0, RF-2
  `name_key(name) -> str` (`casefold`) y `find_habit(data, name) -> dict` (lanza E-3 si no existe).
  Hecho cuando: pasan los tests de "Leer"/"LEER" (iguales), "ß"/"ss" (iguales), "Inglés"/"ingles" (distintos), NFC/NFD (iguales) y hábito inexistente → `HabitNotFoundError`.

- [x] **T07 · Crear hábito** — RF: RF-1
  `add_habit(data, raw_name) -> str`: valida, rechaza un duplicado con E-2 y añade `{"name", "done": []}`.
  Hecho cuando: pasan los tests de alta correcta, duplicado con otras mayúsculas y nombre inválido, y los datos de entrada no cambian cuando hay error.

- [x] **T08 · Validar fechas** — RF: RF-4
  `parse_date(text, today) -> date`: acepta solo `AAAA-MM-DD` con ceros a la izquierda, entre 2000-01-01 y `today`; en otro caso lanza E-4.
  Hecho cuando: pasan los tests de hoy, 2000-01-01, 1999-12-31, mañana, `2026-02-30`, `2026-13-01`, `2026-9-1` y `19/09/2026`.

- [x] **T09 · Marcar un día** — RF: RF-3, RF-4
  `mark_done(data, name, day) -> bool` (devuelve False si ya estaba marcado). Mantiene `done` ordenado y sin repeticiones.
  Hecho cuando: pasan los tests de marcar hoy, marcar dos veces (devuelve False y no cambia nada), marcar un día pasado y marcar de forma desordenada (queda ordenado).

- [x] **T10 · Desmarcar un día** — RF: RF-5
  `unmark_done(data, name, day) -> bool` (devuelve False si no estaba marcado).
  Hecho cuando: pasan los tests de desmarcar un día marcado, uno no marcado y un hábito inexistente.

- [x] **T11 · Calcular la racha** — RF: RF-6
  `current_streak(done_dates, today) -> int` según el pseudocódigo del plan.
  Hecho cuando: pasan los tests de racha 0, solo hoy, hoy sin marcar y ayer marcado, hueco de un día, historial desordenado, 28-feb→1-mar, 31-dic→1-ene, 29 de febrero, desmarcar en mitad de una racha, desmarcar hoy con ayer marcado, fechas futuras ignoradas y una racha de 3 años.

- [x] **T12 · Filas del listado** — RF: RF-6
  `list_rows(data, today) -> list[tuple[str, bool, int]]` con el nombre, si está hecho hoy y la racha, en orden por `(casefold, nombre)`.
  Hecho cuando: pasan los tests de lista vacía, orden alfabético sin mayúsculas, desempate entre "Leer" y "leer" (si llegan a coexistir en los datos) y el indicador de hecho hoy.

- [x] **T13 · Renombrar hábito** — RF: RF-7
  `rename_habit(data, old, new) -> tuple[str, str]`: valida, rechaza con E-2 si el nombre es de otro hábito, permite el propio con otras mayúsculas y conserva `done`.
  Hecho cuando: pasan los tests de renombrado correcto con el historial intacto, "leer"→"Leer" (aceptado), nombre de otro hábito, nombre vacío, 51 caracteres y hábito inexistente.

- [x] **T14 · Borrar hábito** — RF: RF-8
  `remove_habit(data, name) -> str`: elimina el hábito y su historial.
  Hecho cuando: pasan los tests de borrado correcto (el hábito ya no aparece en `list_rows`) y hábito inexistente → E-3.

## Fase 2 — Persistencia (`storage.py`)

- [x] **T15 · Cargar datos válidos** — RF: RF-9
  `load(path) -> dict`: un archivo inexistente devuelve `{"version": 1, "habits": []}`; se lee con `utf-8-sig`.
  Hecho cuando: pasan los tests de archivo inexistente, archivo válido y archivo con BOM.

- [x] **T16 · Detectar datos corruptos** — RF: RF-9
  Validar el esquema al cargar y lanzar `StorageError` (E-5) si no se cumple.
  Hecho cuando: pasan los tests de archivo vacío, JSON inválido, Latin-1, raíz que no es un objeto, `version` ausente o desconocida, `name` vacío, fecha inválida, fecha repetida y nombres equivalentes repetidos, y en todos el archivo sigue igual byte a byte.

- [x] **T17 · Guardado atómico** — RF: RF-9
  `save(path, data)`: escribe en un archivo temporal del mismo directorio y usa `os.replace`; crea el directorio si falta; ordena `done`; escribe UTF-8 con `ensure_ascii=False`.
  Hecho cuando: pasan los tests de ida y vuelta, directorio inexistente creado y fallo simulado de `os.replace` con el original intacto.

- [x] **T18 · Error de escritura** — RF: RF-9, RF-10
  Convertir `OSError` al guardar en `StorageWriteError` (E-6).
  Hecho cuando: un test con un directorio sin permisos de escritura lanza `StorageWriteError` y el archivo anterior no cambia.

## Fase 3 — CLI (`cli.py`)

- [ ] **T19 · Parser y errores de uso** — RF: RF-10
  `argparse` con los subcomandos `add`, `done`, `undo`, `list`, `rename` y `delete` (con `--date` en `done` y `undo`), los textos en español, E-1 y salida 2. `main(argv=None) -> int`.
  Hecho cuando: pasan los tests de comando desconocido → 2 con "Error: uso incorrecto", argumento que falta → 2 y argumento que sobra → 2.

- [ ] **T20 · Ruta de datos, "hoy" y errores de dominio** — RF: RF-3, RF-9, RF-10
  Resolver la ruta con `HABITS_FILE` o `~/.habits.json`; calcular `today` una sola vez y hacerlo sustituible en los tests; capturar `HabitError` y `StorageError` → stderr y salida 1.
  Hecho cuando: un test con `HABITS_FILE` en `tmp_path` y un archivo corrupto devuelve 1, muestra E-5 por stderr y no modifica el archivo.

- [ ] **T21 · Comandos `add` y `list`** — RF: RF-1, RF-6
  Hecho cuando: `add Leer` muestra M-1 y sale con 0; repetirlo muestra E-2 y sale con 1; `list` muestra M-7 si no hay hábitos y las líneas M-6 con `1 día` o `N días` y `[x]`/`[ ]`.

- [ ] **T22 · Comandos `done` y `undo`** — RF: RF-3, RF-4, RF-5
  Hecho cuando: pasan los tests de M-2, M-3 (salida 0), M-4, M-5 (salida 0), `--date` válida, `--date` inválida → E-4 y salida 1, y hábito inexistente → E-3 y salida 1.

- [ ] **T23 · Comando `rename`** — RF: RF-7
  Hecho cuando: pasan los tests de M-8 y salida 0, E-2 y salida 1, y la conservación del historial comprobada con `list`.

- [ ] **T24 · Comando `delete` con confirmación** — RF: RF-8
  Hecho cuando: con `input` simulado, "s", "S" y " s " borran (M-10, 0); "n", "si", "sí" y vacío cancelan (M-11, 0); EOF cancela (M-11, 0); Ctrl+C cancela y sale con 130; en ningún caso de cancelación cambia el archivo.

- [ ] **T25 · Nombres que empiezan por "-"** — RF: RF-0, RF-10
  Hecho cuando: `add -- -leer` crea «-leer» (M-1), y `add -leer` sin `--` sale con 2.

## Fase 4 — Cierre

- [ ] **T26 · Test de rendimiento (RNF-5)** — RF: RNF-5
  Hecho cuando: un test que genera 200 hábitos × 5 años de historial en `tmp_path` ejecuta `main(["list"])` en menos de 1 s.

- [ ] **T27 · Trazabilidad RF→test** — RF: todos
  Revisar que cada criterio EARS y cada caso límite de la sección 7 de la spec tiene al menos un test `test_rf<N>_…`.
  Hecho cuando: `pytest -q --collect-only` lista al menos un test para cada RF-0…RF-10, y cada caso límite está enlazado a un test en un comentario de esta tarea.

- [ ] **T28 · Prueba manual de extremo a extremo** — RF: todos
  Con `HABITS_FILE=/tmp/h.json`, ejecutar `add`, `done`, `done --date`, `list`, `undo`, `rename` y `delete`.
  Hecho cuando: las salidas coinciden con la tabla de mensajes y `pytest -q` pasa entero.
