import React from 'react'
import { clsx } from 'clsx'

export interface StateCapsuleProps {
  label: string
  tone: string
  className?: string
}

/**
 * Single-field status/priority chip. Color encodes the value; the label is
 * the human-readable name only (no machine-key rail).
 */
export const StateCapsule: React.FC<StateCapsuleProps> = ({ label, tone, className }) => (
  <span className={clsx('state-capsule', className)} data-tone={tone} title={label}>
    <span className="state-capsule-dot" aria-hidden="true" />
    <span className="state-capsule-label">{label}</span>
  </span>
)
