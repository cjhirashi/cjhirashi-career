export const LoadingSpinner = () => {
  return (
    <div className="flex items-center justify-center py-12" role="status" aria-label="Loading">
      <div className="relative w-12 h-12">
        <div className="absolute inset-0 bg-gradient-to-r from-primary to-secondary shadow-glow rounded-full animate-spin"></div>
        <div className="absolute inset-1 bg-bg-card backdrop-blur-lg rounded-full"></div>
      </div>
      <span className="sr-only">Loading...</span>
    </div>
  )
}
