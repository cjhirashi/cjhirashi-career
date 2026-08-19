import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '../testUtils'
import userEvent from '@testing-library/user-event'
import { trackingApi } from '@/api/tracking'
import { BlogCard } from '@/components/Common/BlogCard'
import { mockBlogPosts } from '../fixtures/mockData'

vi.mock('@/api/tracking')

describe('BlogCard Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders blog post title', () => {
    const post = mockBlogPosts[0]
    render(<BlogCard post={post} />)

    expect(screen.getByText(post.title)).toBeInTheDocument()
  })

  it('renders blog post excerpt', () => {
    const post = mockBlogPosts[0]
    render(<BlogCard post={post} />)

    expect(screen.getByText(post.excerpt!)).toBeInTheDocument()
  })

  it('renders the published date formatted', () => {
    const post = mockBlogPosts[0]
    render(<BlogCard post={post} />)

    expect(screen.getByText('10 Aug 2024')).toBeInTheDocument()
  })

  it('renders reading time when available', () => {
    const post = mockBlogPosts[0]
    render(<BlogCard post={post} />)

    expect(screen.getByText(`${post.reading_minutes} min de lectura`)).toBeInTheDocument()
  })

  it('renders up to 3 tags', () => {
    const post = mockBlogPosts[0]
    render(<BlogCard post={post} />)

    post.tags.slice(0, 3).forEach(tag => {
      expect(screen.getByText(tag)).toBeInTheDocument()
    })
  })

  it('links to the post detail page by slug', () => {
    const post = mockBlogPosts[0]
    render(<BlogCard post={post} />)

    const link = screen.getByText(post.title).closest('a')
    expect(link).toHaveAttribute('href', `/blog/${post.slug}`)
  })

  it('falls back to the post id when slug is missing', () => {
    const post = { ...mockBlogPosts[0], slug: null }
    render(<BlogCard post={post} />)

    const link = screen.getByText(post.title).closest('a')
    expect(link).toHaveAttribute('href', `/blog/${post.id}`)
  })

  it('renders a "Leer más" call to action', () => {
    const post = mockBlogPosts[0]
    render(<BlogCard post={post} />)

    expect(screen.getByText(/Leer más/i)).toBeInTheDocument()
  })

  it('tracks a click on the card', async () => {
    const user = userEvent.setup()
    const post = mockBlogPosts[0]
    render(<BlogCard post={post} />)

    const card = screen.getByText(post.title).closest('a')!
    await user.click(card)

    expect(trackingApi.trackEvent).toHaveBeenCalledWith(expect.objectContaining({ target: `blog-${post.slug}` }))
  })

  it('applies a hover shadow effect', () => {
    const post = mockBlogPosts[0]
    const { container } = render(<BlogCard post={post} />)

    expect(container.querySelector('.hover\\:shadow-lg')).toBeInTheDocument()
  })

  it('applies line-clamp to the title', () => {
    const post = mockBlogPosts[0]
    render(<BlogCard post={post} />)

    expect(screen.getByText(post.title)).toHaveClass('line-clamp-2')
  })

  it('applies line-clamp to the excerpt', () => {
    const post = mockBlogPosts[0]
    render(<BlogCard post={post} />)

    expect(screen.getByText(post.excerpt!)).toHaveClass('line-clamp-3')
  })

  it('uses a time element for the published date', () => {
    const post = mockBlogPosts[0]
    const { container } = render(<BlogCard post={post} />)

    const timeElement = container.querySelector('time')
    expect(timeElement).toBeInTheDocument()
    expect(timeElement).toHaveAttribute('dateTime', post.published_at!)
  })

  it('handles a post with no tags gracefully', () => {
    const post = { ...mockBlogPosts[0], tags: [] }
    render(<BlogCard post={post} />)

    expect(screen.getByText(post.title)).toBeInTheDocument()
  })

  it('handles a post with no reading_minutes gracefully', () => {
    const post = { ...mockBlogPosts[0], reading_minutes: null }
    render(<BlogCard post={post} />)

    expect(screen.getByText(post.title)).toBeInTheDocument()
    expect(screen.queryByText(/min de lectura/i)).not.toBeInTheDocument()
  })

  it('handles a post with no excerpt gracefully', () => {
    const post = { ...mockBlogPosts[0], excerpt: null }
    render(<BlogCard post={post} />)

    expect(screen.getByText(post.title)).toBeInTheDocument()
  })
})
