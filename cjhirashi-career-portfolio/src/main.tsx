import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'
import { reportClientError } from '@/utils/reportClientError'

window.addEventListener('error', (event) => {
  reportClientError({
    message: event.message || 'window.onerror',
    source: `portfolio:window.onerror ${window.location.pathname}`,
    error_type: (event.error as Error | undefined)?.name,
    stack_trace: (event.error as Error | undefined)?.stack,
    context: { filename: event.filename, lineno: event.lineno, colno: event.colno },
  })
})

window.addEventListener('unhandledrejection', (event) => {
  const reason = event.reason as { message?: string; name?: string; stack?: string } | undefined
  reportClientError({
    message: (reason?.message || String(event.reason) || 'unhandledrejection').toString(),
    source: `portfolio:unhandledrejection ${window.location.pathname}`,
    error_type: reason?.name,
    stack_trace: reason?.stack,
  })
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
