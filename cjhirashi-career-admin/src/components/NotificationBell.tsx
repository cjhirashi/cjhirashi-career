import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Bell } from 'lucide-react'
import { clsx } from 'clsx'
import { useNotificationMutations, useNotifications } from '@/hooks/useNotifications'
import { formatDateTime } from '@/utils/formatters'

export const NotificationBell: React.FC = () => {
  const [open, setOpen] = useState(false)
  const navigate = useNavigate()
  const { listQuery, unreadCount } = useNotifications()
  const { markRead, markAllRead } = useNotificationMutations()
  const items = listQuery.data ?? []

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((current) => !current)}
        aria-label="Avisos"
        aria-expanded={open}
        title="Avisos"
        className="relative p-2 rounded-xl text-text-secondary hover:bg-glass hover:text-text focus:outline-none focus:ring-2 focus:ring-cyan-500"
      >
        <Bell size={18} aria-hidden="true" />
        {unreadCount > 0 && (
          <span className="absolute top-1 right-1 min-w-[1rem] h-4 px-1 rounded-full bg-cyan-600 text-white text-[10px] leading-4 text-center font-semibold">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>
      {open && (
        <div className="popover-menu absolute right-0 mt-2 w-80 max-w-[90vw] z-50">
          <div className="p-3 border-b border-border flex items-center justify-between gap-2">
            <p className="text-sm font-medium text-text">Avisos</p>
            {unreadCount > 0 && (
              <button
                type="button"
                className="text-xs text-cyan-600 dark:text-cyan-400 hover:underline"
                onClick={() => markAllRead.mutate()}
              >
                Marcar leídos
              </button>
            )}
          </div>
          <ul className="max-h-80 overflow-auto p-1">
            {items.length === 0 && (
              <li className="px-3 py-6 text-sm text-text-secondary text-center">No hay avisos.</li>
            )}
            {items.map((item) => (
              <li key={item.id}>
                <button
                  type="button"
                  className={clsx(
                    'w-full text-left px-3 py-2 rounded-lg hover:bg-glass transition-colors',
                    !item.read_at && 'bg-cyan-500/5'
                  )}
                  onClick={() => {
                    markRead.mutate(item.id)
                    setOpen(false)
                    if (item.resource_key === 'agent-tasks' && item.resource_id) {
                      navigate(`/tasks?task=${encodeURIComponent(item.resource_id)}`)
                    }
                  }}
                >
                  <p className="text-sm text-text font-medium">{item.title}</p>
                  {item.body && <p className="text-xs text-text-secondary mt-0.5">{item.body}</p>}
                  <p className="text-[11px] text-text-muted mt-1">{formatDateTime(item.created_at)}</p>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
