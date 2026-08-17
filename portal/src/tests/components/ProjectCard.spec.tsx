import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '../testUtils'
import userEvent from '@testing-library/user-event'
import * as trackingApi from '@/api/tracking'
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

  it('renders project thumbnail image', () => {
    const project = mockProjects[0]
    render(<ProjectCard project={project} />)

    const image = screen.getByAltText(project.title) as HTMLImageElement
    expect(image).toBeInTheDocument()
    expect(image.src).toContain(project.thumbnail)
  })

  it('renders short description or full description', () => {
    const project = mockProjects[0]
    render(<ProjectCard project={project} />)

    expect(screen.getByText(project.shortDescription!)).toBeInTheDocument()
  })

  it('displays featured badge when featured prop is true', () => {
    const project = mockProjects[0]
    render(<ProjectCard project={project} featured={true} />)

    expect(screen.getByText(/Featured/)).toBeInTheDocument()
  })

  it('hides featured badge when featured prop is false', () => {
    const project = mockProjects[2]
    render(<ProjectCard project={project} featured={false} />)

    expect(screen.queryByText(/Featured/)).not.toBeInTheDocument()
  })

  it('renders technologies as tags', () => {
    const project = mockProjects[0]
    render(<ProjectCard project={project} />)

    project.technologies.slice(0, 3).forEach(tech => {
      expect(screen.getByText(tech)).toBeInTheDocument()
    })
  })

  it('shows more technologies indicator when more than 3 technologies', () => {
    const project = mockProjects[0]
    render(<ProjectCard project={project} />)

    if (project.technologies.length > 3) {
      expect(screen.getByText(`+${project.technologies.length - 3}`)).toBeInTheDocument()
    }
  })

  it('renders View Project link when link is provided', () => {
    const project = mockProjects[0]
    render(<ProjectCard project={project} />)

    const viewLink = screen.getByRole('link', { name: /View Project/i })
    expect(viewLink).toBeInTheDocument()
    expect(viewLink).toHaveAttribute('href', project.link)
    expect(viewLink).toHaveAttribute('target', '_blank')
  })

  it('renders GitHub link when github is provided', () => {
    const project = mockProjects[0]
    render(<ProjectCard project={project} />)

    const githubLink = screen.getByRole('link', { name: /GitHub/i })
    expect(githubLink).toBeInTheDocument()
    expect(githubLink).toHaveAttribute('href', project.github)
    expect(githubLink).toHaveAttribute('target', '_blank')
  })

  it('does not render View Project link when link is not provided', () => {
    const project = {
      ...mockProjects[0],
      link: undefined,
    }
    render(<ProjectCard project={project} />)

    expect(screen.queryByRole('link', { name: /View Project/i })).not.toBeInTheDocument()
  })

  it('does not render GitHub link when github is not provided', () => {
    const project = {
      ...mockProjects[0],
      github: undefined,
    }
    render(<ProjectCard project={project} />)

    expect(screen.queryByRole('link', { name: /GitHub/i })).not.toBeInTheDocument()
  })

  it('tracks click on project card', async () => {
    const user = userEvent.setup()
    const project = mockProjects[0]
    render(<ProjectCard project={project} />)

    const card = screen.getByText(project.title).closest('div')!
    await user.click(card)

    expect(trackingApi.trackEvent).toHaveBeenCalledWith(
      expect.objectContaining({
        target: `project-${project.id}`,
      })
    )
  })

  it('tracks click when viewing project', async () => {
    const user = userEvent.setup()
    const project = mockProjects[0]
    render(<ProjectCard project={project} />)

    const viewLink = screen.getByRole('link', { name: /View Project/i })
    await user.click(viewLink)

    expect(trackingApi.trackEvent).toHaveBeenCalledWith(
      expect.objectContaining({
        target: `project-view-${project.id}`,
      })
    )
  })

  it('applies hover shadow effect on card', () => {
    const project = mockProjects[0]
    const { container } = render(<ProjectCard project={project} />)

    const card = container.querySelector('.hover\\:shadow-lg')
    expect(card).toBeInTheDocument()
  })

  it('uses lazy loading for images', () => {
    const project = mockProjects[0]
    render(<ProjectCard project={project} />)

    const image = screen.getByAltText(project.title) as HTMLImageElement
    expect(image).toHaveAttribute('loading', 'lazy')
  })

  it('renders card without thumbnail when thumbnail is not provided', () => {
    const project = {
      ...mockProjects[0],
      thumbnail: undefined,
    }
    render(<ProjectCard project={project} />)

    expect(screen.queryByAltText(project.title)).not.toBeInTheDocument()
    expect(screen.getByText(project.title)).toBeInTheDocument()
  })
})
