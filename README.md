# habits-cli

CLI en Python para registrar hábitos de estudio y ver cuántos días
seguidos llevas cumpliéndolos (tu "racha"). Todo se guarda en un archivo
JSON local: no necesitas cuenta ni conexión a internet.

## Requisitos

- Python 3.12 o superior.
- [pytest](https://pytest.org) solo para ejecutar los tests (no hace falta
  para usar la CLI).

## Instalación

No hay que instalar nada del proyecto en sí; solo necesitas Python. Para
ejecutar los tests, se recomienda un entorno virtual:

```bash
python3 -m venv .venv
.venv/bin/pip install pytest
```

## Cómo ejecutarlo

Desde la raíz del proyecto:

```bash
python3 -m habits <comando> [argumentos]
```

## Comandos

| Comando | Qué hace |
|---|---|
| `add NOMBRE` | Crea un hábito nuevo. |
| `done NOMBRE [--date AAAA-MM-DD]` | Marca el hábito como hecho hoy, o en la fecha indicada. |
| `undo NOMBRE [--date AAAA-MM-DD]` | Desmarca el día (hoy por defecto, o el indicado). |
| `list` | Muestra todos los hábitos con su racha actual. |
| `rename NOMBRE NUEVO` | Cambia el nombre de un hábito, sin perder su historial. |
| `delete NOMBRE` | Borra un hábito y todo su historial (pide confirmación). |

Si el nombre de un hábito tiene espacios, va entre comillas. Si empieza
por `-`, se escribe después de `--`, por ejemplo:

```bash
python3 -m habits add -- "-mi hábito"
```

## Ejemplo de uso

```console
$ python3 -m habits add Leer
Hábito «Leer» creado.

$ python3 -m habits done Leer
«Leer» marcado el 2026-09-19.

$ python3 -m habits done Leer --date 2026-09-18
«Leer» marcado el 2026-09-18.

$ python3 -m habits list
[x] Leer — racha: 2 días

$ python3 -m habits rename Leer Lectura
«Leer» renombrado a «Lectura».

$ python3 -m habits delete Lectura
¿Borrar «Lectura» y todo su historial? (s/n): s
Hábito «Lectura» borrado.
```

## Notas de uso

- **Racha:** cuenta los días seguidos marcados que terminan hoy o, si hoy
  aún no lo has marcado, ayer. Un día sin marcar corta la racha.
- **Nombres:** no distinguen mayúsculas ("Leer" y "leer" son el mismo
  hábito) y admiten como máximo 50 caracteres.
- **Fechas:** solo en formato `AAAA-MM-DD`, entre el 2000-01-01 y hoy.
- **Borrar:** siempre pide confirmación; solo "s" o "S" borra de verdad,
  cualquier otra respuesta cancela.
- **Códigos de salida:** `0` en éxito (incluidos los avisos como "ya
  estaba marcado"), `1` en errores de datos (hábito inexistente, fecha
  inválida, nombre duplicado...) y `2` si el comando o sus argumentos
  están mal escritos.

## Dónde se guardan los datos

Por defecto en `~/.habits.json`. Puedes usar otro archivo con la variable
de entorno `HABITS_FILE`:

```bash
HABITS_FILE=/ruta/a/mis-habitos.json python3 -m habits list
```

## Desarrollo

El proyecto sigue un flujo de spec → plan → tareas → código, documentado
en `specs/001-habits-mvp/`. Las reglas del proyecto están en
`docs/constitution.md`.

Ejecutar los tests:

```bash
.venv/bin/pytest -q
```
