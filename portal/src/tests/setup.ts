import '@testing-library/jest-dom'
import { afterEach, vi } from 'vitest'
import { useUIStore } from '@/stores/uiStore'

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  takeRecords() {
    return []
  }
  unobserve() {}
} as any

// The UI store (theme, mobile menu) is a module-level singleton shared
// across tests within the same file - reset the transient bits after every
// test so one test's interactions can't leak into the next.
afterEach(() => {
  useUIStore.setState({ mobileMenuOpen: false })
})
