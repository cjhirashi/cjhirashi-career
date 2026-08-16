// Logger utility for development and debugging

const LOG_LEVELS = {
  DEBUG: 0,
  INFO: 1,
  WARN: 2,
  ERROR: 3,
} as const

type LogLevel = keyof typeof LOG_LEVELS

const currentLogLevel = import.meta.env.MODE === 'development' ? LOG_LEVELS.DEBUG : LOG_LEVELS.WARN

const formatTimestamp = (): string => {
  return new Date().toLocaleTimeString()
}

const formatMessage = (level: LogLevel, message: string, ...args: any[]): string => {
  return `[${formatTimestamp()}] [${level}] ${message}`
}

export const logger = {
  debug: (message: string, ...args: any[]) => {
    if (LOG_LEVELS.DEBUG >= currentLogLevel) {
      console.debug(formatMessage('DEBUG', message), ...args)
    }
  },

  info: (message: string, ...args: any[]) => {
    if (LOG_LEVELS.INFO >= currentLogLevel) {
      console.info(formatMessage('INFO', message), ...args)
    }
  },

  warn: (message: string, ...args: any[]) => {
    if (LOG_LEVELS.WARN >= currentLogLevel) {
      console.warn(formatMessage('WARN', message), ...args)
    }
  },

  error: (message: string, ...args: any[]) => {
    if (LOG_LEVELS.ERROR >= currentLogLevel) {
      console.error(formatMessage('ERROR', message), ...args)
    }
  },
}

// Performance monitoring
export const performance = {
  startMeasure: (label: string) => {
    if (import.meta.env.MODE === 'development') {
      window.performance.mark(`${label}-start`)
    }
  },

  endMeasure: (label: string) => {
    if (import.meta.env.MODE === 'development') {
      window.performance.mark(`${label}-end`)
      try {
        window.performance.measure(label, `${label}-start`, `${label}-end`)
        const measure = window.performance.getEntriesByName(label)[0]
        logger.debug(`${label}: ${measure.duration.toFixed(2)}ms`)
      } catch {
        logger.warn(`Failed to measure ${label}`)
      }
    }
  },
}
