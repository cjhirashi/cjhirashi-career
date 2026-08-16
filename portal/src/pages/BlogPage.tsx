import { useState } from 'react'
import { useBlogPosts } from '@/hooks/useBlog'
import { BlogCard } from '@/components/Common/BlogCard'
import { LoadingSpinner } from '@/components/Common/LoadingSpinner'
import { ErrorMessage } from '@/components/Common/ErrorMessage'
import { useTrackClick } from '@/hooks/useTracking'

export const BlogPage = () => {
  const { data: posts, isLoading, error } = useBlogPosts()
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedTag, setSelectedTag] = useState<string | null>(null)
  const { trackClick } = useTrackClick()

  const handleSearch = (term: string) => {
    trackClick(`blog-search-${term}`)
    setSearchTerm(term)
  }

  const handleTagFilter = (tag: string) => {
    trackClick(`blog-tag-${tag}`)
    setSelectedTag(selectedTag === tag ? null : tag)
  }

  if (isLoading) return <LoadingSpinner />
  if (error) return <ErrorMessage message="Failed to load blog posts" />

  // Extract unique tags
  const allTags = Array.from(new Set(posts?.flatMap(p => p.tags) || []))

  // Filter posts
  let filteredPosts = posts || []

  if (searchTerm) {
    filteredPosts = filteredPosts.filter(
      p =>
        p.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.excerpt.toLowerCase().includes(searchTerm.toLowerCase())
    )
  }

  if (selectedTag) {
    filteredPosts = filteredPosts.filter(p => p.tags.includes(selectedTag))
  }

  return (
    <div className="min-h-screen py-16 px-4 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-4xl">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-4xl font-bold text-slate-900 mb-4">Blog</h1>
          <p className="text-lg text-slate-600">
            Technical articles, insights, and learnings from my professional journey.
          </p>
        </div>

        {/* Search */}
        <div className="mb-12">
          <div className="relative">
            <svg
              className="absolute left-3 top-3 w-5 h-5 text-slate-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
            <input
              type="text"
              placeholder="Search articles..."
              value={searchTerm}
              onChange={e => handleSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-600"
            />
          </div>
        </div>

        {/* Tags Filter */}
        {allTags.length > 0 && (
          <div className="mb-12">
            <h2 className="text-sm font-bold text-slate-700 uppercase tracking-wide mb-4">
              Filter by Tag
            </h2>
            <div className="flex flex-wrap gap-2">
              {allTags.map(tag => (
                <button
                  key={tag}
                  onClick={() => handleTagFilter(tag)}
                  className={`px-4 py-2 rounded-full text-sm font-medium transition ${
                    selectedTag === tag
                      ? 'bg-cyan-600 text-white'
                      : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                  }`}
                >
                  {tag}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Posts Grid */}
        {filteredPosts.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {filteredPosts.map(post => (
              <BlogCard key={post.id} post={post} />
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-slate-600 text-lg">No articles found.</p>
          </div>
        )}
      </div>
    </div>
  )
}
