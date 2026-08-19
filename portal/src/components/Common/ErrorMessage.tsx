interface ErrorMessageProps {
  message: string
  retry?: () => void
}

export const ErrorMessage = ({ message, retry }: ErrorMessageProps) => {
  return (
    <div
      role="alert"
      className="bg-error-bg backdrop-blur-lg border border-error-border rounded-md p-4 my-4"
    >
      <div className="flex items-start">
        <div className="flex-shrink-0">
          <svg
            className="h-5 w-5 text-error-text"
            viewBox="0 0 20 20"
            fill="currentColor"
            aria-hidden="true"
          >
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z"
              clipRule="evenodd"
            />
          </svg>
        </div>
        <div className="ml-3 flex-1">
          <p className="text-sm font-medium text-error-text">{message}</p>
          {retry && (
            <button
              onClick={retry}
              className="mt-2 inline-block text-sm font-medium text-error-text hover:opacity-80 underline"
            >
              Try again
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
