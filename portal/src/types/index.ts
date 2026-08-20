// ============================================================================
// Mirrors api/src/schemas/public.py - the unauthenticated /public/* API this
// portal reads from (single portfolio owner, see PUBLIC_PORTAL_USER_ID).
// ============================================================================

// Projects
export interface Project {
  id: number
  title: string
  category: string | null
  industry: string | null
  year: number | null
  card_summary: string | null
  tech_stack: string[]
  metrics: Record<string, unknown> | unknown[] | null
  image_url: string | null
  github_url: string | null
  demo_url: string | null
  detailed_summary: string | null
  problem: string | null
  solution: string | null
  architecture: string | null
  approach_steps: string | null
  results: Record<string, unknown> | unknown[] | null
  status: string | null
  is_featured: boolean
  is_anchor: boolean
}

// Blog
export interface BlogPost {
  id: number
  title: string
  slug: string | null
  excerpt: string | null
  image_url: string | null
  content_type: string | null
  platform: string | null
  published_at: string | null
  reading_minutes: number | null
  tags: string[]
  body_content: string | null
  publication_url: string | null
}

// Home
export interface HomeStat {
  label: string
  value: string
}

export interface HomeContent {
  hero_photo_url: string | null
  hero_title: string | null
  hero_subtitle: string | null
  hero_intro: string | null
  stats: HomeStat[]
  anchor_project: Project | null
  featured_projects: Project[]
  featured_publications: BlogPost[]
}

// About
export interface WorkHistoryEntry {
  company: string
  role_title: string
  start_date: string | null
  end_date: string | null
  description: string | null
  narrative: string | null
  achievements: string | null
  key_metrics: Record<string, unknown> | unknown[] | null
}

export interface SkillGroup {
  category: string
  skills: string[]
}

export interface CertificationEntry {
  name: string
  institution: string | null
  year: number | null
}

export interface AboutContent {
  professional_tagline: string | null
  bio_summary: string | null
  unique_value_proposition: string | null
  photo_url: string | null
  work_history: WorkHistoryEntry[]
  skill_groups: SkillGroup[]
  certifications: CertificationEntry[]
}

// Contact
export interface FooterLink {
  label: string
  url: string
}

export interface ContactContent {
  contact_email: string | null
  whatsapp: string | null
  location: string | null
  availability_status: string | null
  preferred_contact_method: string | null
  footer_links: FooterLink[]
  linkedin_url: string | null
  github_url: string | null
}

// Contact form (client-side only - no backend endpoint to receive it yet)
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
