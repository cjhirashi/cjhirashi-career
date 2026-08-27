import React from 'react'
import ReactDOM from 'react-dom/client'
import { App } from './App'
import './index.css'
import { reportClientError } from '@/utils/reportClientError'

window.addEventListener('error', (event) => {
  reportClientError({
    message: event.message || 'window.onerror',
    source: `admin:window.onerror ${window.location.pathname}`,
    error_type: event.error?.name,
    stack_trace: event.error?.stack,
    context: { filename: event.filename, lineno: event.lineno, colno: event.colno },
  })
})

window.addEventListener('unhandledrejection', (event) => {
  const reason = event.reason
  reportClientError({
    message: (reason?.message || String(reason) || 'unhandledrejection').toString(),
    source: `admin:unhandledrejection ${window.location.pathname}`,
    error_type: reason?.name,
    stack_trace: reason?.stack,
  })
})

const rootElement = document.getElementById('root')
if (!rootElement) {
  throw new Error('Root element not found')
}

ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
