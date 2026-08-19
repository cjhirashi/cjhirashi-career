import { Link } from 'react-router-dom'
import { BlogPost } from '@/types'
import { useTrackClick } from '@/hooks/useTracking'
import { format, parseISO } from 'date-fns'

interface BlogCardProps {
  post: BlogPost
}

export const BlogCard = ({ post }: BlogCardProps) => {
  const { trackClick } = useTrackClick()

  const publishDate = post.published_at ? format(parseISO(post.published_at), 'd MMM yyyy') : ''

  return (
    <Link
      to={`/blog/${post.slug ?? post.id}`}
      className="card group hover:shadow-lg p-4 block"
      onClick={() => trackClick(`blog-${post.slug ?? post.id}`)}
    >
      {/* Meta */}
      <div className="mono flex items-center justify-between text-xs text-text-secondary mb-3">
        {publishDate && <time dateTime={post.published_at ?? undefined}>{publishDate}</time>}
        {post.reading_minutes && <span>{post.reading_minutes} min de lectura</span>}
      </div>

      <h3 className="font-bold text-lg text-text mb-2 line-clamp-2">{post.title}</h3>

      {post.excerpt && <p className="text-text-secondary text-sm mb-4 line-clamp-3">{post.excerpt}</p>}

      {post.tags.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {post.tags.slice(0, 3).map(tag => (
            <span key={tag} className="badge mono">
              {tag}
            </span>
          ))}
        </div>
      )}

      <span className="text-primary hover:[text-shadow:0_0_10px_var(--primary-glow)] font-medium text-sm inline-flex items-center">
        Leer más →
      </span>
    </Link>
  )
}
