import { Link, useParams } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { format, parseISO } from 'date-fns'
import { useBlogPostBySlug } from '@/hooks/useBlog'
import { LoadingSpinner } from '@/components/Common/LoadingSpinner'
import { ErrorMessage } from '@/components/Common/ErrorMessage'

export const BlogPostPage = () => {
  const { slug } = useParams<{ slug: string }>()
  const { data: post, isLoading, error } = useBlogPostBySlug(slug ?? '')

  if (isLoading) return <LoadingSpinner />
  if (error || !post) return <ErrorMessage message="No se encontró este artículo" />

  const publishDate = post.published_at ? format(parseISO(post.published_at), "d 'de' MMMM, yyyy") : ''

  return (
    <div className="min-h-screen py-16 px-4 sm:px-6 lg:px-8">
      <article className="mx-auto max-w-3xl">
        <Link to="/blog" className="text-primary text-sm font-medium mb-6 inline-block">
          ← Volver al Blog
        </Link>

        <div className="mono flex items-center gap-3 text-xs text-text-secondary mb-3">
          {publishDate && <time dateTime={post.published_at ?? undefined}>{publishDate}</time>}
          {post.reading_minutes && <span>· {post.reading_minutes} min de lectura</span>}
          {post.platform && <span>· {post.platform}</span>}
        </div>

        <h1 className="text-3xl sm:text-4xl font-bold text-text mb-6">{post.title}</h1>

        {post.tags.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-8">
            {post.tags.map(tag => (
              <span key={tag} className="badge mono">
                {tag}
              </span>
            ))}
          </div>
        )}

        {post.body_content ? (
          <div className="markdown-content">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{post.body_content}</ReactMarkdown>
          </div>
        ) : (
          post.excerpt && <p className="text-text-secondary text-lg">{post.excerpt}</p>
        )}

        {post.publication_url && (
          <a
            href={post.publication_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary hover:[text-shadow:0_0_10px_var(--primary-glow)] font-medium text-sm inline-block mt-8"
          >
            Ver publicación original →
          </a>
        )}
      </article>
    </div>
  )
}
