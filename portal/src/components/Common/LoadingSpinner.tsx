export const LoadingSpinner = () => {
  return (
    <div className="flex items-center justify-center py-12">
      <div className="relative w-12 h-12">
        <div className="absolute inset-0 bg-gradient-to-r from-cyan-400 to-slate-400 dark:from-cyan-600 dark:to-slate-600 rounded-full animate-spin"></div>
        <div className="absolute inset-1 bg-surface-card rounded-full"></div>
      </div>
    </div>
  )
}
