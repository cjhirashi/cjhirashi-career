import type { Config } from 'tailwindcss'

export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      // Custom breakpoint matching cjhirashi.com's content layout breakpoint,
      // used where project/content grids collapse from multi-column to stacked.
      screens: {
        content: '860px',
      },
      colors: {
        cyan: {
          50: '#ecf8fb',
          100: '#d9f0f7',
          200: '#b3e1ef',
          300: '#8dd3e7',
          400: '#67c4df',
          500: '#41b5d7',
          600: '#2d9ab7',
          700: '#207f97',
          800: '#156477',
          900: '#0a4957',
        },
        slate: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
        },
        // Semantic tokens sourced from CSS custom properties (see src/index.css).
        // These automatically adapt to the active theme (light/dark) because
        // the underlying --variable values change on [data-theme="dark"].
        // "Glass Steel" tokens (primary source of truth):
        'bg-primary': 'var(--bg-primary)',
        'bg-secondary': 'var(--bg-secondary)',
        'bg-glass': 'var(--bg-glass)',
        'bg-card': 'var(--bg-card)',
        'text-muted': 'var(--text-muted)',
        'border-glass': 'var(--border-glass)',
        'border-glass-hover': 'var(--border-glass-hover)',
        'primary-hover': 'var(--primary-hover)',
        'primary-light': 'var(--primary-light)',
        'primary-glow': 'var(--primary-glow)',
        'secondary-hover': 'var(--secondary-hover)',
        'secondary-light': 'var(--secondary-light)',
        'error-bg': 'var(--error-bg)',
        'error-text': 'var(--error-text)',
        'error-border': 'var(--error-border)',
        'warning-bg': 'var(--warning-bg)',
        'warning-text': 'var(--warning-text)',
        'warning-border': 'var(--warning-border)',
        'success-bg': 'var(--success-bg)',
        'success-text': 'var(--success-text)',
        'success-border': 'var(--success-border)',
        // Legacy aliases (kept so existing className usage across the portal
        // keeps working, now backed by the Glass Steel custom properties):
        bg: 'var(--bg)',
        surface: 'var(--surface)',
        'surface-card': 'var(--surface-card)',
        border: 'var(--border)',
        text: 'var(--text)',
        'text-secondary': 'var(--text-secondary)',
        primary: 'var(--primary)',
        'on-primary': 'var(--on-primary)',
        'primary-container': 'var(--primary-container)',
        secondary: 'var(--secondary)',
        'secondary-container': 'var(--secondary-container)',
      },
      borderRadius: {
        sm: 'var(--radius-sm)',
        md: 'var(--radius-md)',
        lg: 'var(--radius-lg)',
      },
      boxShadow: {
        glass: 'var(--shadow-glass)',
        glow: 'var(--shadow-glow)',
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [],
} satisfies Config
