import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '../testUtils'
import userEvent from '@testing-library/user-event'
import { blogApi } from '@/api/blog'
import { trackingApi } from '@/api/tracking'
import { BlogPage } from '@/pages/BlogPage'
import { mockBlogPosts } from '../fixtures/mockData'

vi.mock('@/api/blog')
vi.mock('@/api/tracking')

describe('BlogPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders page heading', async () => {
    vi.mocked(blogApi.getPosts).mockResolvedValue(mockBlogPosts)

    render(<BlogPage />)

    await waitFor(() => {
      expect(screen.getByText('Blog')).toBeInTheDocument()
    })
  })

  it('renders page description', async () => {
    vi.mocked(blogApi.getPosts).mockResolvedValue(mockBlogPosts)

    render(<BlogPage />)

    await waitFor(() => {
      expect(screen.getByText(/Artículos técnicos, ideas/i)).toBeInTheDocument()
    })
  })

  it('renders all blog posts', async () => {
    vi.mocked(blogApi.getPosts).mockResolvedValue(mockBlogPosts)

    render(<BlogPage />)

    await waitFor(() => {
      mockBlogPosts.forEach(post => {
        expect(screen.getByText(post.title)).toBeInTheDocument()
      })
    })
  })

  it('renders search input field', async () => {
    vi.mocked(blogApi.getPosts).mockResolvedValue(mockBlogPosts)

    render(<BlogPage />)

    await waitFor(() => {
      const searchInput = screen.getByPlaceholderText(/Buscar artículos/i)
      expect(searchInput).toBeInTheDocument()
    })
  })

  it('filters blog posts by search term', async () => {
    const user = userEvent.setup()
    vi.mocked(blogApi.getPosts).mockResolvedValue(mockBlogPosts)

    render(<BlogPage />)

    await waitFor(() => {
      expect(screen.getByText(mockBlogPosts[0].title)).toBeInTheDocument()
    })

    const searchInput = screen.getByPlaceholderText(/Buscar artículos/i)
    await user.type(searchInput, 'System')

    await waitFor(() => {
      expect(screen.getByText(/Understanding System Design/)).toBeInTheDocument()
    })
  })

  it('searches by post title', async () => {
    const user = userEvent.setup()
    vi.mocked(blogApi.getPosts).mockResolvedValue(mockBlogPosts)

    render(<BlogPage />)

    await waitFor(() => {
      expect(screen.getByText(mockBlogPosts[0].title)).toBeInTheDocument()
    })

    const searchInput = screen.getByPlaceholderText(/Buscar artículos/i)
    await user.clear(searchInput)
    await user.type(searchInput, 'React')

    await waitFor(() => {
      expect(screen.getByText(/React Best Practices/)).toBeInTheDocument()
    })
  })

  it('searches by post excerpt', async () => {
    const user = userEvent.setup()
    vi.mocked(blogApi.getPosts).mockResolvedValue(mockBlogPosts)

    render(<BlogPage />)

    await waitFor(() => {
      expect(screen.getByText(mockBlogPosts[0].title)).toBeInTheDocument()
    })

    const searchInput = screen.getByPlaceholderText(/Buscar artículos/i)
    await user.clear(searchInput)
    await user.type(searchInput, 'Essential')

    await waitFor(() => {
      expect(screen.getByText(/React Best Practices/)).toBeInTheDocument()
    })
  })

  it('tracks search queries', async () => {
    const user = userEvent.setup()
    vi.mocked(blogApi.getPosts).mockResolvedValue(mockBlogPosts)

    render(<BlogPage />)

    await waitFor(() => {
      expect(screen.getByText(mockBlogPosts[0].title)).toBeInTheDocument()
    })

    const searchInput = screen.getByPlaceholderText(/Buscar artículos/i)
    await user.type(searchInput, 'React')

    expect(trackingApi.trackEvent).toHaveBeenCalledWith(
      expect.objectContaining({
        target: 'blog-search-React',
      })
    )
  })

  it('renders tag filter buttons', async () => {
    vi.mocked(blogApi.getPosts).mockResolvedValue(mockBlogPosts)

    render(<BlogPage />)

    await waitFor(() => {
      expect(screen.getByText('Filtrar por etiqueta')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Architecture' })).toBeInTheDocument()
    })
  })

  it('filters posts by selected tag', async () => {
    const user = userEvent.setup()
    vi.mocked(blogApi.getPosts).mockResolvedValue(mockBlogPosts)

    render(<BlogPage />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Architecture' })).toBeInTheDocument()
    })

    const archTag = screen.getByRole('button', { name: 'Architecture' })
    await user.click(archTag)

    await waitFor(() => {
      expect(screen.getByText(/Understanding System Design/)).toBeInTheDocument()
    })
  })

  it('removes tag filter when same tag is clicked again', async () => {
    const user = userEvent.setup()
    vi.mocked(blogApi.getPosts).mockResolvedValue(mockBlogPosts)

    render(<BlogPage />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'React' })).toBeInTheDocument()
    })

    const reactTag = screen.getByRole('button', { name: 'React' })
    await user.click(reactTag)

    await waitFor(() => {
      expect(reactTag).toHaveClass('bg-cyan-600')
    })

    await user.click(reactTag)

    await waitFor(() => {
      expect(reactTag).not.toHaveClass('bg-cyan-600')
    })
  })

  it('tracks tag filter clicks', async () => {
    const user = userEvent.setup()
    vi.mocked(blogApi.getPosts).mockResolvedValue(mockBlogPosts)

    render(<BlogPage />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'React' })).toBeInTheDocument()
    })

    const reactTag = screen.getByRole('button', { name: 'React' })
    await user.click(reactTag)

    expect(trackingApi.trackEvent).toHaveBeenCalledWith(
      expect.objectContaining({
        target: 'blog-tag-React',
      })
    )
  })

  it('combines search and tag filters', async () => {
    const user = userEvent.setup()
    vi.mocked(blogApi.getPosts).mockResolvedValue(mockBlogPosts)

    render(<BlogPage />)

    await waitFor(() => {
      expect(screen.getByText(mockBlogPosts[0].title)).toBeInTheDocument()
    })

    // Search for React
    const searchInput = screen.getByPlaceholderText(/Buscar artículos/i)
    await user.type(searchInput, 'React')

    // Filter by Frontend tag
    const frontendTag = screen.getByRole('button', { name: 'Frontend' })
    await user.click(frontendTag)

    await waitFor(() => {
      expect(screen.getByText(/React Best Practices/)).toBeInTheDocument()
    })
  })

  it('shows loading spinner initially', () => {
    vi.mocked(blogApi.getPosts).mockImplementation(
      () => new Promise(() => {})
    )

    render(<BlogPage />)

    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('shows error message when posts fail to load', async () => {
    vi.mocked(blogApi.getPosts).mockRejectedValue(new Error('Failed'))

    render(<BlogPage />)

    await waitFor(() => {
      expect(screen.getByText(/No se pudieron cargar los artículos del blog/i)).toBeInTheDocument()
    })
  })

  it('shows no articles message when no results', async () => {
    const user = userEvent.setup()
    vi.mocked(blogApi.getPosts).mockResolvedValue(mockBlogPosts)

    render(<BlogPage />)

    await waitFor(() => {
      expect(screen.getByText(mockBlogPosts[0].title)).toBeInTheDocument()
    })

    const searchInput = screen.getByPlaceholderText(/Buscar artículos/i)
    await user.type(searchInput, 'NonexistentTerm123')

    await waitFor(() => {
      expect(screen.getByText(/No se encontraron artículos/i)).toBeInTheDocument()
    })
  })

  it('renders posts in grid layout', async () => {
    vi.mocked(blogApi.getPosts).mockResolvedValue(mockBlogPosts)

    const { container } = render(<BlogPage />)

    await waitFor(() => {
      const grid = container.querySelector('.grid')
      expect(grid).toBeInTheDocument()
      expect(grid).toHaveClass('grid-cols-1', 'md:grid-cols-2')
    })
  })

  it('extracts unique tags from all posts', async () => {
    vi.mocked(blogApi.getPosts).mockResolvedValue(mockBlogPosts)

    render(<BlogPage />)

    await waitFor(() => {
      const uniqueTags = Array.from(new Set(mockBlogPosts.flatMap(p => p.tags)))
      uniqueTags.forEach(tag => {
        expect(screen.getByRole('button', { name: tag })).toBeInTheDocument()
      })
    })
  })

  it('handles empty blog posts array', async () => {
    vi.mocked(blogApi.getPosts).mockResolvedValue([])

    render(<BlogPage />)

    await waitFor(() => {
      expect(screen.getByText(/Blog/)).toBeInTheDocument()
    })
  })

  it('maintains search state when typing', async () => {
    const user = userEvent.setup()
    vi.mocked(blogApi.getPosts).mockResolvedValue(mockBlogPosts)

    render(<BlogPage />)

    await waitFor(() => {
      expect(screen.getByText(mockBlogPosts[0].title)).toBeInTheDocument()
    })

    const searchInput = screen.getByPlaceholderText(/Buscar artículos/i) as HTMLInputElement
    await user.type(searchInput, 'React')

    expect(searchInput.value).toBe('React')
  })
})
