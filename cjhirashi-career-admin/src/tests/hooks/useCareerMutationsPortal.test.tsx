import React from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { careerApi } from '@/api/career'
import { useCareerMutations } from '@/hooks/useCareerResource'
import { createTestQueryClient } from '../utils'

vi.mock('@/api/career')

const setup = (resource: string) => {
  const client = createTestQueryClient()
  const spy = vi.spyOn(client, 'invalidateQueries')
  const wrapper = ({ children }: { children: React.ReactNode }) => <QueryClientProvider client={client}>{children}</QueryClientProvider>
  const hook = renderHook(() => useCareerMutations(resource), { wrapper })
  return { hook, spy }
}

/** ¿Alguna de las invalidaciones alcanza a una consulta con esta clave? */
const invalidates = (spy: ReturnType<typeof setup>['spy'], key: readonly unknown[]) =>
  spy.mock.calls.some(([filters]) => {
    if (!filters) return false
    const f = filters as { queryKey?: readonly unknown[]; predicate?: (q: { queryKey: readonly unknown[] }) => boolean }
    if (f.predicate) return f.predicate({ queryKey: key })
    return !!f.queryKey && f.queryKey.every((part, i) => key[i] === part)
  })

beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(careerApi.create).mockResolvedValue({} as never)
})

describe('guardar metas, embudos o anotaciones refresca el tablero de métricas', () => {
  it.each(['portal-goals', 'portal-funnels', 'portal-annotations'])('%s invalida las consultas de la analítica', async (resource) => {
    const { hook, spy } = setup(resource)
    hook.result.current.createMutation.mutate({ name: 'x' })
    await waitFor(() => expect(spy).toHaveBeenCalled())
    expect(invalidates(spy, ['career', 'portal-analytics-kpis', { q: {} }])).toBe(true)
    expect(invalidates(spy, ['career', 'portal-analytics-trend', { q: {} }])).toBe(true)
    expect(invalidates(spy, ['career', 'portal-analytics-goals', { q: {} }])).toBe(true)
    expect(invalidates(spy, ['career', 'portal-analytics-funnel', { q: {} }])).toBe(true)
  })

  it('otros recursos no tocan la analítica', async () => {
    const { hook, spy } = setup('projects')
    hook.result.current.createMutation.mutate({ name: 'x' })
    await waitFor(() => expect(spy).toHaveBeenCalled())
    expect(invalidates(spy, ['career', 'portal-analytics-kpis', { q: {} }])).toBe(false)
  })

  it('sigue invalidando las consultas del propio recurso', async () => {
    const { hook, spy } = setup('portal-goals')
    hook.result.current.createMutation.mutate({ name: 'x' })
    await waitFor(() => expect(spy).toHaveBeenCalled())
    expect(invalidates(spy, ['career', 'portal-goals', { skip: 0 }])).toBe(true)
  })
})
