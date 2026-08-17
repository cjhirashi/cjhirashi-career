import { AxiosError } from 'axios'

export class ApiError extends Error {
  constructor(
    public statusCode: number,
    public message: string,
    public details?: any
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export class ValidationError extends Error {
  constructor(
    public errors: Record<string, string>,
    message: string = 'Validation failed'
  ) {
    super(message)
    this.name = 'ValidationError'
  }
}

export class NetworkError extends Error {
  constructor(message: string = 'Network error') {
    super(message)
    this.name = 'NetworkError'
  }
}

// Extract error message from AxiosError
export const getErrorMessage = (error: unknown): string => {
  if (error instanceof AxiosError) {
    if (error.response?.data?.detail) {
      return error.response.data.detail
    }
    if (error.response?.data?.message) {
      return error.response.data.message
    }
    if (error.response?.status === 401) {
      return 'Unauthorized. Please login again.'
    }
    if (error.response?.status === 403) {
      return 'You do not have permission to perform this action.'
    }
    if (error.response?.status === 404) {
      return 'Resource not found.'
    }
    if (error.response?.status === 422) {
      return 'Validation error. Please check your input.'
    }
    if ((error.response?.status ?? 0) >= 500) {
      return 'Server error. Please try again later.'
    }
  }

  if (error instanceof Error) {
    return error.message
  }

  return 'An unknown error occurred'
}

// Extract validation errors from AxiosError
export const getValidationErrors = (
  error: unknown
): Record<string, string> | null => {
  if (error instanceof AxiosError) {
    if (error.response?.data?.errors) {
      const errors: Record<string, string> = {}
      const rawErrors = error.response.data.errors

      if (Array.isArray(rawErrors)) {
        rawErrors.forEach((err: any) => {
          if (err.loc && err.msg) {
            const field = err.loc[1] || 'general'
            errors[field] = err.msg
          }
        })
      } else if (typeof rawErrors === 'object') {
        Object.assign(errors, rawErrors)
      }

      return Object.keys(errors).length > 0 ? errors : null
    }
  }

  return null
}

// Check if error is due to network
export const isNetworkError = (error: unknown): boolean => {
  if (error instanceof AxiosError) {
    return !error.response || error.message === 'Network Error'
  }
  return false
}

// Check if error is authorization-related
export const isAuthError = (error: unknown): boolean => {
  if (error instanceof AxiosError) {
    return error.response?.status === 401 || error.response?.status === 403
  }
  return false
}

// Check if error is validation-related
export const isValidationError = (error: unknown): boolean => {
  if (error instanceof AxiosError) {
    return error.response?.status === 422
  }
  return error instanceof ValidationError
}

// Log error for debugging
export const logError = (error: unknown, context: string = ''): void => {
  if (process.env.NODE_ENV === 'development') {
    console.error(`[${context}]`, error)
  }
}
