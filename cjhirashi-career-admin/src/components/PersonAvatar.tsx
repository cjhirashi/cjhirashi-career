import React from 'react'
import { clsx } from 'clsx'

export function initialsFromName(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (parts.length === 0) return '?'
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase()
}

interface PersonAvatarProps {
  src?: string | null
  name: string
  size?: number
  className?: string
}

export const PersonAvatar: React.FC<PersonAvatarProps> = ({ src, name, size = 24, className }) => (
  <span
    className={clsx('person-avatar', className)}
    style={{ width: size, height: size, fontSize: Math.max(9, Math.round(size * 0.38)) }}
    title={name}
    aria-hidden="true"
  >
    {src ? <img src={src} alt="" /> : initialsFromName(name)}
  </span>
)

export const PersonChip: React.FC<PersonAvatarProps & { label?: string; variant?: 'plain' | 'capsule' }> = ({
  src,
  name,
  size = 22,
  className,
  label,
  variant = 'plain',
}) => (
  <span
    className={clsx(
      variant === 'capsule' ? 'actor-capsule' : 'inline-flex items-center gap-2 min-w-0',
      className
    )}
    title={label ?? name}
  >
    <PersonAvatar src={src} name={name} size={variant === 'capsule' ? 20 : size} />
    <span className={clsx('truncate', variant === 'capsule' && 'actor-capsule-name')}>{label ?? name}</span>
  </span>
)
