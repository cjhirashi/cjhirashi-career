// ============================================================================
// Career Domain (v2) - TypeScript types mirroring api/src/schemas/career_*.py
// and the "CAREER DOMAIN SCHEMA (v2)" section of api/init.sql.
//
// These are intentionally kept close to the Pydantic Response schemas: every
// optional/nullable column is typed as `T | null` because FastAPI serializes
// `None` as `null` (the key is always present in the JSON payload).
// ============================================================================

export type ISODate = string
export type ISODateTime = string

// ---------------------------------------------------------------------------
// Dominio 1: Identidad Profesional
// ---------------------------------------------------------------------------

export interface Differentiator {
  id: number
  user_id: number
  pillar_name: string
  pillar_description?: string | null
  strengths?: string[] | null
  evidence?: string | null
  is_active: boolean
  created_at: ISODateTime
  updated_at: ISODateTime
}

export interface Identity {
  id: number
  user_id: number
  professional_tagline?: string | null
  bio_summary?: string | null
  unique_value_proposition?: string | null
  created_at: ISODateTime
  updated_at: ISODateTime
}

export type IdentityDimension = 'passion' | 'profession' | 'vocation' | 'mission'

export interface IdentityReflection {
  id: number
  user_id: number
  dimension: IdentityDimension
  content?: string | null
  tags?: string[] | null
  updated_at: ISODateTime
}

export type CompetencyType = 'technical' | 'transferable' | 'business'

export interface Competency {
  id: number
  user_id: number
  name: string
  type: CompetencyType
  category?: string | null
  level?: string | null
  years_of_experience?: number | null
  practice_start_date?: ISODate | null
  context_libraries?: unknown[] | null
  depth_description?: string | null
  market_gaps?: string | null
  honesty_note?: string | null
  aligned_differentiator_ids?: number[] | null
  proficiency_score?: number | null
  is_highlighted: boolean
  created_at: ISODateTime
  updated_at: ISODateTime
}

export interface Certification {
  id: number
  user_id: number
  name: string
  institution?: string | null
  year?: number | null
  description?: string | null
  related_competency_id?: number | null
  created_at: ISODateTime
}

export interface TargetRole {
  id: number
  user_id: number
  role_name: string
  priority_order?: number | null
  salary_median?: number | null
  salary_min?: number | null
  salary_max?: number | null
  years_experience_required?: number | null
  description?: string | null
  market_active_vacancies?: number | null
  market_validated_at?: ISODate | null
  market_sources?: unknown[] | null
  current_accessibility?: string | null
  key_requirements?: string[] | null
  is_active: boolean
  created_at: ISODateTime
  updated_at: ISODateTime
}

export interface WorkHistory {
  id: number
  user_id: number
  company: string
  role_title: string
  start_date?: ISODate | null
  end_date?: ISODate | null
  people_managed?: string | null
  description?: string | null
  narrative?: string | null
  achievements?: string[] | null
  key_metrics?: Record<string, unknown> | null
  learnings?: string | null
  contract_type?: string | null
  industry_sector?: string | null
  created_at: ISODateTime
}

export type EvidenceType = 'direct_account' | 'public_backed'

export interface Achievement {
  id: number
  user_id: number
  title: string
  work_history_id?: number | null
  context?: Record<string, unknown> | null
  challenge?: string | null
  solution?: string | null
  impact_metrics?: Record<string, unknown> | null
  evidence_type?: EvidenceType | null
  documentation_urls?: string[] | null
  executive_storytelling?: string | null
  demonstrated_competency_ids?: number[] | null
  visible_on_cv: boolean
  visible_in_interview: boolean
  visible_on_portal: boolean
  created_at: ISODateTime
}

export interface StarStory {
  id: number
  user_id: number
  title: string
  duration_seconds?: number | null
  narrative?: string | null
  key_points?: string[] | null
  achievement_id?: number | null
  cross_pattern?: string | null
  role_application?: string | null
  times_practiced: number
  active_in_interviews: boolean
  created_at: ISODateTime
}

export type ReviewType = 'gap_analysis' | 'transition_decision' | 'quarterly_review'
export type TrackingStatus = 'active' | 'completed' | 'paused'

export interface CareerReview {
  id: number
  user_id: number
  review_date?: ISODate | null
  review_type?: ReviewType | null
  context?: string | null
  decision_or_finding?: string | null
  result_or_learning?: string | null
  action_items?: string[] | null
  tracking_status: TrackingStatus
  created_at: ISODateTime
}

export type Severity = 'critical' | 'high' | 'medium' | 'low'
export type Viability = 'viable' | 'viable_with_caveats' | 'not_viable'
export type ClosureStatus = 'not_started' | 'in_progress' | 'completed' | 'paused'

export interface RoleGapAnalysis {
  id: number
  user_id: number
  target_role_id: number
  gap_name: string
  severity?: Severity | null
  market_requirement?: string | null
  closing_plan?: string | null
  viability?: Viability | null
  closure_status: ClosureStatus
  created_at: ISODateTime
}

export type ProjectStatus = 'active' | 'in_development' | 'archived'

export interface Project {
  id: number
  user_id: number
  title: string
  category?: string | null
  industry?: string | null
  year?: number | null
  card_summary?: string | null
  detailed_summary?: string | null
  problem?: string | null
  solution?: string | null
  architecture?: string | null
  tech_stack?: string[] | null
  metrics?: Record<string, unknown> | null
  approach_steps?: string[] | null
  results?: Record<string, unknown> | null
  github_url?: string | null
  demo_url?: string | null
  repo_structure?: string | null
  evidence_sources?: string[] | null
  releases?: unknown[] | null
  status: ProjectStatus
  is_featured: boolean
  created_at: ISODateTime
  updated_at: ISODateTime
}

// ---------------------------------------------------------------------------
// Dominio 2: Operativa de Búsqueda
// ---------------------------------------------------------------------------

export interface FitScoringFactor {
  id: number
  user_id: number
  factor_name: string
  weight_percentage?: number | null
  scoring_guide?: string | null
  display_order?: number | null
}

export type MarketType = 'visible' | 'hidden'

export interface MarketSegment {
  id: number
  user_id: number
  market_type?: MarketType | null
  channel_name?: string | null
  channel_type?: string | null
  strategy_text?: string | null
  applications_made: number
  responses_received: number
  interviews_achieved: number
  priority?: number | null
  is_active: boolean
  created_at: ISODateTime
}

export interface RoleNarrative {
  id: number
  user_id: number
  target_role_id?: number | null
  title: string
  usage_context?: string | null
  full_narrative?: string | null
  key_points?: string[] | null
  is_active: boolean
  created_at: ISODateTime
  updated_at: ISODateTime
}

export type PlanStatus = 'not_started' | 'in_progress' | 'paused' | 'completed' | 'cancelled'

export interface SearchPlan {
  id: number
  user_id: number
  period_start?: ISODate | null
  period_end?: ISODate | null
  target_role_id?: number | null
  weekly_targets?: Record<string, unknown> | null
  primary_channels?: string[] | null
  target_cvs_sent?: number | null
  target_interviews?: number | null
  target_offers?: number | null
  plan_status: PlanStatus
  completion_percentage: number
  lessons_learned?: string | null
  created_at: ISODateTime
  updated_at: ISODateTime
}

export type RoleCategory =
  | 'data_director'
  | 'automation_ai_peer'
  | 'manager_team_lead'
  | 'specialized_recruiter'
  | 'target_company_lead'
export type ContactStatus = 'pending' | 'contacted' | 'following_up' | 'converted'

export interface NetworkingContact {
  id: number
  user_id: number
  name: string
  role_title?: string | null
  company_or_specialty?: string | null
  linkedin_url?: string | null
  email?: string | null
  role_category?: RoleCategory | null
  contact_status: ContactStatus
  how_originated?: string | null
  notes?: string | null
  created_at: ISODateTime
  updated_at: ISODateTime
}

export interface TargetCompany {
  id: number
  user_id: number
  company_name: string
  tier?: number | null
  best_fit_role_id?: number | null
  company_size?: string | null
  salary_estimate?: string | null
  work_modality?: string | null
  target_market?: string | null
  weak_tie_contact_id?: number | null
  priority?: string | null
  status?: string | null
  notes?: string | null
  created_at: ISODateTime
  updated_at: ISODateTime
}

export type Evaluation = 'apply' | 'do_not_apply' | 'pending_review'

export interface Vacancy {
  id: number
  user_id: number
  order_number?: number | null
  company: string
  exact_role: string
  vacancy_url?: string | null
  source?: string | null
  found_date?: ISODate | null
  fit_percentage?: number | null
  track_category?: string | null
  recommended_cv_version?: string | null
  analysis_notes?: string | null
  evaluation: Evaluation
  is_active: boolean
  created_at: ISODateTime
}

export type VersionStatus = 'draft' | 'approved' | 'final'

export interface CVVersion {
  id: number
  user_id: number
  target_role_id?: number | null
  title: string
  length_pages?: number | null
  status: VersionStatus
  executive_summary?: string | null
  key_competencies?: string[] | null
  key_experience?: unknown[] | null
  featured_achievement?: string | null
  target_vacancy_ids?: number[] | null
  file_upload_id?: number | null
  created_at: ISODateTime
  updated_at: ISODateTime
}

export interface CoverLetterVersion {
  id: number
  user_id: number
  target_role_id?: number | null
  target_vacancy_id?: number | null
  title: string
  status: VersionStatus
  body_content?: string | null
  file_upload_id?: number | null
  created_at: ISODateTime
  updated_at: ISODateTime
}

export type CurrentStatus = 'applied' | 'in_process' | 'offer' | 'rejected' | 'archived'
export type FinalResult = 'offer_accepted' | 'offer_rejected' | 'rejected' | 'negotiating'

export interface Application {
  id: number
  user_id: number
  vacancy_id: number
  applied_at?: ISODateTime | null
  cv_version_id?: number | null
  cover_letter_version_id?: number | null
  current_status: CurrentStatus
  recruiter_contact_id?: number | null
  final_result?: FinalResult | null
  created_at: ISODateTime
}

export interface ApplicationInteraction {
  id: number
  user_id: number
  application_id: number
  interaction_at?: ISODateTime | null
  channel?: string | null
  content_sent?: string | null
  response_received?: string | null
  status?: string | null
  created_at: ISODateTime
}

export type OverallImpression = 'very_positive' | 'positive' | 'neutral' | 'negative'
export type InterviewResult = 'pending' | 'advanced' | 'rejected' | 'under_consideration'

export interface Interview {
  id: number
  user_id: number
  application_id: number
  interview_type?: string | null
  scheduled_at?: ISODateTime | null
  interviewers?: string[] | null
  questions_asked?: string[] | null
  answers_given?: string[] | null
  feedback_received?: string | null
  overall_impression?: OverallImpression | null
  narrative_used_id?: number | null
  interview_result?: InterviewResult | null
  created_at: ISODateTime
}

export interface ContactInteraction {
  id: number
  user_id: number
  contact_id: number
  related_vacancy_id?: number | null
  interaction_at?: ISODateTime | null
  channel?: string | null
  content_sent?: string | null
  response_received?: string | null
  status?: string | null
  generated_opportunity: boolean
  created_at: ISODateTime
}

export type NetworkingCategory = 'give_value_70' | 'share_learning_20' | 'talk_about_you_10'

export interface NetworkingActivity {
  id: number
  user_id: number
  category?: NetworkingCategory | null
  activity_type: string
  concrete_action?: string | null
  example?: string | null
  frequency_description?: string | null
  times_completed: number
  is_active: boolean
  created_at: ISODateTime
}

// ---------------------------------------------------------------------------
// Dominio 3: Presencia Digital
// ---------------------------------------------------------------------------

export type PlatformName =
  | 'linkedin'
  | 'github'
  | 'kaggle'
  | 'portfolio_web'
  | 'medium'
  | 'twitter'
  | 'other'

export interface DigitalPlatform {
  id: number
  user_id: number
  platform_name?: PlatformName | null
  profile_url?: string | null
  profile_status?: string | null
  platform_strategy?: string | null
  followers_count?: number | null
  is_active_in_search: boolean
  created_at: ISODateTime
}

export type ContentStatus = 'draft' | 'scheduled' | 'published'

export interface ContentPiece {
  id: number
  user_id: number
  title: string
  slug?: string | null
  excerpt?: string | null
  body_content?: string | null
  content_type?: string | null
  thematic_pillar?: string | null
  tags?: string[] | null
  status: ContentStatus
  reading_minutes?: number | null
  featured_on_home: boolean
  scheduled_publish_at?: ISODateTime | null
  related_project_id?: number | null
  related_achievement_id?: number | null
  related_competency_id?: number | null
  created_at: ISODateTime
}

export interface Publication {
  id: number
  user_id: number
  content_piece_id: number
  platform_id: number
  published_title?: string | null
  publication_url?: string | null
  published_at?: ISODateTime | null
  full_content?: string | null
  char_length?: number | null
  hashtags_used?: string[] | null
  views?: number | null
  likes_reactions?: number | null
  comments?: number | null
  shares?: number | null
  content_status: ContentStatus
  created_at: ISODateTime
}

// ---------------------------------------------------------------------------
// Dominio 4: Soporte
// ---------------------------------------------------------------------------

export interface Tag {
  id: number
  user_id: number
  tag_name: string
  entity_type?: string | null
  color_hex?: string | null
  is_active: boolean
  created_at: ISODateTime
}

// ---------------------------------------------------------------------------
// Metrics (read-only view)
// ---------------------------------------------------------------------------

export interface WeeklySearchMetrics {
  week_start: ISODate | null
  applications_sent: number
  responses_received: number
  response_rate_percentage: number | null
  interviews_scheduled: number
  offers: number
  rejections: number
}

/** Any career-domain entity always has at least these two columns. */
export interface CareerEntity {
  id: number
  user_id: number
  [key: string]: unknown
}
