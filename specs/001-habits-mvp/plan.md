# Plan técnico — Spec 001 MVP

Referencias: `docs/constitution.md` y `specs/001-habits-mvp/spec.md`.

## 1. Estructura de módulos

```
habits/
  __init__.py
  __main__.py   # entrada: python -m habits → cli.main()
  core.py       # dominio puro: validación, operaciones, racha (sin E/S)
  storage.py    # lectura y escritura del JSON (única E/S de datos)
  cli.py        # argparse, input() para confirmar, print, códigos de salida
tests/
  test_core.py
  test_storage.py
  test_cli.py
  test_nfr.py
```

| Módulo | Responsabilidad | RF |
|---|---|---|
| `core.py` | Normalizar y validar nombres, validar fechas, marcar, desmarcar, renombrar, borrar, calcular la racha y ordenar el listado. Recibe `today` como parámetro, nunca consulta el reloj (constitución, principio 3). Lanza excepciones de dominio (`HabitError` y sus subclases) con el mensaje en español. | RF-0…RF-8 |
| `storage.py` | `load(path) -> dict` y `save(path, data)`. El archivo inexistente equivale a datos vacíos. Lee con `utf-8-sig` (acepta BOM). Si el archivo está corrupto lanza `StorageError` y nunca escribe. El guardado es atómico (temporal + `os.replace`), crea el directorio si falta y convierte `OSError` en `StorageWriteError` (E-6). | RF-9 |
| `cli.py` | Analizar los argumentos, obtener `date.today()`, pedir confirmación al borrar, traducir excepciones a mensajes y códigos de salida. Calcula `today` una sola vez al empezar. Captura `KeyboardInterrupt` al confirmar y termina con 130. No contiene lógica de negocio. | RF-3, RF-6, RF-8, RF-10 |

Flujo de cada comando: `cli` → `storage.load` → función de `core` → `storage.save` (si hubo cambios) → `print`.

## 2. Modelo de datos JSON (RF-9)

Ruta: la variable de entorno `HABITS_FILE` o, si no existe, `~/.habits.json`.

```json
{
  "version": 1,
  "habits": [
    {
      "name": "Leer",
      "done": ["2026-09-17", "2026-09-18", "2026-09-19"]
    },
    {
      "name": "Inglés",
      "done": []
    }
  ]
}
```

- `name`: el nombre normalizado según RF-0 (NFC, sin espacios en los extremos y con los internos reducidos a uno). La clave de comparación es `name.casefold()` y se calcula al vuelo, no se guarda (RF-0, RF-2). Esquema definido en la sección 5 de la spec.
- `done`: fechas en ISO `AAAA-MM-DD`, sin repeticiones y ordenadas de forma ascendente al guardar (RF-3, RF-4, RF-5).
- `version`: permite cambiar el formato en el futuro. Si falta o no se reconoce, se trata como archivo corrupto (RF-9).
- Validación al cargar: el raíz es un objeto, `habits` es una lista, cada `name` es un texto no vacío, cada fecha es ISO válida, no hay fechas repetidas en un mismo hábito y no hay nombres equivalentes repetidos (RF-9). Si algo falla → `StorageError`.

## 3. Algoritmo de racha (RF-6)

```
función racha(fechas_hechas: conjunto de fechas, hoy: fecha) -> entero
    si hoy ∈ fechas_hechas:
        día ← hoy
    si no, si hoy − 1 ∈ fechas_hechas:
        día ← hoy − 1
    si no:
        devolver 0
    n ← 0
    mientras día ∈ fechas_hechas:
        n ← n + 1
        día ← día − 1
    devolver n
```

- Coste O(racha) con un conjunto; no depende del orden de las fechas en el historial.
- Las fechas futuras que haya en el JSON (por un cambio de reloj) se ignoran de forma natural porque se empieza en hoy o en ayer, y se conservan al guardar (RF-6).
- Los cambios de mes o de año y los años bisiestos los resuelve `date - timedelta(days=1)`.

## 4. Contrato de la CLI

Uso: `python -m habits <comando> [argumentos]`. Los nombres con espacios van entre comillas; los que empiezan por "-" van después de `--` (RF-10). Los textos exactos son los de la tabla de mensajes de la spec (M-x y E-x).

| Comando | Efecto | Salida (stdout) | RF |
|---|---|---|---|
| `add NOMBRE` | Crea el hábito | `Hábito «Leer» creado.` | RF-1 |
| `done NOMBRE [--date AAAA-MM-DD]` | Marca hoy o la fecha indicada | `«Leer» marcado el 2026-09-19.` / si ya lo estaba: `«Leer» ya estaba marcado el 2026-09-19.` | RF-3, RF-4 |
| `undo NOMBRE [--date AAAA-MM-DD]` | Desmarca hoy o la fecha indicada | `«Leer» desmarcado el 2026-09-19.` / si no lo estaba: `«Leer» no estaba marcado el 2026-09-19.` | RF-5 |
| `list` | Lista los hábitos | Una línea por hábito, en orden por `(casefold, nombre)`: `[x] Leer — racha: 3 días` o `[ ] Inglés — racha: 0 días`. Sin hábitos: `No hay hábitos todavía.` | RF-6 |
| `rename NOMBRE NUEVO` | Renombra el hábito y conserva su historial | `«Leer» renombrado a «Lectura».` | RF-7 |
| `delete NOMBRE` | Pregunta `¿Borrar «Leer» y todo su historial? (s/n): `; solo borra con `s` o `S` tras `strip()`; EOF → cancela (0); Ctrl+C → cancela (130) | `Hábito «Leer» borrado.` / `Borrado cancelado.` | RF-8 |

Singular: `racha: 1 día`.

**Errores:** se escriben en stderr con el prefijo `Error: ` (RF-10).

| Código | Cuándo |
|---|---|
| 0 | Éxito, incluidos los avisos informativos (M-3, M-5, M-11) |
| 1 | Error de dominio o de datos: E-0, E-2 a E-6 |
| 130 | Ctrl+C durante la confirmación de borrado |
| 2 | Error de uso (E-1): comando desconocido o argumentos que faltan o sobran (argparse, con su texto de ayuda traducido al español) |

Ejemplos de mensajes: `Error: el hábito «Correr» no existe.`, `Error: ya existe un hábito llamado «leer».`, `Error: la fecha «2026-02-30» no es válida (usa AAAA-MM-DD, entre 2000-01-01 y hoy).` (ver la tabla de la spec).

Si al borrar llega un fin de entrada (EOF), se trata como `n` y el borrado se cancela.

## 5. Decisiones técnicas

| Decisión | Por qué | Alternativa descartada |
|---|---|---|
| `argparse` con subcomandos | Está en la biblioteca estándar, genera la ayuda y hace la validación básica | `click`/`typer`: añaden una dependencia (constitución, principio 1) |
| `today` inyectado en `core` | Hace el núcleo puro y testeable sin tocar el reloj (principio 3, RNF-3) | Llamar a `date.today()` dentro de `core`: exigiría mocks |
| Nombre original + clave `casefold()` calculada | Se muestra lo que escribió el usuario y se compara sin mayúsculas, incluidos los acentos | Guardar el nombre en minúsculas: se pierde la forma original |
| JSON con `version` y una lista de hábitos | Legible, fácil de migrar, y el orden no importa porque se ordena al listar | Un diccionario indexado por nombre: renombrar obliga a cambiar la clave y duplica la normalización |
| Guardado atómico (archivo temporal + `os.replace`) | Si el proceso se interrumpe, no queda el JSON a medias (RF-9) | Escribir directamente: riesgo de corromper los datos |
| Corrupto → error sin sobrescribir | Así lo decidió el usuario; no se pierden datos | Reiniciar o hacer una copia automática |
| Excepciones de dominio con el mensaje en español; la CLI las traduce a código 1 | Un único punto de salida para los errores (RF-10) | Devolver códigos desde `core`: mezcla interfaz y lógica |
| Normalizar: `unicodedata.normalize('NFC')`, sustituir cada secuencia de caracteres de categoría Unicode `Zs` por un espacio y recortar los extremos; después validar con `isprintable()` y `len ≤ 50` (RF-0) | Colapsa los espacios Unicode (NBSP incluido) sin ocultar un tabulador interno, que `isprintable()` rechaza. `split()` no sirve, porque convertiría el tabulador en un espacio | Una expresión regular alfanumérica: más restrictiva de lo que se decidió |
| Ruta configurable con `HABITS_FILE` | Los tests usan `tmp_path` sin tocar el home | Una ruta fija: no se puede probar de forma aislada |

## 6. Estrategia de tests

Solo pytest (principio 5). Cada criterio EARS tiene al menos un test, nombrado `test_rf<N>_<caso>`.

- **`test_core.py`** (unitarios, sin E/S; `today` fijo, por ejemplo `date(2026, 9, 19)`):
  - RF-0/RF-1/RF-2: espacios Unicode y espacios internos repetidos, tabulador interno, 50 frente a 51 code points, NFC frente a NFD, ß/ss, acentos distintos, duplicado con mayúsculas distintas, nombre numérico, hábito inexistente.
  - RF-3/RF-4: marcar hoy, marcar dos veces (sin cambios, con aviso), fecha pasada, hoy explícito, mañana, `1999-12-31`, `2026-02-30`, `2026-13-01`, `2026-9-1`, `19/09/2026`.
  - RF-5: desmarcar un día marcado, uno sin marcar y una fecha inválida.
  - RF-6: racha 0, hoy sin marcar y ayer marcado, hueco de un día, historial desordenado, cruce de 28-feb a 1-mar y de 31-dic a 1-ene, 29 de febrero, desmarcar en mitad de una racha, desmarcar hoy con ayer marcado, fechas futuras en los datos, racha de varios años, orden con desempate.
  - RF-7: renombrar conservando el historial, al mismo nombre con otras mayúsculas (se permite), a un nombre de otro hábito, vacío o de 51 caracteres.
  - RF-8: borrar elimina el hábito y su historial.
- **`test_storage.py`** (con `tmp_path`): RF-9, con archivo inexistente → vacío, directorio inexistente creado al guardar, ida y vuelta, BOM aceptado, archivo vacío, JSON inválido, Latin-1, esquema inválido, `version` desconocida, fechas repetidas y nombres equivalentes → `StorageError`, y el archivo sigue intacto byte a byte. Directorio sin permisos de escritura → `StorageWriteError` y datos anteriores intactos. Fallo simulado de `os.replace` → el original sigue intacto.
- **`test_cli.py`** (integración: `main(argv)` con `HABITS_FILE` apuntando a `tmp_path`, `capsys` para las salidas, `monkeypatch` para `input` y para la fecha de hoy): los mensajes y códigos de salida de cada comando, la confirmación del borrado (`s`, `S`, ` s `, `si`, `sí`, vacío, EOF y Ctrl+C → 130), un nombre con `-` después de `--`, un archivo corrupto con salida 1 y sin sobrescribir, y un comando desconocido con salida 2 (RF-3, RF-6, RF-8, RF-10).
- **`test_nfr.py`**: RNF-2 (analiza con `ast` los imports de `habits/` y solo permite la biblioteca estándar, sin módulos de red) y RNF-5 (200 hábitos × 5 años, `list` en menos de 1 s).
- Criterio de terminado: `pytest -q` en verde y la tabla RF→test completa.

## 7. Cobertura de RF

| RF | Secciones del plan |
|---|---|
| RF-0 Nombre válido | 1, 2, 5, 6 |
| RF-1 Crear | 1, 4, 5, 6 |
| RF-2 Identificación | 1, 2, 5, 6 |
| RF-3 Marcar hoy | 1, 2, 4, 6 |
| RF-4 Fecha pasada | 1, 2, 4, 6 |
| RF-5 Desmarcar | 1, 2, 4, 6 |
| RF-6 Listar y racha | 1, 3, 4, 6 |
| RF-7 Renombrar | 1, 4, 6 |
| RF-8 Borrar | 1, 4, 6 |
| RF-9 Persistencia | 1, 2, 5, 6 |
| RF-10 Errores | 1, 4, 5, 6 |
