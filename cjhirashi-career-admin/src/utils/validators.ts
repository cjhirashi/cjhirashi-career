// Email validation
export const isValidEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

// Username validation (alphanumeric, underscore, 3-20 characters)
export const isValidUsername = (username: string): boolean => {
  const usernameRegex = /^[a-zA-Z0-9_]{3,20}$/
  return usernameRegex.test(username)
}

// Password validation (at least 8 characters, 1 uppercase, 1 digit)
export const isValidPassword = (password: string): boolean => {
  const passwordRegex = /^(?=.*[A-Z])(?=.*\d).{8,}$/
  return passwordRegex.test(password)
}

// URL validation
export const isValidUrl = (url: string): boolean => {
  try {
    new URL(url)
    return true
  } catch {
    return false
  }
}

// Phone number validation (basic format)
export const isValidPhone = (phone: string): boolean => {
  const phoneRegex = /^[+]?[(]?[0-9]{3}[)]?[-\s.]?[0-9]{3}[-\s.]?[0-9]{4,6}$/
  return phoneRegex.test(phone.replace(/\s/g, ''))
}

// LinkedIn URL validation
export const isValidLinkedInUrl = (url: string): boolean => {
  if (!url) return true // Optional field
  return url.includes('linkedin.com')
}

// Check if string is not empty after trimming
export const isNotEmpty = (value: string): boolean => {
  return value.trim().length > 0
}

// Check if string length is within range
export const isLengthInRange = (value: string, min: number, max: number): boolean => {
  return value.length >= min && value.length <= max
}

// Validation error messages
export const VALIDATION_ERRORS = {
  REQUIRED: 'This field is required',
  INVALID_EMAIL: 'Please enter a valid email address',
  INVALID_USERNAME: 'Username must be 3-20 alphanumeric characters or underscore',
  INVALID_PASSWORD:
    'Password must be at least 8 characters with at least 1 uppercase letter and 1 digit',
  INVALID_URL: 'Please enter a valid URL',
  INVALID_PHONE: 'Please enter a valid phone number',
  INVALID_LINKEDIN: 'Please enter a valid LinkedIn URL',
  TOO_SHORT: (min: number) => `Must be at least ${min} characters`,
  TOO_LONG: (max: number) => `Must be no more than ${max} characters`,
  PASSWORDS_DONT_MATCH: 'Passwords do not match',
  ALREADY_EXISTS: 'This item already exists',
} as const

// Form validation helper
export interface ValidationResult {
  isValid: boolean
  errors: Record<string, string>
}

export const validateFormData = (
  data: Record<string, any>,
  rules: Record<string, (value: any) => string | undefined>
): ValidationResult => {
  const errors: Record<string, string> = {}

  Object.entries(rules).forEach(([field, validator]) => {
    const error = validator(data[field])
    if (error) {
      errors[field] = error
    }
  })

  return {
    isValid: Object.keys(errors).length === 0,
    errors,
  }
}
