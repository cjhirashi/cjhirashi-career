// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'
export const API_TIMEOUT = 10000 // 10 seconds

// Token Configuration
export const ACCESS_TOKEN_KEY = 'access_token'
export const REFRESH_TOKEN_KEY = 'refresh_token'
export const TOKEN_EXPIRES_AT_KEY = 'token_expires_at'

// Routes
export const ROUTES = {
  LOGIN: '/login',
  DASHBOARD: '/dashboard',
  IDENTITY: '/identity',
  COMPETENCIES: '/competencies',
  EVIDENCE: '/evidence',
  JOB_STRATEGIES: '/job-strategies',
  NETWORKING: '/networking',
  INTERVIEWS: '/interviews',
  METRICS: '/metrics',
} as const

// Competency Levels
export const COMPETENCY_LEVELS = {
  BEGINNER: 'beginner',
  INTERMEDIATE: 'intermediate',
  ADVANCED: 'advanced',
  EXPERT: 'expert',
} as const

// Competency Categories
export const COMPETENCY_CATEGORIES = {
  TECHNICAL: 'technical',
  TRANSFERABLE: 'transferable',
  BUSINESS: 'business',
} as const

// Job Application Status
export const JOB_APPLICATION_STATUS = {
  APPLIED: 'applied',
  REJECTED: 'rejected',
  INTERVIEW: 'interview',
  OFFER: 'offer',
  ACCEPTED: 'accepted',
} as const

// Interview Question Categories
export const INTERVIEW_QUESTION_CATEGORIES = {
  BEHAVIORAL: 'behavioral',
  TECHNICAL: 'technical',
  DOMAIN: 'domain',
} as const

// Interview Difficulty Levels
export const INTERVIEW_DIFFICULTY = {
  EASY: 'easy',
  MEDIUM: 'medium',
  HARD: 'hard',
} as const

// Toast Messages
export const MESSAGES = {
  SUCCESS: {
    LOGIN: 'Successfully logged in',
    CREATE: 'Item created successfully',
    UPDATE: 'Item updated successfully',
    DELETE: 'Item deleted successfully',
    LOGOUT: 'Successfully logged out',
  },
  ERROR: {
    LOGIN: 'Login failed. Please check your credentials.',
    NETWORK: 'Network error. Please try again.',
    UNAUTHORIZED: 'Your session has expired. Please login again.',
    VALIDATION: 'Please check your input and try again.',
    SERVER: 'Server error. Please try again later.',
  },
  INFO: {
    LOADING: 'Loading...',
    SAVING: 'Saving...',
  },
} as const

// Pagination
export const DEFAULT_PAGE_SIZE = 10
export const PAGE_SIZE_OPTIONS = [10, 25, 50, 100] as const

// Date Formats
export const DATE_FORMATS = {
  DISPLAY: 'MMM dd, yyyy',
  INPUT: 'yyyy-MM-dd',
  FULL: 'MMM dd, yyyy HH:mm',
} as const
