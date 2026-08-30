# Arquitectura de Tablas — cjhirashi-career-api

Clasificación de las 62 tablas en tres categorías para facilitar la reutilización de la API.

## Categorías

### Sistema (27 tablas)

Núcleo reutilizable: se replican sin cambios en cualquier instancia de esta API.

→ [Ver detalle](sistema/README.md)

### Operativa (31 tablas)

Core del dominio `cjhirashi-career`: se rediseñan completamente al replicar para otro dominio.

→ [Ver detalle](operativa/README.md)

### Integración (4 tablas)

Adaptadores a plataformas externas (LinkedIn, GitHub).

→ [Ver detalle](integracion/README.md)

## Impacto de migración

| Acción | Tablas |
|--------|--------|
| Reusar sin cambios | 27 (Sistema) |
| Rediseñar para nuevo dominio | 31 (Operativa) |
| Evaluar según integraciones | 4 (Integración) |

## Criterio de clasificación

- **Sistema**: tabla no atada al dominio de negocio — aplica a cualquier sistema que use esta stack (auth, auditoría, agentes IA, panel admin, documentos).
- **Operativa**: tabla que refleja el modelo de negocio específico de gestión de carrera — completamente dependiente del dominio.
- **Integración**: adaptador a una plataforma externa específica — reutilizable solo si la misma integración aplica al nuevo proyecto.
