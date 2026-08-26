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
      expect(screen.getByText(/Pensamiento sistémico aplicado a arquitectura/i)).toBeInTheDocument()
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

  it('renders category filter buttons', async () => {
    vi.mocked(blogApi.getPosts).mockResolvedValue(mockBlogPosts)

    render(<BlogPage />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Todos' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: mockBlogPosts[0].content_type! })).toBeInTheDocument()
    })
  })

  it('filters posts by selected category', async () => {
    const user = userEvent.setup()
    vi.mocked(blogApi.getPosts).mockResolvedValue(mockBlogPosts)

    render(<BlogPage />)

    const categoryButton = await screen.findByRole('button', { name: 'Pensamiento Sistémico' })
    await user.click(categoryButton)

    await waitFor(() => {
      expect(screen.getByText('React Best Practices')).toBeInTheDocument()
      expect(screen.queryByText('Understanding System Design')).not.toBeInTheDocument()
    })
  })

  it('removes the category filter when clicked again', async () => {
    const user = userEvent.setup()
    vi.mocked(blogApi.getPosts).mockResolvedValue(mockBlogPosts)

    render(<BlogPage />)

    const categoryButton = await screen.findByRole('button', { name: 'Pensamiento Sistémico' })
    await user.click(categoryButton)
    await waitFor(() => expect(categoryButton).toHaveClass('filter-chip-active'))

    await user.click(categoryButton)
    await waitFor(() => expect(categoryButton).not.toHaveClass('filter-chip-active'))
  })

  it('tracks category filter clicks', async () => {
    const user = userEvent.setup()
    vi.mocked(blogApi.getPosts).mockResolvedValue(mockBlogPosts)

    render(<BlogPage />)

    const categoryButton = await screen.findByRole('button', { name: 'Pensamiento Sistémico' })
    await user.click(categoryButton)

    expect(trackingApi.trackEvent).toHaveBeenCalledWith(
      expect.objectContaining({ target: 'blog-category-Pensamiento Sistémico' })
    )
  })

  it('renders a sort toggle and switches label on click', async () => {
    const user = userEvent.setup()
    vi.mocked(blogApi.getPosts).mockResolvedValue(mockBlogPosts)

    render(<BlogPage />)

    const sortButton = await screen.findByText('Más antiguos')
    await user.click(sortButton)

    await waitFor(() => {
      expect(screen.getByText('Más recientes')).toBeInTheDocument()
    })
  })

  it('shows loading spinner initially', () => {
    vi.mocked(blogApi.getPosts).mockImplementation(() => new Promise(() => {}))

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

  it('shows a no-results message when there are no posts', async () => {
    vi.mocked(blogApi.getPosts).mockResolvedValue([])

    render(<BlogPage />)

    await waitFor(() => {
      expect(screen.getByText(/No se encontraron artículos/i)).toBeInTheDocument()
    })
  })

  it('renders posts in a grid layout', async () => {
    vi.mocked(blogApi.getPosts).mockResolvedValue(mockBlogPosts)

    const { container } = render(<BlogPage />)

    await waitFor(() => {
      const grid = container.querySelector('.grid')
      expect(grid).toHaveClass('grid-cols-1', 'md:grid-cols-2', 'lg:grid-cols-3')
    })
  })

  it('extracts unique categories from all posts', async () => {
    vi.mocked(blogApi.getPosts).mockResolvedValue(mockBlogPosts)

    render(<BlogPage />)

    await waitFor(() => {
      const categories = Array.from(new Set(mockBlogPosts.map(p => p.content_type)))
      categories.forEach(category => {
        expect(screen.getByRole('button', { name: category! })).toBeInTheDocument()
      })
    })
  })

  it('handles an empty blog posts array', async () => {
    vi.mocked(blogApi.getPosts).mockResolvedValue([])

    render(<BlogPage />)

    await waitFor(() => {
      expect(screen.getByText('Blog')).toBeInTheDocument()
    })
  })
})
