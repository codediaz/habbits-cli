# Constitución — habits-cli

1. **Stack mínimo.** Python 3.12+ y solo la biblioteca estándar; pytest es la única dependencia, y solo para tests.
2. **Spec antes que código.** Todo cambio de comportamiento empieza en una spec de `specs/`; el código implementa la spec, nunca al revés.
3. **Núcleo puro.** `habits/core.py` no hace E/S (ni `print`, ni `input`, ni archivos, ni reloj del sistema): recibe datos y devuelve datos.
4. **CLI delgada.** `habits/cli.py` solo lee los argumentos, llama al núcleo y a la persistencia, y formatea la salida; aquí no va lógica de negocio.
5. **Tests obligatorios.** Cada regla de una spec tiene al menos un test en `tests/`; `pytest -q` pasa antes de cerrar cualquier tarea.
6. **Persistencia simple.** Los datos viven en un único JSON local gestionado solo por `habits/storage.py`; su formato solo cambia si antes cambia la spec.
7. **Idioma.** Los identificadores y comentarios de código van en inglés; los mensajes al usuario, en español.

Las specs describen el qué y el porqué; las rutas y la arquitectura solo aparecen en esta constitución y en los planes.

> Cómo comprobarlo: revisar los imports (1, 3), buscar la spec vinculada (2), ejecutar pytest (5).
