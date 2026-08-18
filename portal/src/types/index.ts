// Identity Types
export interface Identity {
  id: string
  name: string
  title: string
  bio: string
  avatar: string
  location: string
  email: string
  phone?: string
  website?: string
  tagline: string
  ikigai?: {
    passion: string
    profession: string
    vocation: string
    mission: string
  }
  createdAt: string
  updatedAt: string
}

// Competencies Types
export interface Competency {
  id: string
  name: string
  level: 'beginner' | 'intermediate' | 'advanced' | 'expert'
  category: string
  years?: number
  description?: string
  verified?: boolean
}

// Project/Evidence Types
export interface Project {
  id: string
  title: string
  description: string
  shortDescription?: string
  thumbnail?: string
  images?: string[]
  technologies: string[]
  link?: string
  github?: string
  status: 'completed' | 'in-progress' | 'archived'
  startDate: string
  endDate?: string
  featured?: boolean
  metrics?: Record<string, string | number>
  createdAt: string
  updatedAt: string
}

// Blog/Networking Types
export interface BlogPost {
  id: string
  title: string
  slug: string
  excerpt: string
  content: string
  tags: string[]
  published: boolean
  publishedAt?: string
  image?: string
  readTime?: number
  createdAt: string
  updatedAt: string
}

// Contact Types
export interface ContactMessage {
  id?: string
  name: string
  email: string
  subject?: string
  message: string
  timestamp?: string
}

// Event Tracking Types
export type EventType = 'pageview' | 'click' | 'download' | 'form_submit' | 'scroll'

export interface TrackingEvent {
  type: EventType
  page: string
  target?: string
  metadata?: Record<string, unknown>
  timestamp?: string
  userAgent?: string
  ip?: string
}

// API Response Types
export interface ApiResponse<T> {
  data: T
  status: string
  message?: string
}

export interface ApiError {
  status: number
  message: string
  code?: string
}

// Theme Types
// 'light' | 'dark' are explicit user choices, 'system' follows the OS preference.
export type ThemeMode = 'light' | 'system' | 'dark'
export type ResolvedTheme = 'light' | 'dark'

// UI State Types
export interface UIState {
  /** User's theme preference, persisted to localStorage. */
  theme: ThemeMode
  /** 'system' resolved to an actual 'light' | 'dark' value, applied to the DOM. */
  resolvedTheme: ResolvedTheme
  mobileMenuOpen: boolean
  loading: boolean
  error: string | null
  setTheme: (theme: ThemeMode) => void
  toggleMobileMenu: () => void
  setMobileMenuOpen: (open: boolean) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
}
