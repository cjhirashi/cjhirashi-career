# ADR-028: Contraste de los tokens semánticos de texto del Admin (tema claro)

## Estado

Aceptado — 2026-10-13 (decisión del usuario D-15, feature 007, Fase 4).

## Contexto

La revisión UX de la feature 007 (`spec.md` §8.1, hallazgo B-1) midió el contraste WCAG 2.1
de los badges de Vacantes componiendo sus fondos translúcidos sobre las superficies de cada
tema. En el tema **claro**, `--warning-text` (#d97706), `--success-text` (#059669) y
`--error-text` (#dc2626) quedaban entre 2.71 y 4.14:1 sobre su fondo al 10%, por debajo del
umbral AA de 4.5:1. La etapa más frecuente (`warning`, 8 de 13) era la peor. El tema oscuro
cumplía (mínimo 5.25:1). Estos tokens los usan todos los badges y textos semánticos del
Admin, no sólo Vacantes.

## Decisión

Oscurecer **sólo** tres tokens del tema claro en `cjhirashi-career-admin/src/index.css`:

| Token | Antes | Ahora | Ratio (blanco / página) |
|---|---|---|---|
| `--warning-text` | #d97706 | #92400e | 6.38 / 6.02 |
| `--success-text` | #059669 | #065f46 | 6.81 / 6.45 |
| `--error-text` | #dc2626 | #b91c1c | 5.54 / 5.23 |

No cambian el tema oscuro, los `-bg`, los `-border` ni ningún otro token. No se añaden
variantes de `Badge` ni colores nuevos fuera de la paleta (se ajusta el tono de tokens
existentes). La regresión la guarda `src/tests/styles/badgeContrast.test.ts`, que lee el
CSS y exige >= 4.5:1 para cada variante usada por Vacantes en ambos temas.

## Alternativas descartadas

- **Aceptar el contraste como deuda:** incumple RF-018 y la accesibilidad AA.
- **Usar sólo `slate` en Vacantes:** pierde la distinción por color entre etapas.
- **Variante local sólo para Vacantes:** deja el mismo fallo en el resto de badges del Admin.
- **`#b45309` para warning:** no basta (4.52 / 4.26).

## Consecuencias

- Mejora el contraste de todos los badges y textos `warning`/`success`/`error` del tema
  claro del Admin; el cambio visual es global y deliberado (tonos más oscuros).
- Cualquier token semántico nuevo o ajustado deberá pasar el mismo test.
- Los bordes (`*-border`) son decorativos y no se miden.
