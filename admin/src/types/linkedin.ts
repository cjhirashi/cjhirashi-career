// Mirrors api/src/schemas/linkedin.py

export interface LinkedInStatus {
  connected: boolean
  member_name: string | null
  member_email: string | null
  profile_picture_url: string | null
  expires_at: string | null
}

export type LinkedInPostStatus = 'scheduled' | 'published' | 'failed'

export interface LinkedInPostEntity {
  id: number
  text: string
  image_url: string | null
  status: LinkedInPostStatus
  error_message: string | null
  linkedin_post_urn: string | null
  scheduled_at: string | null
  published_at: string | null
  created_at: string
}
