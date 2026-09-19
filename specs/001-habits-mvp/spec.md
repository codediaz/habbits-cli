# Spec 001 — MVP de habits-cli

## 1. Contexto y objetivo
Quien estudia de forma autodidacta necesita constancia, y ver una racha de días seguidos motiva a no romperla. El objetivo es una herramienta de línea de comandos que permita registrar hábitos de estudio diarios, marcar los días cumplidos y consultar la racha actual de cada hábito, de forma local y sin cuentas.

## 2. Usuarios
- **Estudiante:** una sola persona que usa la herramienta en su propio equipo desde la terminal.
- **Desarrollador junior:** mantiene el proyecto, así que la spec debe ser clara y comprobable.

## 3. Historias de usuario
- HU-1: Como estudiante, quiero crear un hábito con un nombre para empezar a seguirlo.
- HU-2: Como estudiante, quiero marcar un hábito como hecho hoy para registrar mi progreso.
- HU-3: Como estudiante, quiero marcar o desmarcar cualquier día (hoy o pasado) para corregir olvidos o errores.
- HU-4: Como estudiante, quiero listar mis hábitos con su racha actual para ver cómo voy.
- HU-5: Como estudiante, quiero renombrar o borrar un hábito para mantener la lista al día.

## 4. Requisitos funcionales

**RF-0 Nombre válido** (lo usan RF-1, RF-2 y RF-7)
- El sistema deberá normalizar todo nombre recibido así: normalización Unicode NFC, eliminación de los espacios Unicode del inicio y del final, y reducción de cualquier secuencia de espacios internos a un solo espacio.
- El sistema deberá considerar válido un nombre normalizado que no esté vacío, tenga como máximo 50 code points y solo contenga caracteres imprimibles (un tabulador o un salto de línea no lo son).
- Si el nombre normalizado no es válido, entonces el sistema deberá rechazarlo con un mensaje de error que indique el motivo.
- El sistema deberá comparar nombres sin distinguir mayúsculas mediante el plegado de mayúsculas de Unicode ("ß" equivale a "ss") y distinguiendo acentos ("Inglés" y "ingles" son distintos).

**RF-1 Crear hábito**
- Cuando el usuario cree un hábito con un nombre válido (RF-0), el sistema deberá guardarlo normalizado, con el historial vacío, y mostrar el mensaje M-1.
- Si ya existe un hábito con un nombre equivalente (RF-0), entonces el sistema deberá rechazarlo con el error E-2.

**RF-2 Identificación de hábitos**
- El sistema deberá identificar cada hábito por su nombre normalizado y comparado según RF-0.
- Si una orden hace referencia a un hábito que no existe, entonces el sistema deberá mostrar el error E-3.

**RF-3 Día actual y marcar hoy**
- El sistema deberá tomar como día actual la fecha local del equipo, obtenida una sola vez al empezar cada ejecución; a partir de medianoche es el día siguiente.
- Cuando el usuario marque un hábito sin indicar fecha, el sistema deberá registrar el día actual y mostrar el mensaje M-2.
- Si ese día ya estaba marcado, entonces el sistema deberá mostrar el aviso M-3 sin cambiar nada.

**RF-4 Fechas indicadas por el usuario** (las usan marcar y desmarcar)
- El sistema deberá aceptar las fechas solo en el formato AAAA-MM-DD, con ceros a la izquierda (se rechaza "2026-9-1").
- El sistema deberá aceptar fechas entre 2000-01-01 y el día actual, ambos incluidos.
- Si la fecha no tiene el formato, no existe (como "2026-02-30" o "2026-13-01") o está fuera de ese rango, entonces el sistema deberá rechazarla con el error E-4.
- Cuando el usuario marque un hábito con una fecha válida, el sistema deberá registrar ese día y mostrar el mensaje M-2, o el aviso M-3 si ya estaba marcado.

**RF-5 Desmarcar un día**
- Cuando el usuario desmarque un día de un hábito (el día actual por defecto, o una fecha válida según RF-4), el sistema deberá eliminar ese registro y mostrar el mensaje M-4.
- Si ese día no estaba marcado, entonces el sistema deberá mostrar el aviso M-5 sin cambiar nada.

**RF-6 Listar hábitos con racha**
- Cuando el usuario pida la lista, el sistema deberá mostrar una línea por hábito con el formato M-6.
- El sistema deberá ordenar los hábitos por su nombre plegado según RF-0 y, en caso de empate, por el nombre original. No se aplica ningún orden que dependa del idioma del sistema.
- Mientras no haya hábitos, el sistema deberá mostrar el mensaje M-7.
- El sistema deberá calcular la racha como el número de días consecutivos marcados que terminan en el día actual o, si ese día no está marcado, en el día anterior.
- Si no están marcados ni el día actual ni el anterior, entonces el sistema deberá mostrar una racha de 0.
- El sistema deberá ignorar para la racha las fechas posteriores al día actual que haya en los datos guardados, y conservarlas sin modificarlas.

**RF-7 Renombrar hábito**
- Cuando el usuario renombre un hábito existente con un nombre válido (RF-0), el sistema deberá cambiar el nombre, conservar el historial y mostrar el mensaje M-8.
- Si el nuevo nombre es equivalente al de otro hábito distinto, entonces el sistema deberá rechazarlo con el error E-2.
- Cuando el nuevo nombre sea equivalente al del propio hábito (por ejemplo, solo cambian las mayúsculas), el sistema deberá aceptarlo y guardar la nueva forma.

**RF-8 Borrar hábito**
- Cuando el usuario pida borrar un hábito existente, el sistema deberá pedir confirmación con el mensaje M-9.
- Cuando la respuesta, con los espacios recortados, sea exactamente "s" o "S", el sistema deberá eliminar el hábito junto con su historial y mostrar el mensaje M-10.
- Si la respuesta es cualquier otra, la entrada termina (EOF) o no es interactiva, entonces el sistema deberá cancelar sin cambiar nada y mostrar el aviso M-11.
- Si el usuario interrumpe con Ctrl+C durante la confirmación, entonces el sistema deberá cancelar sin cambiar nada y terminar con el código 130.

**RF-9 Persistencia**
- El sistema deberá conservar los hábitos y sus registros entre ejecuciones, con el contenido descrito en la sección 5.
- Si no existen datos previos, entonces el sistema deberá empezar con una lista vacía y crear el directorio de destino cuando guarde por primera vez.
- El sistema deberá leer los datos en UTF-8, con o sin BOM.
- El sistema deberá considerar corruptos los datos que no sean JSON válido, estén en otra codificación, tengan una estructura inesperada o una versión desconocida, o contengan fechas inválidas, fechas repetidas en un mismo hábito o nombres equivalentes repetidos.
- Si los datos están corruptos o no se pueden leer, entonces el sistema deberá mostrar el error E-5 y no modificarlos.
- Si no se pueden guardar los datos (por falta de permisos o de espacio), entonces el sistema deberá mostrar el error E-6 y dejar intactos los datos anteriores.
- El sistema deberá guardar de forma que una interrupción a mitad del guardado no deje los datos a medias.

**RF-10 Errores y códigos de salida**
- El sistema deberá terminar con 0 en caso de éxito, incluidos los avisos informativos (M-3, M-5, M-11).
- Si ocurre un error de datos o de dominio (E-2 a E-6, y los errores de nombre de RF-0), entonces el sistema deberá mostrar el mensaje por la salida de errores y terminar con 1.
- Si ocurre un error de uso (comando desconocido, o argumentos que faltan o sobran), entonces el sistema deberá mostrar el error E-1 y terminar con 2.
- El sistema deberá permitir nombres que empiecen por "-" si se escriben después del separador `--`.

### Mensajes

«X» es el nombre guardado del hábito y F una fecha en AAAA-MM-DD. Los errores llevan el prefijo "Error: ".

| Id | Texto |
|---|---|
| M-1 | `Hábito «X» creado.` |
| M-2 | `«X» marcado el F.` |
| M-3 | `«X» ya estaba marcado el F.` |
| M-4 | `«X» desmarcado el F.` |
| M-5 | `«X» no estaba marcado el F.` |
| M-6 | `[x] X — racha: N días` (hecho hoy) o `[ ] X — racha: N días`; con N = 1 se escribe `1 día` |
| M-7 | `No hay hábitos todavía.` |
| M-8 | `«X» renombrado a «Y».` |
| M-9 | `¿Borrar «X» y todo su historial? (s/n): ` |
| M-10 | `Hábito «X» borrado.` |
| M-11 | `Borrado cancelado.` |
| E-0 | `Error: el nombre no es válido: <motivo>.` (vacío, más de 50 caracteres o caracteres no imprimibles) |
| E-1 | `Error: uso incorrecto. <detalle>` |
| E-2 | `Error: ya existe un hábito llamado «X».` |
| E-3 | `Error: el hábito «X» no existe.` |
| E-4 | `Error: la fecha «F» no es válida (usa AAAA-MM-DD, entre 2000-01-01 y hoy).` |
| E-5 | `Error: los datos guardados están dañados o no se pueden leer; no se han modificado.` |
| E-6 | `Error: no se han podido guardar los datos; se conservan los anteriores.` |

## 5. Datos persistidos
- Documento JSON con una `version` (entera, actualmente 1) y una lista de hábitos.
- Cada hábito tiene su `name` (el nombre normalizado según RF-0) y `done` (las fechas marcadas, en AAAA-MM-DD, sin repeticiones y en orden ascendente).
- Cualquier cambio en este contenido requiere antes una nueva versión de esta spec y un incremento de `version`.

## 6. Requisitos no funcionales
- RNF-1: Todos los mensajes al usuario están en español y coinciden con la tabla de mensajes.
- RNF-2: La lógica de negocio y la persistencia no usan red ni dependencias externas en tiempo de ejecución. Se verifica con una prueba automática que revisa los imports.
- RNF-3: La lógica de negocio recibe el día actual como entrada en todas las operaciones (marcar, desmarcar, validar fechas y calcular la racha), de modo que se puede probar con un "hoy" controlado.
- RNF-4: Cada criterio de aceptación tiene al menos una prueba automatizada.
- RNF-5: Listar 200 hábitos con 5 años de historial cada uno tarda menos de 1 segundo, verificado con una prueba automatizada.

## 7. Casos límite
- Nombre con espacios en los extremos, tabuladores, espacios Unicode o espacios internos repetidos.
- Nombres que solo cambian en mayúsculas (equivalentes), en "ß"/"ss" (equivalentes), en acentos (distintos) o en normalización NFC/NFD (equivalentes).
- Nombre de exactamente 50 code points (válido) y de 51 (rechazado); nombre con un tabulador interno (rechazado).
- Nombre que empieza por "-" (válido si se escribe tras `--`) y nombre solo numérico (válido).
- Marcar dos veces el mismo día.
- Racha con hoy sin marcar y ayer marcado (se mantiene).
- Hueco de un día en el historial (la racha se corta ahí).
- Historial marcado de forma desordenada (con fechas pasadas añadidas después).
- Cambio de mes o de año, y el 29 de febrero, dentro de una racha.
- Racha de varios años.
- Desmarcar un día D en mitad de una racha: la racha solo cuenta los días posteriores a D y solo si llegan hasta hoy o ayer.
- Desmarcar hoy cuando ayer está marcado: la racha pasa a contar hasta ayer.
- Fechas "2026-02-30", "2026-13-01", "2026-9-1", "1999-12-31", la de mañana y la de hoy escrita de forma explícita.
- Fechas futuras ya guardadas (por un cambio de zona horaria o de reloj): se ignoran para la racha y se conservan.
- Ejecución justo antes y después de medianoche: "hoy" es el de cuando empezó la ejecución.
- Borrar o renombrar un hábito inexistente; renombrar a un nombre vacío tras normalizarlo.
- Renombrar un hábito a su mismo nombre con otras mayúsculas (se acepta).
- Confirmación de borrado con "S", " s ", "si", "sí", vacío, EOF o Ctrl+C.
- Archivo de datos inexistente, vacío, con JSON inválido, con BOM, en otra codificación, con fechas repetidas o con nombres equivalentes repetidos.
- Directorio de destino inexistente; datos sin permisos de escritura.
- Interrupción durante el guardado.

## 8. Fuera de alcance
- Hábitos con frecuencia no diaria (semanales, días concretos) y recordatorios.
- Estadísticas extra: mejor racha histórica, porcentajes, gráficos.
- Varios usuarios, sincronización o acceso remoto.
- Ejecuciones simultáneas: si dos ejecuciones guardan a la vez, se conserva la última.

## 9. Criterios de finalización
- Todos los RF-0 a RF-10 implementados y cubiertos por pruebas que pasan.
- Se cumplen los RNF-1 a RNF-5, cada uno con su prueba.
- Cada caso límite de la sección 7 tiene una prueba.

## 10. Historial de decisiones
- 2026-09-19: formato de fecha AAAA-MM-DD; el borrado siempre pide confirmación; el listado muestra la racha y "hecho hoy" en orden alfabético; el día actual es la fecha local; el nombre admite como máximo 50 caracteres.
- 2026-09-19: resueltos los 38 hallazgos de la revisión QA (normalización de nombres, tabla de mensajes, códigos de salida, rango de fechas, definición de datos corruptos, datos persistidos y RNF medibles).
