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
    },
  },
  plugins: [],
} satisfies Config
