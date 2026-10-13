import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import {
  VACANCY_STAGE_OPTIONS,
  VACANCY_STATUS_LABELS,
  vacancyStageBadgeColor,
  vacancyStatusBadgeColor,
} from '@/config/careerResources'

// RF-018 / D-15: contraste WCAG 2.1 AA (>= 4.5:1) de los badges de Vacantes en ambos temas.
// Los badges usan CSS propio (.badge-*) con tokens de index.css; los fondos son translúcidos,
// así que se compone el rgba sobre las superficies de cada tema (misma medición que spec §8.1).

const css = readFileSync(path.resolve(__dirname, '../../index.css'), 'utf8')

type RGB = [number, number, number]

const blockAfter = (selector: string): string => {
  const start = css.indexOf(selector)
  if (start < 0) throw new Error(`Selector no encontrado: ${selector}`)
  const open = css.indexOf('{', start)
  let depth = 0
  for (let i = open; i < css.length; i++) {
    if (css[i] === '{') depth++
    else if (css[i] === '}' && --depth === 0) return css.slice(open + 1, i)
  }
  throw new Error(`Bloque sin cerrar: ${selector}`)
}

const lightTokens = blockAfter(':root {')
const darkTokens = blockAfter("[data-theme='dark'] {")

const token = (block: string, name: string): string => {
  const m = new RegExp(`${name}:\\s*([^;]+);`).exec(block)
  if (!m) throw new Error(`Token no encontrado: ${name}`)
  return m[1].trim()
}

const parseColor = (value: string): { rgb: RGB; alpha: number } => {
  const hex = /^#([0-9a-f]{6})$/i.exec(value)
  if (hex) {
    const n = parseInt(hex[1], 16)
    return { rgb: [(n >> 16) & 255, (n >> 8) & 255, n & 255], alpha: 1 }
  }
  const rgba = /^rgba?\(\s*(\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\s*\)$/.exec(value)
  if (!rgba) throw new Error(`Color no soportado: ${value}`)
  return { rgb: [+rgba[1], +rgba[2], +rgba[3]], alpha: rgba[4] === undefined ? 1 : +rgba[4] }
}

const over = (fg: { rgb: RGB; alpha: number }, base: RGB): RGB =>
  fg.rgb.map((c, i) => c * fg.alpha + base[i] * (1 - fg.alpha)) as RGB

const luminance = ([r, g, b]: RGB): number => {
  const lin = (c: number) => {
    const s = c / 255
    return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4
  }
  return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)
}

const ratio = (a: RGB, b: RGB): number => {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x)
  return (hi + 0.05) / (lo + 0.05)
}

// Variante de Badge -> tokens (.badge-* en index.css). slate usa --text-secondary / --bg-glass.
const VARIANT_TOKENS: Record<string, { text: string; bg: string }> = {
  warning: { text: '--warning-text', bg: '--warning-bg' },
  success: { text: '--success-text', bg: '--success-bg' },
  error: { text: '--error-text', bg: '--error-bg' },
  slate: { text: '--text-secondary', bg: '--bg-glass' },
}

// Variantes que usan realmente los badges de Vacantes (derivadas de las funciones de color).
const usedVariants = [
  ...new Set([
    ...VACANCY_STAGE_OPTIONS.map((o) => vacancyStageBadgeColor(o.value)),
    ...Object.keys(VACANCY_STATUS_LABELS).map((s) => vacancyStatusBadgeColor(s)),
    vacancyStageBadgeColor(undefined),
  ]),
] as string[]

// Superficies: tema claro = blanco y página; tema oscuro = página y card sobre página.
const lightPage = parseColor(token(lightTokens, '--bg-primary')).rgb
const darkPage = parseColor(token(darkTokens, '--bg-primary')).rgb
const darkCard = over(parseColor(token(darkTokens, '--bg-card')), darkPage)

const surfaces: Array<{ theme: string; name: string; tokens: string; base: RGB }> = [
  { theme: 'claro', name: 'blanco', tokens: lightTokens, base: [255, 255, 255] },
  { theme: 'claro', name: 'página', tokens: lightTokens, base: lightPage },
  { theme: 'oscuro', name: 'página', tokens: darkTokens, base: darkPage },
  { theme: 'oscuro', name: 'card', tokens: darkTokens, base: darkCard },
]

describe('RF-018: contraste de badges de Vacantes (WCAG AA >= 4.5:1)', () => {
  it('Vacantes usa las 4 variantes medidas', () => {
    expect([...usedVariants].sort()).toEqual(['error', 'slate', 'success', 'warning'])
  })

  for (const variant of ['warning', 'success', 'error', 'slate']) {
    for (const s of surfaces) {
      it(`${variant} en tema ${s.theme} sobre ${s.name}`, () => {
        const t = VARIANT_TOKENS[variant]
        const bg = over(parseColor(token(s.tokens, t.bg)), s.base)
        const fg = parseColor(token(s.tokens, t.text)).rgb
        const r = ratio(fg, bg)
        expect(r, `${variant}/${s.theme}/${s.name}: ${r.toFixed(2)}`).toBeGreaterThanOrEqual(4.5)
      })
    }
  }
})
