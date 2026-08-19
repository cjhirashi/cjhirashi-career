// Mirrors api/src/schemas/linkedin.py

export interface LinkedInStatus {
  connected: boolean
  member_name: string | null
  member_email: string | null
  profile_picture_url: string | null
  expires_at: string | null
}

export interface LinkedInPostEntity {
  id: number
  text: string
  linkedin_post_urn: string | null
  published_at: string
}
