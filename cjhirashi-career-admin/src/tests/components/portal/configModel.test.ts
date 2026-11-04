import { describe, expect, it } from 'vitest'
import {
  buildMatch,
  describeMatch,
  emptyStep,
  moveStep,
  readMatch,
  stepsFromApi,
  stepsToPayload,
  validateFunnel,
  validateMatchInput,
} from '@/components/career/portal/configModel'

describe('buildMatch / readMatch hablan el mismo diccionario que el servidor', () => {
  it.each([
    ['event', 'download', { event_type: 'download' }],
    ['page', '/projects/', { path_prefix: '/projects/' }],
    ['outbound', ' linkedin.com ', { url_contains: 'linkedin.com' }],
    ['min_active', '30', { ms: 30000 }],
    ['min_active', '1.5', { ms: 1500 }],
    ['min_pages', '3', { pages: 3 }],
  ])('%s «%s» -> %j', (type, input, expected) => {
    expect(buildMatch(type, input)).toEqual(expected)
  })

  it('leer devuelve lo que se escribió (los milisegundos vuelven a segundos)', () => {
    expect(readMatch('min_active', { ms: 30000 })).toBe('30')
    expect(readMatch('page', { path_prefix: '/blog' })).toBe('/blog')
    expect(readMatch('page', {})).toBe('')
    expect(readMatch('page', null)).toBe('')
  })

  it('un tipo desconocido es un error de programación, no un valor silencioso', () => {
    expect(() => buildMatch('nope', 'x')).toThrow()
  })
})

describe('describeMatch', () => {
  it('describe cada tipo en español', () => {
    expect(describeMatch('event', { event_type: 'download' })).toBe('Evento: Descarga de archivo')
    expect(describeMatch('event', { event_type: 'raro' })).toBe('Evento: raro')
    expect(describeMatch('page', { path_prefix: '/projects/' })).toBe('Ruta que empieza con /projects/')
    expect(describeMatch('outbound', { url_contains: 'github.com' })).toBe('Enlace que contiene github.com')
    expect(describeMatch('min_active', { ms: 45000 })).toBe('45 s activos o más')
    expect(describeMatch('min_pages', { pages: 3 })).toBe('3 páginas o más')
  })
  it('sin valor muestra el nombre del tipo y con tipo desconocido lo devuelve tal cual', () => {
    expect(describeMatch('page', {})).toBe('Página vista')
    expect(describeMatch('otro', {})).toBe('otro')
  })
})

describe('validateMatchInput', () => {
  it('rechaza vacío, no numérico, cero y negativos', () => {
    expect(validateMatchInput('page', '  ')).toBe('Falta el valor.')
    expect(validateMatchInput('min_active', 'abc')).toBe('Escribe un número mayor que cero.')
    expect(validateMatchInput('min_active', '0')).toBe('Escribe un número mayor que cero.')
    expect(validateMatchInput('min_pages', '-2')).toBe('Escribe un número mayor que cero.')
  })
  it('las páginas por visita deben ser enteras y las rutas empezar con barra', () => {
    expect(validateMatchInput('min_pages', '2.5')).toBe('Escribe un número entero.')
    expect(validateMatchInput('page', 'projects')).toBe('La ruta debe empezar con «/».')
  })
  it('acepta valores correctos (segundos con decimales sí)', () => {
    expect(validateMatchInput('min_active', '1.5')).toBeNull()
    expect(validateMatchInput('page', '/')).toBeNull()
    expect(validateMatchInput('outbound', 'x.com')).toBeNull()
    expect(validateMatchInput('event', 'click')).toBeNull()
  })
})

describe('embudos', () => {
  const ok = [
    { label: 'Inicio', type: 'page', value: '/' },
    { label: 'Descarga', type: 'event', value: 'download' },
  ]

  it('el servidor exige al menos 2 pasos y nombre', () => {
    expect(validateFunnel('CV', ok)).toEqual([])
    expect(validateFunnel('', ok)).toContain('Falta el nombre del embudo.')
    expect(validateFunnel('CV', ok.slice(0, 1))).toContain('Un embudo necesita al menos 2 pasos.')
  })

  it('señala el paso con el problema', () => {
    const errors = validateFunnel('CV', [{ label: '', type: 'page', value: '/' }, { label: 'B', type: 'page', value: 'sin-barra' }])
    expect(errors).toEqual(['El paso 1 no tiene nombre.', 'Paso 2: La ruta debe empezar con «/».'])
  })

  it('ida y vuelta con la forma del servidor', () => {
    const payload = stepsToPayload(ok)
    expect(payload).toEqual([
      { label: 'Inicio', type: 'page', match: { path_prefix: '/' } },
      { label: 'Descarga', type: 'event', match: { event_type: 'download' } },
    ])
    expect(stepsFromApi(payload)).toEqual(ok)
    expect(stepsFromApi(null)).toEqual([])
  })

  it('un paso nuevo arranca en página, vacío', () => {
    expect(emptyStep()).toEqual({ label: '', type: 'page', value: '' })
  })

  it('moveStep reordena sin tocar el original y se queda quieto en los bordes', () => {
    const list = ['a', 'b', 'c']
    expect(moveStep(list, 2, 0)).toEqual(['c', 'a', 'b'])
    expect(moveStep(list, 0, 1)).toEqual(['b', 'a', 'c'])
    expect(moveStep(list, 0, -1)).toBe(list)
    expect(moveStep(list, 2, 3)).toBe(list)
    expect(list).toEqual(['a', 'b', 'c'])
  })
})
