# AGENTS.md - Núcleo de Gobernanza del Arnés

## 1. Protocolo de Arranque Obligatorio
Antes de ejecutar cualquier tarea o modificar código, el agente DEBE:
1. Ejecutar el script computacional de validación de entorno: `./init.sh`
2. Si el script falla o devuelve errores, **DETENERSE inmediatamente** y reportar el problema. No intentar programar sobre un entorno roto.
3. Leer el estado actual de las tareas externas en `progress/current.json`.

## 2. Directrices de Eficiencia de Tokens (Context Engineering)
- **Cero Redundancia:** Ve directo al grano. No expliques fragmentos de código obvios ni repitas explicaciones largas en el chat.
- **Memoria Externa:** No guardes el progreso en el historial conversacional. Anota los avances y los siguientes pasos directamente en la carpeta `progress/`.

## 3. Normas de Ejecución y Roles
- **Roles:** Si operas como Agente Líder, delega subtareas acotadas. Si operas como Implementador, escribe código limpio y directo utilizando herramientas básicas del sistema de archivos y bash.
- **Validación Estricta:** Ninguna tarea puede marcarse como completada (`done`) a menos que el entorno y las pruebas locales respondan con éxito a través del script del arnés.

## 4. Protocolo de Auto-Aprendizaje (Self-Improving Loop)
- **Registro de Correcciones:** Si el usuario te corrige un error de lógica, patrón de arquitectura o convención, NO olvides el feedback. Anótalo inmediatamente en `progress/memory.md`.
- **Arranque con Memoria:** Al iniciar cada nueva sesión, lee obligatoriamente los aprendizajes acumulados en `progress/memory.md` para evitar reincidir en errores pasados[cite: 11].
- **Evolución del Arnés:** Si durante la ejecución de una tarea detectas que una regla en este `AGENTS.md` es imprecisa o incompleta, propón una actualización justificada al final de tu informe de progreso.

## 5. Protocolo de Actualización Autónoma del Sensor (`init.sh`)
- **Evaluación Periódica:** Al inicio de cada ciclo de desarrollo o cuando se integre una nueva funcionalidad (*feature*), el agente tiene la directriz obligatoria de inspeccionar el estado actual del repositorio (dependencias, módulos y pruebas).
- **Evolución del Script:** Si se detectan nuevos requerimientos técnicos, dependencias o componentes que deban ser probados, el agente **debe actualizar por sí mismo el archivo `./init.sh`** para incorporar las nuevas validaciones o pruebas unitarias necesarias.
- **Compuerta de Bloqueo Automática:** Ninguna validación añadida debe ser ignorada; el archivo `./init.sh` actualizado debe seguir funcionando como una barrera estricta que bloquea la ejecución si el entorno no cumple con los requisitos mínimos de calidad.