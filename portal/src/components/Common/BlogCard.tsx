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
    <article className="card group hover:shadow-lg p-4" onClick={handleClick}>
      {/* Image */}
      {post.image && (
        <div className="relative mb-4 h-40 bg-gradient-to-br from-cyan-100 to-slate-100 dark:from-slate-800 dark:to-slate-900 rounded-md overflow-hidden">
          <img
            src={post.image}
            alt={post.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            loading="lazy"
          />
        </div>
      )}

      {/* Meta */}
      <div className="mono flex items-center justify-between text-xs text-text-secondary mb-3">
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
            <span key={tag} className="badge mono">
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* CTA */}
      <a
        href={`/blog/${post.slug}`}
        className="text-primary hover:[text-shadow:0_0_10px_var(--primary-glow)] font-medium text-sm inline-flex items-center"
      >
        Read More →
      </a>
    </article>
  )
}
