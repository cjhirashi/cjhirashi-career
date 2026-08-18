import React, { useState } from 'react'
import { useAuth } from '@/hooks/useAuth'

export const ChangePasswordPage: React.FC = () => {
  const { changePassword, isLoading, error, clearError } = useAuth()
  const [formData, setFormData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  })
  const [formErrors, setFormErrors] = useState<Record<string, string>>({})
  const [success, setSuccess] = useState(false)

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {}
    if (!formData.currentPassword) errors.currentPassword = 'Current password is required'
    if (!formData.newPassword) errors.newPassword = 'New password is required'
    else if (formData.newPassword.length < 8)
      errors.newPassword = 'New password must be at least 8 characters'
    if (formData.confirmPassword !== formData.newPassword)
      errors.confirmPassword = 'Passwords do not match'
    setFormErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    clearError()
    setSuccess(false)

    if (!validateForm()) return

    try {
      await changePassword(formData.currentPassword, formData.newPassword)
      setSuccess(true)
      setFormData({ currentPassword: '', newPassword: '', confirmPassword: '' })
    } catch {
      // Error is handled by useAuth hook
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
    if (formErrors[name]) {
      setFormErrors((prev) => ({ ...prev, [name]: '' }))
    }
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">Change Password</h1>
        <p className="text-slate-600 dark:text-slate-400 mt-2">Update your account password</p>
      </div>

      <div className="card max-w-md">
        <div className="card-body">
          {success && (
            <div className="mb-6 p-4 bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800/50 rounded-lg">
              <p className="text-green-800 dark:text-green-300 text-sm font-medium">Password changed successfully</p>
            </div>
          )}

          {error && (
            <div className="mb-6 p-4 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800/50 rounded-lg">
              <p className="text-red-800 dark:text-red-300 text-sm font-medium">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="form-group">
              <label htmlFor="currentPassword" className="form-label">
                Current Password
              </label>
              <input
                type="password"
                id="currentPassword"
                name="currentPassword"
                value={formData.currentPassword}
                onChange={handleInputChange}
                disabled={isLoading}
                className="input-field"
                placeholder="Enter your current password"
              />
              {formErrors.currentPassword && (
                <p className="text-red-500 dark:text-red-400 text-sm mt-1">{formErrors.currentPassword}</p>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="newPassword" className="form-label">
                New Password
              </label>
              <input
                type="password"
                id="newPassword"
                name="newPassword"
                value={formData.newPassword}
                onChange={handleInputChange}
                disabled={isLoading}
                className="input-field"
                placeholder="Enter your new password"
              />
              {formErrors.newPassword && (
                <p className="text-red-500 dark:text-red-400 text-sm mt-1">{formErrors.newPassword}</p>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="confirmPassword" className="form-label">
                Confirm New Password
              </label>
              <input
                type="password"
                id="confirmPassword"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleInputChange}
                disabled={isLoading}
                className="input-field"
                placeholder="Re-enter your new password"
              />
              {formErrors.confirmPassword && (
                <p className="text-red-500 dark:text-red-400 text-sm mt-1">{formErrors.confirmPassword}</p>
              )}
            </div>

            <button type="submit" disabled={isLoading} className="btn-primary w-full">
              {isLoading ? 'Updating...' : 'Update Password'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
