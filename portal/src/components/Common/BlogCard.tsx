import { BlogPost } from '@/types'
import { useTrackClick } from '@/hooks/useTracking'
import { format, parseISO } from 'date-fns'

interface BlogCardProps {
  post: BlogPost
}

export const BlogCard = ({ post }: BlogCardProps) => {
  const { trackClick } = useTrackClick()

  const handleClick = () => {
    trackClick(`blog-${post.slug}`)
  }

  const publishDate = post.publishedAt ? format(parseISO(post.publishedAt), 'MMM d, yyyy') : ''

  return (
    <article
      className="bg-surface-card border border-border rounded-lg overflow-hidden hover:shadow-lg transition-shadow p-4"
      onClick={handleClick}
    >
      {/* Image */}
      {post.image && (
        <div className="mb-4 h-40 bg-gradient-to-br from-cyan-100 to-slate-100 dark:from-slate-800 dark:to-slate-900 rounded-lg overflow-hidden">
          <img
            src={post.image}
            alt={post.title}
            className="w-full h-full object-cover hover:scale-105 transition-transform"
            loading="lazy"
          />
        </div>
      )}

      {/* Meta */}
      <div className="flex items-center justify-between text-xs text-text-secondary mb-3">
        <time dateTime={post.publishedAt}>{publishDate}</time>
        {post.readTime && <span>{post.readTime} min read</span>}
      </div>

      {/* Title */}
      <h3 className="font-bold text-lg text-text mb-2 line-clamp-2">{post.title}</h3>

      {/* Excerpt */}
      <p className="text-text-secondary text-sm mb-4 line-clamp-3">{post.excerpt}</p>

      {/* Tags */}
      {post.tags && post.tags.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {post.tags.slice(0, 3).map(tag => (
            <span
              key={tag}
              className="inline-block bg-primary-container text-primary text-xs px-2 py-1 rounded"
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* CTA */}
      <a
        href={`/blog/${post.slug}`}
        className="text-primary hover:opacity-80 font-medium text-sm inline-flex items-center"
      >
        Read More →
      </a>
    </article>
  )
}
