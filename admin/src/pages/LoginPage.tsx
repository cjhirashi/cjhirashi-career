import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { UserCircle } from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'

export const LoginPage: React.FC = () => {
  const navigate = useNavigate()
  const { login, isLoading, error, clearError } = useAuth()
  const [formData, setFormData] = useState({ username: '', password: '' })
  const [formErrors, setFormErrors] = useState<{ username?: string; password?: string }>({})

  const validateForm = (): boolean => {
    const errors: typeof formErrors = {}
    if (!formData.username) errors.username = 'Username is required'
    if (!formData.password) errors.password = 'Password is required'
    setFormErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    clearError()

    if (!validateForm()) return

    try {
      await login(formData.username, formData.password)
      navigate('/dashboard')
    } catch {
      // Error is handled by useAuth hook
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
    if (formErrors[name as keyof typeof formErrors]) {
      setFormErrors((prev) => ({ ...prev, [name]: undefined }))
    }
  }

  return (
    // Transparent so the body's Glass Steel ambient gradient (see
    // src/index.css) shows through behind this floating glass card.
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-cyan-600 rounded-full flex items-center justify-center mx-auto mb-4 shadow-glow">
            <UserCircle size={28} className="text-white" aria-hidden="true" />
          </div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">Admin Panel</h1>
          <p className="text-slate-600 dark:text-slate-400 mt-2">Career Management Portal</p>
        </div>

        {/* Login Card */}
        <div className="card p-6 sm:p-8">
          {/* Error Message */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800/50 rounded-lg">
              <p className="text-red-800 dark:text-red-300 text-sm font-medium">{error}</p>
            </div>
          )}

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Username Input */}
            <div>
              <label htmlFor="username" className="form-label">
                Username
              </label>
              <input
                type="text"
                id="username"
                name="username"
                value={formData.username}
                onChange={handleInputChange}
                disabled={isLoading}
                className="input-field"
                placeholder="Enter your username"
              />
              {formErrors.username && (
                <p className="text-red-500 dark:text-red-400 text-sm mt-1">{formErrors.username}</p>
              )}
            </div>

            {/* Password Input */}
            <div>
              <label htmlFor="password" className="form-label">
                Password
              </label>
              <input
                type="password"
                id="password"
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                disabled={isLoading}
                className="input-field"
                placeholder="Enter your password"
              />
              {formErrors.password && (
                <p className="text-red-500 dark:text-red-400 text-sm mt-1">{formErrors.password}</p>
              )}
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary w-full"
            >
              {isLoading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
