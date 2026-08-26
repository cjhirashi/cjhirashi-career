import React from 'react'
import { clsx } from 'clsx'

interface StatusIndicatorProps {
  active: boolean
  className?: string
}

/**
 * Read-only status chip for boolean fields in record viewers and tables.
 * Not a switch: a LED + label so the value is scanned, not operated.
 */
export const StatusIndicator: React.FC<StatusIndicatorProps> = ({ active, className }) => (
  <span
    className={clsx('status-indicator', className)}
    data-on={active ? 'true' : 'false'}
    role="status"
  >
    <span className="status-indicator-dot" aria-hidden="true" />
    <span className="status-indicator-label">{active ? 'Activo' : 'Inactivo'}</span>
  </span>
)
