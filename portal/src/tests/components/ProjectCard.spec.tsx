import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '../testUtils'
import userEvent from '@testing-library/user-event'
import { trackingApi } from '@/api/tracking'
import { ProjectCard } from '@/components/Common/ProjectCard'
import { mockProjects } from '../fixtures/mockData'

vi.mock('@/api/tracking')

describe('ProjectCard Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders project title', () => {
    const project = mockProjects[0]
    render(<ProjectCard project={project} />)

    expect(screen.getByText(project.title)).toBeInTheDocument()
  })

  it('renders the card summary', () => {
    const project = mockProjects[0]
    render(<ProjectCard project={project} />)

    expect(screen.getByText(project.card_summary!)).toBeInTheDocument()
  })

  it('renders the category and industry badges', () => {
    const project = mockProjects[0]
    render(<ProjectCard project={project} />)

    expect(screen.getByText(project.category!)).toBeInTheDocument()
    expect(screen.getByText(project.industry!)).toBeInTheDocument()
  })

  it('renders the year', () => {
    const project = mockProjects[0]
    render(<ProjectCard project={project} />)

    expect(screen.getByText(String(project.year))).toBeInTheDocument()
  })

  it('renders the image when available', () => {
    const project = mockProjects[0]
    render(<ProjectCard project={project} />)

    const image = screen.getByAltText(project.title) as HTMLImageElement
    expect(image.src).toContain(project.image_url)
  })

  it('renders metrics as chips', () => {
    const project = mockProjects[0]
    render(<ProjectCard project={project} />)

    const metrics = project.metrics as Record<string, string>
    Object.values(metrics).forEach(value => {
      expect(screen.getByText(value)).toBeInTheDocument()
    })
  })

  it('displays "Destacado" badge when featured prop is true', () => {
    const project = mockProjects[0]
    render(<ProjectCard project={project} featured={true} />)

    expect(screen.getByText('Destacado')).toBeInTheDocument()
  })

  it('hides the "Destacado" badge when featured prop is false', () => {
    const project = mockProjects[2]
    render(<ProjectCard project={project} featured={false} />)

    expect(screen.queryByText('Destacado')).not.toBeInTheDocument()
  })

  it('renders a "Ver caso" call to action', () => {
    const project = mockProjects[0]
    render(<ProjectCard project={project} />)

    expect(screen.getByText(/Ver caso/i)).toBeInTheDocument()
  })

  it('links to the project detail page', () => {
    const project = mockProjects[0]
    render(<ProjectCard project={project} />)

    const link = screen.getByText(project.title).closest('a')
    expect(link).toHaveAttribute('href', `/projects/${project.id}`)
  })

  it('tracks a click on the project card', async () => {
    const user = userEvent.setup()
    const project = mockProjects[0]
    render(<ProjectCard project={project} />)

    const card = screen.getByText(project.title).closest('a')!
    await user.click(card)

    expect(trackingApi.trackEvent).toHaveBeenCalledWith(expect.objectContaining({ target: `project-${project.id}` }))
  })

  it('applies a hover shadow effect on the card', () => {
    const project = mockProjects[0]
    const { container } = render(<ProjectCard project={project} />)

    expect(container.querySelector('.hover\\:shadow-lg')).toBeInTheDocument()
  })

  it('handles a project with no image gracefully', () => {
    const project = mockProjects[1]
    render(<ProjectCard project={project} />)

    expect(screen.queryByAltText(project.title)).not.toBeInTheDocument()
    expect(screen.getByText(project.title)).toBeInTheDocument()
  })

  it('handles a project with no metrics gracefully', () => {
    const project = mockProjects[1]
    render(<ProjectCard project={project} />)

    expect(screen.getByText(project.title)).toBeInTheDocument()
  })

  it('handles a project with no card_summary gracefully', () => {
    const project = { ...mockProjects[0], card_summary: null }
    render(<ProjectCard project={project} />)

    expect(screen.getByText(project.title)).toBeInTheDocument()
  })

  it('handles a project with no category or industry gracefully', () => {
    const project = { ...mockProjects[0], category: null, industry: null }
    render(<ProjectCard project={project} />)

    expect(screen.getByText(project.title)).toBeInTheDocument()
  })
})
