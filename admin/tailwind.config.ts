import type { Config } from 'tailwindcss'

export default {
  // Dark mode is toggled via a `data-theme="dark"` attribute on <html>,
  // set by src/stores/themeStore.ts (and pre-applied by an inline script in
  // index.html to avoid a flash of incorrect theme). This uses Tailwind's
  // "selector" darkMode strategy (available since Tailwind 3.4.1) instead of
  // the default `.dark` class strategy.
  darkMode: ['selector', '[data-theme="dark"]'],
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Semantic tokens backed by CSS variables (see src/index.css).
        // These automatically switch value when `data-theme` changes, so
        // components using them (e.g. `bg-surface-card`, `text-text`) don't
        // need explicit `dark:` variants. Values match the verified palette
        // from cjhirashi.com (light + dark).
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
        cyan: {
          50: '#ecf9fd',
          100: '#d4f1fa',
          200: '#b1e7f5',
          300: '#7ddbef',
          400: '#44cde5',
          500: '#22bfd4',
          600: '#16a3b8',
          700: '#168195',
          800: '#1a6a7b',
          900: '#1b5666',
          950: '#0d3946',
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
          950: '#020617',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
} satisfies Config
