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