// User and Authentication Types
export interface User {
  id: number
  username: string
  email: string
  full_name: string
  phone?: string
  country?: string
  professional_title?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  expires_in: number
  user: User
}

export interface TokenRefreshResponse {
  access_token: string
  expires_in: number
}

// Career Modules Types

// Identity Module
export interface Identity {
  id: number
  user_id: number
  ikigai_what_do_i_do?: string
  ikigai_what_do_i_love?: string
  ikigai_what_am_i_good_at?: string
  ikigai_what_pays?: string
  differentiators?: string[]
  professional_narrative?: string
  value_proposition?: string
  created_at: string
  updated_at: string
}

// Competencies Module
export type CompetencyCategory = 'technical' | 'transferable' | 'business'

export interface Competency {
  id: number
  user_id: number
  name: string
  category: CompetencyCategory
  level: 'beginner' | 'intermediate' | 'advanced' | 'expert'
  description?: string
  years_of_experience?: number
  is_verified: boolean
  verified_by?: string
  created_at: string
  updated_at: string
}

// Evidence Module
export interface Project {
  id: number
  user_id: number
  title: string
  description: string
  technologies: string[]
  link?: string
  start_date: string
  end_date?: string
  created_at: string
  updated_at: string
}

export interface Position {
  id: number
  user_id: number
  title: string
  company: string
  start_date: string
  end_date?: string
  description?: string
  achievements?: string[]
  created_at: string
  updated_at: string
}

export interface Achievement {
  id: number
  user_id: number
  title: string
  type: 'award' | 'certification' | 'recognition'
  date: string
  issuer?: string
  description?: string
  created_at: string
  updated_at: string
}

export interface STARCase {
  id: number
  user_id: number
  situation: string
  task: string
  action: string
  result: string
  related_skills?: string[]
  context?: string
  created_at: string
  updated_at: string
}

// Job Strategies Module
export interface JobStrategy {
  id: number
  user_id: number
  target_title: string
  target_companies: string[]
  target_industries: string[]
  status: 'active' | 'paused' | 'completed'
  created_at: string
  updated_at: string
}

export interface JobApplication {
  id: number
  user_id: number
  company: string
  position: string
  status: 'applied' | 'rejected' | 'interview' | 'offer' | 'accepted'
  application_date: string
  follow_up_date?: string
  notes?: string
  created_at: string
  updated_at: string
}

// Networking Module
export interface NetworkContact {
  id: number
  user_id: number
  name: string
  role: string
  company: string
  email: string
  phone?: string
  linkedin_url?: string
  last_contact: string
  notes?: string
  created_at: string
  updated_at: string
}

export interface NetworkingOpportunity {
  id: number
  user_id: number
  type: 'referral' | 'collaboration' | 'mentorship' | 'partnership'
  description: string
  status: 'open' | 'in_progress' | 'completed'
  source?: string
  created_at: string
  updated_at: string
}

// Interview Preparation Module
export interface InterviewQuestion {
  id: number
  user_id: number
  question: string
  category: 'behavioral' | 'technical' | 'domain'
  difficulty: 'easy' | 'medium' | 'hard'
  created_at: string
  updated_at: string
}

export interface InterviewAnswer {
  id: number
  user_id: number
  question_id: number
  answer: string
  status: 'draft' | 'ready'
  created_at: string
  updated_at: string
}

// API Response Wrapper
export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

// UI Types
export interface LoadingState {
  isLoading: boolean
  error: string | null
}

export interface NotificationState {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  message: string
  duration?: number
}

export interface PaginationParams {
  page: number
  size: number
  sort?: string
}
