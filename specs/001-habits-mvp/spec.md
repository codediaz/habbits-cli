# Spec 001 — MVP de habits-cli

## 1. Contexto y objetivo
Quien estudia de forma autodidacta necesita constancia, y ver una racha de días seguidos motiva a no romperla. El objetivo es una herramienta de línea de comandos que permita registrar hábitos de estudio diarios, marcar los días cumplidos y consultar la racha actual de cada hábito, de forma local y sin cuentas.

## 2. Usuarios
- **Estudiante:** una sola persona que usa la herramienta en su propio equipo desde la terminal.
- **Desarrollador junior:** mantiene el proyecto, así que la spec debe ser clara y comprobable.

## 3. Historias de usuario
- HU-1: Como estudiante, quiero crear un hábito con un nombre para empezar a seguirlo.
- HU-2: Como estudiante, quiero marcar un hábito como hecho hoy para registrar mi progreso.
- HU-3: Como estudiante, quiero marcar o desmarcar un día pasado para corregir olvidos o errores.
- HU-4: Como estudiante, quiero listar mis hábitos con su racha actual para ver cómo voy.
- HU-5: Como estudiante, quiero renombrar o borrar un hábito para mantener la lista al día.

## 4. Requisitos funcionales

**RF-1 Crear hábito**
- Cuando el usuario cree un hábito con un nombre válido, el sistema deberá guardarlo con el historial vacío y confirmarlo con un mensaje.
- El sistema deberá recortar los espacios del inicio y del final del nombre antes de validarlo.
- Si el nombre queda vacío tras recortarlo, entonces el sistema deberá rechazarlo con un mensaje de error.
- Si el nombre supera los 50 caracteres tras recortarlo o contiene caracteres no imprimibles, entonces el sistema deberá rechazarlo con un mensaje de error.
- Si ya existe un hábito con el mismo nombre sin distinguir mayúsculas, entonces el sistema deberá rechazarlo con un mensaje de error.

**RF-2 Identificación de hábitos**
- El sistema deberá identificar cada hábito por su nombre, sin distinguir mayúsculas y sin los espacios de los extremos.
- Si una orden hace referencia a un hábito que no existe, entonces el sistema deberá mostrar un error indicando que no existe.

**RF-3 Marcar hoy**
- El sistema deberá considerar como día actual la fecha local del equipo; a partir de medianoche es el día siguiente.
- Cuando el usuario marque un hábito como hecho sin indicar fecha, el sistema deberá registrar el día actual y confirmarlo.
- Si el día ya estaba marcado, entonces el sistema deberá informar de que ya lo estaba, no cambiar nada y terminar con éxito.

**RF-4 Marcar un día pasado**
- Cuando el usuario marque un hábito indicando una fecha pasada válida, el sistema deberá registrar ese día.
- El sistema deberá aceptar las fechas solo en formato AAAA-MM-DD.
- Si la fecha es futura, no existe o no sigue ese formato, entonces el sistema deberá rechazarla con un mensaje de error.
- Si ese día ya estaba marcado, entonces el sistema deberá informar de ello sin error.

**RF-5 Desmarcar un día**
- Cuando el usuario desmarque un día de un hábito (hoy por defecto, o una fecha indicada), el sistema deberá eliminar ese registro y confirmarlo.
- Si ese día no estaba marcado, entonces el sistema deberá informar de ello sin error.

**RF-6 Listar hábitos con racha**
- Cuando el usuario pida la lista, el sistema deberá mostrar cada hábito con su racha actual y una indicación de si está hecho hoy, ordenados alfabéticamente sin distinguir mayúsculas.
- Mientras no haya hábitos, el sistema deberá mostrar un mensaje indicando que la lista está vacía.
- El sistema deberá calcular la racha como el número de días consecutivos marcados que terminan hoy o, si hoy no está marcado, ayer.
- Si no están marcados ni hoy ni ayer, entonces el sistema deberá mostrar una racha de 0.

**RF-7 Renombrar hábito**
- Cuando el usuario renombre un hábito existente con un nombre válido, el sistema deberá cambiar el nombre y conservar su historial.
- Si el nuevo nombre está vacío, supera los 50 caracteres o coincide con el de otro hábito, entonces el sistema deberá rechazarlo con un mensaje de error.

**RF-8 Borrar hábito**
- Cuando el usuario pida borrar un hábito existente, el sistema deberá pedir confirmación (s/n) antes de borrarlo.
- Cuando el usuario confirme el borrado, el sistema deberá eliminar el hábito junto con su historial y confirmarlo.
- Si el usuario no confirma, entonces el sistema deberá cancelar el borrado sin cambiar nada e informar de ello.

**RF-9 Persistencia**
- El sistema deberá conservar los hábitos y sus registros entre ejecuciones.
- Si no existen datos previos, entonces el sistema deberá empezar con una lista vacía.
- Si los datos guardados están corruptos o no se pueden leer, entonces el sistema deberá mostrar un error claro y no sobrescribirlos.

**RF-10 Errores**
- Si ocurre cualquier error de uso o de datos, entonces el sistema deberá mostrar un mensaje en español y terminar con un código de salida distinto de 0.

## 5. Requisitos no funcionales
- RNF-1: Todos los mensajes al usuario están en español.
- RNF-2: Funciona sin conexión y sin dependencias externas en tiempo de ejecución.
- RNF-3: El cálculo de la racha no depende de la interfaz y se puede probar de forma aislada con una fecha "hoy" controlada.
- RNF-4: Cada criterio de aceptación tiene al menos una prueba automatizada.
- RNF-5: Las respuestas son inmediatas para un uso personal (cientos de hábitos y años de registros).

## 6. Casos límite
- Nombre con espacios en los extremos o con mayúsculas distintas de las de un nombre existente.
- Marcar dos veces el mismo día.
- Racha con hoy sin marcar y ayer marcado (se mantiene).
- Hueco de un día en el historial (la racha se corta ahí).
- Historial marcado de forma desordenada (con fechas pasadas añadidas después).
- Cambio de mes o de año, y el 29 de febrero, dentro de una racha.
- Desmarcar un día en mitad de una racha (la parte a partir de ese día deja de contar).
- Nombre de exactamente 50 caracteres (válido) y de 51 (rechazado).
- Fecha inexistente, como 2026-02-30.
- Responder algo distinto de s/n al confirmar un borrado (se cancela).
- Renombrar un hábito a su mismo nombre con otras mayúsculas.
- Archivo de datos inexistente, vacío o con contenido inválido.

## 7. Fuera de alcance
- Hábitos con frecuencia no diaria (semanales, días concretos) y recordatorios.
- Estadísticas extra: mejor racha histórica, porcentajes, gráficos.
- Varios usuarios, sincronización o acceso remoto.

## 8. Criterios de finalización
- Todos los RF-1 a RF-10 implementados y cubiertos por pruebas que pasan.
- Se cumplen los RNF-1 a RNF-5.
- Cada caso límite de la sección 6 tiene una prueba.
- Las dudas abiertas se han resuelto o se han pasado a una spec posterior.

## 9. Dudas abiertas
Ninguna. Resueltas el 2026-09-19:
- Formato de fecha: solo AAAA-MM-DD (RF-4).
- Borrar un hábito siempre pide confirmación (RF-8).
- El listado muestra la racha y si está hecho hoy, en orden alfabético (RF-6).
- El día actual es la fecha local del equipo (RF-3).
- El nombre admite como máximo 50 caracteres imprimibles (RF-1, RF-7).
