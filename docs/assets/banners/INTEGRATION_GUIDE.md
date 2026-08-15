# Guía de Integración de Banners

_Cómo integrar rápidamente los banners dinámicos en la documentación de MCP Tools Server._

---

## Vista Rápida

### 1. Estructura de Carpetas (Antes de Integración)

```
docs/
├── README.md
└── assets/
    └── banners/  ← NUEVO DIRECTORIO
        ├── README.md
        ├── banner-template.svg
        ├── getting-started.svg
        ├── api-reference.svg
        ├── troubleshooting.svg
        ├── configuration.svg
        └── INTEGRATION_GUIDE.md  ← Este archivo
```

### 2. Estructura Objetivo (Después de Integración)

```
docs/
├── README.md                          # Con banner-docs.svg
├── assets/
│   ├── banner-docs.svg               # Banner principal de docs (existente)
│   └── banners/                       # Nuevos banners por documento
│       └── *.svg
├── getting-started/
│   └── README.md                      # ![Getting Started](../assets/banners/getting-started.svg)
├── api/
│   └── README.md                      # ![API Reference](../assets/banners/api-reference.svg)
├── troubleshooting/
│   └── README.md                      # ![Troubleshooting](../assets/banners/troubleshooting.svg)
└── configuration/
    └── README.md                      # ![Configuration](../assets/banners/configuration.svg)
```

---

## Pasos de Integración

### Paso 1: Actualizar `docs/getting-started/README.md`

**Agregar banner al inicio:**

```markdown
![Getting Started](../assets/banners/getting-started.svg)

# Getting Started

[Resto del contenido...]
```

### Paso 2: Actualizar `docs/api/README.md`

**Agregar banner al inicio:**

```markdown
![API Reference](../assets/banners/api-reference.svg)

# API Reference

[Resto del contenido...]
```

### Paso 3: Actualizar `docs/troubleshooting/README.md`

**Agregar banner al inicio:**

```markdown
![Troubleshooting](../assets/banners/troubleshooting.svg)

# Troubleshooting

[Resto del contenido...]
```

### Paso 4: Actualizar `docs/configuration/README.md` (si existe)

**Agregar banner al inicio:**

```markdown
![Configuration](../assets/banners/configuration.svg)

# Configuration

[Resto del contenido...]
```

### Paso 5: Verificar en GitHub

1. Crea un Pull Request o rama
2. GitHub renderizará los SVG automáticamente
3. Verifica que los banners se vean correctamente en el preview

---

## Formato Correcto de Referencia de Banner

El formato en Markdown debe ser:

```markdown
![Descripción/Alternativa](ruta/relativa/al/banner.svg)
```

### Ejemplos por Ubicación

#### Desde `docs/getting-started/README.md`
```markdown
![Getting Started](../assets/banners/getting-started.svg)
```
- Sube 1 nivel: `../`
- Accede a `assets/banners/`

#### Desde `docs/api/README.md`
```markdown
![API Reference](../assets/banners/api-reference.svg)
```
- Sube 1 nivel: `../`
- Accede a `assets/banners/`

#### Desde `docs/README.md`
```markdown
![Documentación](assets/banner-docs.svg)
```
- Ya en `docs/`
- Accede directamente a `assets/`

---

## Validación Post-Integración

### Checklist

- [ ] Todos los banners se renderizan en GitHub (no aparecen como "broken image")
- [ ] Los títulos son legibles en tamaño pequeño (mobile)
- [ ] Las descripciones no están truncadas
- [ ] El footer "MCP Tools Server" es visible en todos
- [ ] Los colores del gradiente son consistentes
- [ ] No hay conflictos de IDs de gradiente en la misma página

### Cómo Verificar Localmente

```bash
# Abre el archivo README en tu navegador
firefox /path/to/docs/getting-started/README.md
# O en VS Code con Markdown Preview Enhanced
```

---

## Troubleshooting de Integración

### Problema: Banner No Se Renderiza

**Síntoma**: Se ve un icono de "imagen rota" (broken image)

**Soluciones**:
1. Verifica que la ruta sea relativa correcta
2. Confirma que el archivo SVG existe en `docs/assets/banners/`
3. Asegúrate de que el nombre del archivo sea exacto (case-sensitive)
4. Prueba en una rama diferente y haz push

```bash
# Verifica que el archivo exista
ls -la /mnt/disco2/cjhirashi-data/proyectos/mcp-server/docs/assets/banners/getting-started.svg
```

### Problema: Texto No Es Legible

**Síntoma**: Texto blanco o colores no visibles

**Soluciones**:
1. Verifica en GitHub (no en localhost, GitHub renderiza diferente)
2. Zoom in/out en navegador
3. Abre el SVG directamente en nueva pestaña

### Problema: Banners se Superponen en Índice

**Síntoma**: Si agregas múltiples banners en la misma página

**Soluciones**:
1. Cada documento debe tener SOLO 1 banner al inicio
2. No duplicar banners en la misma sección
3. Si quieres referencias visuales, linkea con `[Ver más](./getting-started/README.md)`

---

## Ejemplo Completo de Integración

### Antes (sin banner)

```markdown
# Getting Started

Welcome to MCP Tools Server. This guide will help you get started in 5 minutes.

## Prerequisites

- Docker installed
- Python 3.11+
```

### Después (con banner)

```markdown
![Getting Started](../assets/banners/getting-started.svg)

# Getting Started

Welcome to MCP Tools Server. This guide will help you get started in 5 minutes.

## Prerequisites

- Docker installed
- Python 3.11+
```

---

## Próximos Pasos

1. **Crear las secciones de documentación** si no existen:
   ```bash
   mkdir -p /mnt/disco2/cjhirashi-data/proyectos/mcp-server/docs/{getting-started,api,troubleshooting,configuration}
   ```

2. **Agregar los banners** a cada README usando las pautas anteriores

3. **Validar en GitHub** haciendo un PR o un push a rama de prueba

4. **Documentar nuevas secciones** usando `banner-template.svg` como base

---

## Mantenimiento Continuo

### Agregar Nueva Sección

Si agregas una nueva sección de documentación (ej: `docs/deployment/`):

1. Copia `banner-template.svg` a `docs/assets/banners/deployment.svg`
2. Edita título, descripción y tipo en el SVG
3. Crea `docs/deployment/README.md` con el banner
4. Referencia en índice principal de docs

### Cambiar Descripción Existente

Si una sección cambia significativamente:

1. Abre el SVG del banner correspondiente
2. Edita la descripción (línea 2 en el SVG)
3. Verifica que no se trunce
4. Haz commit con cambios documentarios

---

## Referencia de Banners Disponibles

| Banner | Ubicación | Uso |
|--------|-----------|-----|
| `getting-started.svg` | `docs/getting-started/` | Guía de inicio |
| `api-reference.svg` | `docs/api/` | Referencia de herramientas |
| `troubleshooting.svg` | `docs/troubleshooting/` | Solución de problemas |
| `configuration.svg` | `docs/configuration/` | Setup y configuración |
| `banner-template.svg` | N/A | Plantilla para nuevos banners |

---

## Contacto & Soporte

Si tienes dudas sobre:
- **Estructura de banners**: Ver `README.md` en este directorio
- **Personalización**: Ver "Crear un Nuevo Banner" en `README.md`
- **Validación visual**: Ver "Herramientas para Validar" en `README.md`

---

**Última actualización**: 2026-08-15  
**Proyecto**: MCP Tools Server
