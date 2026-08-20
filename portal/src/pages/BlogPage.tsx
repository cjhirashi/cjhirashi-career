import { useState } from 'react'
import { useBlogPosts } from '@/hooks/useBlog'
import { BlogCard } from '@/components/Common/BlogCard'
import { LoadingSpinner } from '@/components/Common/LoadingSpinner'
import { ErrorMessage } from '@/components/Common/ErrorMessage'
import { useTrackClick } from '@/hooks/useTracking'

export const BlogPage = () => {
  const { data: posts, isLoading, error } = useBlogPosts()
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [sortOldest, setSortOldest] = useState(false)
  const { trackClick } = useTrackClick()

  const handleCategoryFilter = (category: string) => {
    trackClick(`blog-category-${category}`)
    setSelectedCategory(selectedCategory === category ? null : category)
  }

  if (isLoading) return <LoadingSpinner />
  if (error) return <ErrorMessage message="No se pudieron cargar los artículos del blog" />

  const categories = Array.from(new Set((posts ?? []).map(p => p.content_type).filter((v): v is string => !!v)))

  let filteredPosts = posts ?? []
  if (selectedCategory) {
    filteredPosts = filteredPosts.filter(p => p.content_type === selectedCategory)
  }
  filteredPosts = [...filteredPosts].sort((a, b) => {
    const aTime = a.published_at ? new Date(a.published_at).getTime() : 0
    const bTime = b.published_at ? new Date(b.published_at).getTime() : 0
    return sortOldest ? aTime - bTime : bTime - aTime
  })

  return (
    <div className="min-h-screen py-16 px-4 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-6xl">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-4xl font-bold text-text mb-4">Blog</h1>
          <p className="text-lg text-text-secondary">
            Pensamiento sistémico aplicado a arquitectura de datos, IA y sistemas críticos.
          </p>
        </div>

        {/* Filters */}
        <div className="mb-12 flex flex-wrap items-center justify-between gap-4">
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => {
                trackClick('blog-category-all')
                setSelectedCategory(null)
              }}
              className={`mono px-4 py-2 rounded-full text-sm font-medium transition ${
                selectedCategory === null
                  ? 'filter-chip-active'
                  : 'filter-chip'
              }`}
            >
              Todos
            </button>
            {categories.map(category => (
              <button
                key={category}
                onClick={() => handleCategoryFilter(category)}
                className={`mono px-4 py-2 rounded-full text-sm font-medium transition ${
                  selectedCategory === category
                    ? 'filter-chip-active'
                    : 'filter-chip'
                }`}
              >
                {category}
              </button>
            ))}
          </div>

          <button
            onClick={() => {
              trackClick(`blog-sort-${sortOldest ? 'recent' : 'oldest'}`)
              setSortOldest(!sortOldest)
            }}
            className="text-sm text-text-secondary hover:text-primary font-medium"
          >
            {sortOldest ? 'Más recientes' : 'Más antiguos'}
          </button>
        </div>

        {/* Posts Grid */}
        {filteredPosts.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredPosts.map(post => (
              <BlogCard key={post.id} post={post} />
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-text-secondary text-lg">No se encontraron artículos.</p>
          </div>
        )}
      </div>
    </div>
  )
}
