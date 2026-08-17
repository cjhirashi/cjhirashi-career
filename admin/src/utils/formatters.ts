import { format, formatDistanceToNow, parseISO } from 'date-fns'

// Date formatting
export const formatDate = (dateString: string, formatStr: string = 'MMM dd, yyyy'): string => {
  try {
    const date = typeof dateString === 'string' ? parseISO(dateString) : dateString
    return format(date, formatStr)
  } catch {
    return 'Invalid date'
  }
}

export const formatDateTime = (
  dateString: string,
  formatStr: string = 'MMM dd, yyyy HH:mm'
): string => {
  try {
    const date = typeof dateString === 'string' ? parseISO(dateString) : dateString
    return format(date, formatStr)
  } catch {
    return 'Invalid date'
  }
}

export const formatRelativeTime = (dateString: string): string => {
  try {
    const date = typeof dateString === 'string' ? parseISO(dateString) : dateString
    return formatDistanceToNow(date, { addSuffix: true })
  } catch {
    return 'Unknown'
  }
}

// Number formatting
export const formatNumber = (value: number): string => {
  return new Intl.NumberFormat('en-US').format(value)
}

export const formatCurrency = (value: number, currency: string = 'USD'): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
  }).format(value)
}

export const formatPercent = (value: number, decimals: number = 0): string => {
  return `${(value * 100).toFixed(decimals)}%`
}

// String formatting
export const formatFullName = (firstName: string, lastName: string): string => {
  return `${firstName} ${lastName}`.trim()
}

export const capitalize = (str: string): string => {
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase()
}

export const formatSlug = (str: string): string => {
  return str
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

export const truncate = (str: string, length: number = 50): string => {
  if (str.length <= length) return str
  return `${str.substring(0, length).trim()}...`
}

// Array formatting
export const formatList = (items: string[], separator: string = ', '): string => {
  if (items.length === 0) return ''
  if (items.length === 1) return items[0]
  if (items.length === 2) return items.join(' and ')
  return `${items.slice(0, -1).join(separator)}${separator}and ${items[items.length - 1]}`
}

// Duration formatting (e.g., "1 year 3 months")
export const formatDuration = (months: number): string => {
  const years = Math.floor(months / 12)
  const remainingMonths = months % 12

  const parts: string[] = []
  if (years > 0) {
    parts.push(`${years} year${years > 1 ? 's' : ''}`)
  }
  if (remainingMonths > 0) {
    parts.push(`${remainingMonths} month${remainingMonths > 1 ? 's' : ''}`)
  }

  return parts.length > 0 ? parts.join(' ') : '< 1 month'
}

// Proficiency level to display string
export const formatProficiencyLevel = (level: string): string => {
  const levels: Record<string, string> = {
    beginner: 'Beginner',
    intermediate: 'Intermediate',
    advanced: 'Advanced',
    expert: 'Expert',
  }
  return levels[level] || level
}

// Job application status to display string
export const formatJobApplicationStatus = (status: string): string => {
  const statuses: Record<string, string> = {
    applied: 'Applied',
    rejected: 'Rejected',
    interview: 'Interview',
    offer: 'Offer',
    accepted: 'Accepted',
  }
  return statuses[status] || status
}

// Competency category to display string
export const formatCompetencyCategory = (category: string): string => {
  const categories: Record<string, string> = {
    technical: 'Technical',
    transferable: 'Transferable',
    business: 'Business',
  }
  return categories[category] || category
}

// Format file size
export const formatFileSize = (bytes: number): string => {
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
  if (bytes === 0) return '0 Bytes'

  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return Math.round((bytes / Math.pow(1024, i)) * 100) / 100 + ' ' + sizes[i]
}

// Format phone number
export const formatPhone = (phone: string): string => {
  const cleaned = phone.replace(/\D/g, '')
  if (cleaned.length !== 10 && cleaned.length !== 11) return phone

  const isLong = cleaned.length === 11
  const areaCode = cleaned.slice(isLong ? 1 : 0, isLong ? 4 : 3)
  const firstPart = cleaned.slice(isLong ? 4 : 3, isLong ? 7 : 6)
  const secondPart = cleaned.slice(isLong ? 7 : 6)

  return `(${areaCode}) ${firstPart}-${secondPart}`
}
