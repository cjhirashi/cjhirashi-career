import React from 'react'

interface LoadingSpinnerProps {
  fullScreen?: boolean
  message?: string
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  fullScreen = true,
  message = 'Loading...',
}) => {
  const spinnerContent = (
    <div className="flex flex-col items-center justify-center space-y-4">
      <div className="relative w-12 h-12">
        <div className="absolute inset-0 border-4 border-slate-200 rounded-full"></div>
        <div className="absolute inset-0 border-4 border-transparent border-t-cyan-600 rounded-full animate-spin"></div>
      </div>
      {message && <p className="text-slate-600">{message}</p>}
    </div>
  )

  if (fullScreen) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-50">
        {spinnerContent}
      </div>
    )
  }

  return <div className="flex items-center justify-center py-8">{spinnerContent}</div>
}
