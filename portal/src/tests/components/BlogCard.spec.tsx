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

    expect(screen.getByText(post.excerpt)).toBeInTheDocument()
  })

  it('renders published date formatted correctly', () => {
    const post = mockBlogPosts[0]
    render(<BlogCard post={post} />)

    const dateText = screen.getByText('Aug 10, 2024')
    expect(dateText).toBeInTheDocument()
  })

  it('renders read time when available', () => {
    const post = mockBlogPosts[0]
    render(<BlogCard post={post} />)

    expect(screen.getByText(`${post.readTime} min read`)).toBeInTheDocument()
  })

  it('renders all tags up to 3', () => {
    const post = mockBlogPosts[0]
    render(<BlogCard post={post} />)

    post.tags.slice(0, 3).forEach(tag => {
      expect(screen.getByText(tag)).toBeInTheDocument()
    })
  })

  it('renders blog post image when available', () => {
    const post = mockBlogPosts[0]
    render(<BlogCard post={post} />)

    const image = screen.getByAltText(post.title) as HTMLImageElement
    expect(image).toBeInTheDocument()
    expect(image.src).toContain(post.image)
  })

  it('uses lazy loading for blog images', () => {
    const post = mockBlogPosts[0]
    render(<BlogCard post={post} />)

    const image = screen.getByAltText(post.title) as HTMLImageElement
    expect(image).toHaveAttribute('loading', 'lazy')
  })

  it('renders Read More link with correct href', () => {
    const post = mockBlogPosts[0]
    render(<BlogCard post={post} />)

    const readMoreLink = screen.getByRole('link', { name: /Read More/i })
    expect(readMoreLink).toHaveAttribute('href', `/blog/${post.slug}`)
  })

  it('tracks click when card is clicked', async () => {
    const user = userEvent.setup()
    const post = mockBlogPosts[0]
    render(<BlogCard post={post} />)

    const card = screen.getByText(post.title).closest('article')!
    await user.click(card)

    expect(trackingApi.trackEvent).toHaveBeenCalledWith(
      expect.objectContaining({
        target: `blog-${post.slug}`,
      })
    )
  })

  it('applies hover shadow effect', () => {
    const post = mockBlogPosts[0]
    const { container } = render(<BlogCard post={post} />)

    const card = container.querySelector('.hover\\:shadow-lg')
    expect(card).toBeInTheDocument()
  })

  it('renders card without image when image is not provided', () => {
    const post = {
      ...mockBlogPosts[0],
      image: undefined,
    }
    render(<BlogCard post={post} />)

    expect(screen.queryByAltText(post.title)).not.toBeInTheDocument()
    expect(screen.getByText(post.title)).toBeInTheDocument()
  })

  it('renders article element', () => {
    const post = mockBlogPosts[0]
    const { container } = render(<BlogCard post={post} />)

    const article = container.querySelector('article')
    expect(article).toBeInTheDocument()
  })

  it('applies line-clamp to title', () => {
    const post = mockBlogPosts[0]
    const { container } = render(<BlogCard post={post} />)

    const title = screen.getByText(post.title)
    expect(title).toHaveClass('line-clamp-2')
  })

  it('applies line-clamp to excerpt', () => {
    const post = mockBlogPosts[0]
    const { container } = render(<BlogCard post={post} />)

    const excerpt = screen.getByText(post.excerpt)
    expect(excerpt).toHaveClass('line-clamp-3')
  })

  it('uses time element for published date', () => {
    const post = mockBlogPosts[0]
    const { container } = render(<BlogCard post={post} />)

    const timeElement = container.querySelector('time')
    expect(timeElement).toBeInTheDocument()
    expect(timeElement).toHaveAttribute('dateTime', post.publishedAt)
  })

  it('handles post without tags gracefully', () => {
    const post = {
      ...mockBlogPosts[0],
      tags: [],
    }
    render(<BlogCard post={post} />)

    expect(screen.getByText(post.title)).toBeInTheDocument()
    expect(screen.queryByRole('generic', { name: /tags/i })).not.toBeInTheDocument()
  })

  it('handles post without readTime gracefully', () => {
    const post = {
      ...mockBlogPosts[0],
      readTime: undefined,
    }
    render(<BlogCard post={post} />)

    expect(screen.getByText(post.title)).toBeInTheDocument()
    expect(screen.queryByText(/min read/i)).not.toBeInTheDocument()
  })
})
