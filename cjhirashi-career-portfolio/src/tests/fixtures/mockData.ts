import { AboutContent, BlogPost, ContactContent, HomeContent, Project } from '@/types'

export const mockProjects: Project[] = [
  {
    id: '1',
    title: 'E-Commerce Platform',
    category: 'Systems',
    industry: 'Retail',
    year: 2023,
    card_summary: 'Full-featured e-commerce platform',
    tech_stack: ['React', 'Node.js', 'PostgreSQL', 'AWS'],
    metrics: { users: '10,000+', 'tiempo de entrega': '3.5 meses' },
    image_url: 'https://example.com/project1.jpg',
    github_url: 'https://github.com/example/project1',
    demo_url: 'https://example.com/project1',
    detailed_summary: 'A full-featured e-commerce platform built with React and Node.js',
    problem: 'Manual order processing.',
    solution: 'Automated pipeline.',
    architecture: 'Microservices on AWS.',
    approach_steps: 'Discovery, design, build, launch.',
    results: { uptime: '99.9%' },
    status: 'active',
    is_featured: true,
    is_anchor: true,
  },
  {
    id: '2',
    title: 'SaaS Dashboard',
    category: 'ML Ops',
    industry: 'SaaS',
    year: 2023,
    card_summary: 'Analytics dashboard for SaaS applications',
    tech_stack: ['React', 'TypeScript', 'GraphQL'],
    metrics: null,
    image_url: null,
    github_url: null,
    demo_url: 'https://example.com/project2',
    detailed_summary: 'Analytics dashboard for SaaS applications',
    problem: null,
    solution: null,
    architecture: null,
    approach_steps: null,
    results: null,
    status: 'active',
    is_featured: true,
    is_anchor: false,
  },
  {
    id: '3',
    title: 'Mobile App',
    category: 'Mobile',
    industry: null,
    year: 2024,
    card_summary: 'React Native mobile application',
    tech_stack: ['React Native', 'Firebase'],
    metrics: null,
    image_url: null,
    github_url: null,
    demo_url: null,
    detailed_summary: null,
    problem: null,
    solution: null,
    architecture: null,
    approach_steps: null,
    results: null,
    status: 'in_development',
    is_featured: false,
    is_anchor: false,
  },
]

export const mockFeaturedProjects = mockProjects.filter(p => p.is_featured)

export const mockBlogPosts: BlogPost[] = [
  {
    id: '1',
    title: 'Understanding System Design',
    slug: 'understanding-system-design',
    excerpt: 'Deep dive into system design principles and best practices.',
    image_url: 'https://example.com/blog1.jpg',
    content_type: 'Arquitectura',
    platform: 'Blog propio',
    published_at: '2024-08-10T00:00:00Z',
    reading_minutes: 8,
    tags: ['Architecture', 'Design', 'System Design'],
    body_content: 'Full content about system design...',
    publication_url: null,
  },
  {
    id: '2',
    title: 'React Best Practices',
    slug: 'react-best-practices',
    excerpt: 'Essential practices for writing better React code.',
    image_url: null,
    content_type: 'Pensamiento Sistémico',
    platform: 'LinkedIn',
    published_at: '2024-08-05T00:00:00Z',
    reading_minutes: 5,
    tags: ['React', 'JavaScript', 'Frontend'],
    body_content: 'Full content about React practices...',
    publication_url: null,
  },
  {
    id: '3',
    title: 'TypeScript Tips',
    slug: 'typescript-tips',
    excerpt: 'Advanced TypeScript techniques.',
    image_url: null,
    content_type: 'Arquitectura',
    platform: 'Blog propio',
    published_at: '2024-08-01T00:00:00Z',
    reading_minutes: 6,
    tags: ['TypeScript', 'JavaScript'],
    body_content: 'Full content about TypeScript...',
    publication_url: null,
  },
]

export const mockHome: HomeContent = {
  hero_photo_url: 'https://example.com/avatar.jpg',
  hero_title: 'Carlos Jiménez Hirashi',
  hero_subtitle: 'AI Solutions Architect',
  hero_intro: 'Transformando ideas complejas en soluciones elegantes y escalables.',
  hero_ctas: [
    { label: 'Ver Caso Bioterio', url: '/projects/1' },
    { label: 'Ver proyectos', url: '/projects' },
  ],
  stats: [
    { label: 'Años en Sistemas Críticos', value: '20+' },
    { label: 'Proyectos Completados', value: '15' },
    { label: 'Equipos Liderados', value: '5' },
    { label: 'Uptime Sostenido', value: '99.9%' },
  ],
  anchor_project: mockProjects[0],
  featured_projects: mockProjects.filter(p => p.is_featured),
  featured_publications: mockBlogPosts.slice(0, 1),
  skill_categories: ['Data Science & IA', 'Cloud'],
}

export const mockAbout: AboutContent = {
  name: 'Carlos A. Jiménez Hirashi',
  professional_tagline: 'AI Solutions Architect | Intelligent Automation',
  bio_summary: 'Passionate about building scalable solutions and continuous learning.',
  unique_value_proposition: 'Diseño y programo la solución completa.',
  photo_url: 'https://example.com/avatar.jpg',
  work_history: [
    {
      company: 'Tech Company',
      role_title: 'Senior Solutions Architect',
      start_date: '2020-01-01',
      end_date: null,
      description: 'Leading architecture and design of enterprise-scale applications.',
      achievements: [
        {
          id: 'ach-1',
          title: 'Reduced downtime by 80% in the first year.',
          executive_storytelling: null,
        },
      ],
      key_metrics: { downtime_reduction: '80%' },
    },
  ],
  skill_groups: [
    { category: 'Frontend', skills: ['React', 'TypeScript'] },
    { category: 'Cloud', skills: ['AWS'] },
  ],
  certifications: [
    {
      name: 'AWS Certified',
      institution: 'Amazon',
      year: 2023,
      description: 'Arquitectura de soluciones en AWS (SAA-C03).',
    },
  ],
}

export const mockContact: ContactContent = {
  contact_email: 'cjhirashi@gmail.com',
  whatsapp: '+52 55 1371 0160',
  location: 'Ciudad de México, México · GMT-6',
  availability_status: 'Disponible para nuevos proyectos',
  preferred_contact_method: 'Email',
  footer_links: [{ label: 'Sitio personal', url: 'https://cjhirashi.com' }],
  linkedin_url: 'https://linkedin.com/in/cjhirashi',
  github_url: 'https://github.com/cjhirashi',
}

export const mockContactMessage = {
  name: 'John Doe',
  email: 'john@example.com',
  message: 'I would like to discuss a project opportunity.',
}

export const mockTrackingEvent = {
  type: 'click' as const,
  page: '/home',
  target: 'test-button',
  metadata: {},
}
