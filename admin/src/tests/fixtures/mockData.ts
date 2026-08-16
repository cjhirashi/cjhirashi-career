import { User, LoginResponse, Identity, Competency } from '@/types'

export const mockUser: User = {
  id: 1,
  username: 'demo',
  email: 'demo@example.com',
  full_name: 'Demo User',
  phone: '1234567890',
  country: 'US',
  professional_title: 'Software Engineer',
  is_active: true,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
}

export const mockLoginResponse: LoginResponse = {
  access_token: 'mock_access_token_123',
  refresh_token: 'mock_refresh_token_456',
  expires_in: 3600,
  user: mockUser,
}

export const mockIdentity: Identity = {
  id: 1,
  user_id: 1,
  ikigai_what_do_i_do: 'Build scalable backend systems',
  ikigai_what_do_i_love: 'Problem solving with elegant code',
  ikigai_what_am_i_good_at: 'Software architecture, Python, databases',
  ikigai_what_pays: 'Enterprise software solutions',
  differentiators: [
    'Deep expertise in cloud architecture',
    'Strong track record scaling startups',
    'Proven leadership in distributed teams',
  ],
  professional_narrative: 'I am a software engineer with 8+ years of experience...',
  value_proposition: 'I deliver scalable, maintainable solutions that drive business value',
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
}

export const mockCompetency: Competency = {
  id: 1,
  user_id: 1,
  name: 'Python',
  category: 'technical',
  level: 'expert',
  description: 'Expert-level Python development',
  years_of_experience: 8,
  is_verified: true,
  verified_by: 'Employer A',
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
}

export const mockCompetencies: Competency[] = [
  mockCompetency,
  {
    ...mockCompetency,
    id: 2,
    name: 'Leadership',
    category: 'transferable',
    level: 'advanced',
  },
  {
    ...mockCompetency,
    id: 3,
    name: 'Product Strategy',
    category: 'business',
    level: 'intermediate',
  },
]
