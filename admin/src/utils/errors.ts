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

/** Same as `getErrorMessage`, but for requests made with `responseType:
 * 'blob'` (file/PDF downloads): on error, axios still hands back the body
 * as a `Blob` instead of parsed JSON (it doesn't know the *error* response
 * isn't the binary payload the success path expects), so
 * `error.response.data.detail` is always undefined there and callers would
 * otherwise only ever see the generic per-status-code fallback. Reads that
 * Blob as text and, if it parses as JSON with a `detail`, surfaces the same
 * backend message the non-blob API calls already show. */
export const getBlobErrorMessage = async (error: unknown): Promise<string> => {
  if (error instanceof AxiosError && error.response?.data instanceof Blob) {
    const blob = error.response.data as Blob
    if (blob.type.includes('json') || blob.type === '' || blob.type.includes('text')) {
      try {
        const text = await blob.text()
        const parsed = JSON.parse(text)
        if (typeof parsed?.detail === 'string') return parsed.detail
        if (typeof parsed?.message === 'string') return parsed.message
      } catch {
        // Body wasn't valid JSON (or wasn't text at all) - fall through to
        // the normal status-code-based fallback below.
      }
    }
  }
  return getErrorMessage(error)
}

/** Returns true when a Blob looks like a PDF (%PDF header). */
export const isPdfBlob = async (blob: Blob): Promise<boolean> => {
  const header = await blob.slice(0, 5).text()
  return header.startsWith('%PDF')
}

/** Rejects HTML/JSON error pages that axios may treat as successful blob responses. */
export const assertPdfBlob = async (blob: Blob): Promise<void> => {
  if (await isPdfBlob(blob)) return
  const text = (await blob.text()).trim()
  if (text.startsWith('{')) {
    try {
      const parsed = JSON.parse(text) as { detail?: string }
      if (parsed.detail) throw new Error(parsed.detail)
    } catch (err) {
      if (!(err instanceof SyntaxError)) throw err
    }
  }
  throw new Error(
    'La vista previa no devolvió un PDF válido. El servicio de generación puede estar caído o sobrecargado.'
  )
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
