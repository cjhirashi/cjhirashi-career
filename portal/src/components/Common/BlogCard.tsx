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
      className="card group hover:shadow-lg overflow-hidden block"
      onClick={() => trackClick(`blog-${post.slug ?? post.id}`)}
    >
      {post.image_url && (
        <div className="relative h-40 bg-gradient-to-br from-cyan-100 to-slate-100 dark:from-slate-800 dark:to-slate-900 overflow-hidden">
          <img
            src={post.image_url}
            alt={post.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            loading="lazy"
          />
        </div>
      )}

      <div className="p-4">
        {post.content_type && <span className="badge mono mb-3">{post.content_type}</span>}

        <h3 className="font-bold text-lg text-text mb-2 line-clamp-2">{post.title}</h3>

        {post.excerpt && <p className="text-text-secondary text-sm mb-4 line-clamp-3">{post.excerpt}</p>}

        <div className="mono flex items-center gap-2 text-xs text-text-secondary">
          {publishDate && <time dateTime={post.published_at ?? undefined}>{publishDate}</time>}
          {post.reading_minutes && <span>· {post.reading_minutes} min de lectura</span>}
        </div>
      </div>
    </Link>
  )
}
