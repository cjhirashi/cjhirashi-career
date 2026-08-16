# Admin Panel Setup Guide

## Overview

The Admin Panel is a modern React SPA (Single Page Application) for managing professional identity, competencies, evidence, job strategies, networking, and interview preparation.

**Location**: `/admin/`
**Port (Host)**: 8002
**Port (Internal)**: 8000
**Framework**: React 18 + TypeScript + Vite

## Prerequisites

- Node.js 18+ and npm/yarn
- API REST running on port 8001
- Docker (for containerization)

## Local Development

### 1. Install Dependencies

```bash
cd admin
npm install
```

### 2. Create Environment File

```bash
cp .env.example .env.local
```

### 3. Configure API URL

Edit `.env.local`:

```env
VITE_API_BASE_URL=http://api:8001/api/v1
```

### 4. Start Development Server

```bash
npm run dev
```

Access at: `http://localhost:8000`

## Development Commands

### Run Development Server

```bash
npm run dev
```

Starts Vite dev server with hot reload.

### Run Tests

```bash
npm test
```

Run all tests with Vitest.

### Run Tests with UI

```bash
npm run test:ui
```

Interactive test UI for debugging.

### Generate Coverage Report

```bash
npm run test:coverage
```

Generates HTML coverage report in `coverage/` directory.

### Type Checking

```bash
npm run type-check
```

Check TypeScript compilation errors.

### Linting

```bash
npm run lint
npm run lint:fix
```

ESLint validation and auto-fix.

### Code Formatting

```bash
npm run format
```

Format code with Prettier.

### Build for Production

```bash
npm run build
```

Creates optimized build in `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

Serves built application locally.

## Docker Deployment

### Build Docker Image

```bash
docker build -t admin-panel:latest .
```

### Run Docker Container

```bash
docker run -p 8002:8000 \
  -e VITE_API_BASE_URL=http://api:8001/api/v1 \
  admin-panel:latest
```

### Using Docker Compose

In project root:

```yaml
admin:
  build: ./admin
  container_name: admin_panel
  ports:
    - "8002:8000"
  environment:
    - VITE_API_BASE_URL=http://api:8001/api/v1
  networks:
    - network-cjhirashi-srv
  depends_on:
    - api
```

Run with: `docker-compose up admin`

## Project Structure

```
admin/
├── src/
│   ├── components/          # Reusable components
│   ├── pages/              # Page components
│   ├── hooks/              # Custom React hooks
│   ├── stores/             # Zustand state management
│   ├── api/                # API client
│   ├── types/              # TypeScript interfaces
│   ├── utils/              # Utility functions
│   ├── tests/              # Test files
│   ├── App.tsx             # Root component
│   ├── main.tsx            # Entry point
│   └── index.css           # Global styles
├── public/                 # Static assets
├── index.html              # HTML template
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.ts
├── vitest.config.ts
├── Dockerfile
└── README.md
```

## Authentication

### Login Flow

1. User enters username/password on LoginPage
2. Credentials sent to `POST /auth/login`
3. API returns JWT tokens and user data
4. Tokens stored in Zustand + localStorage
5. User redirected to Dashboard
6. PrivateRoute guards protect authenticated pages

### Token Refresh

- Automatic token refresh 15 minutes before expiry
- Axios interceptor handles expired tokens
- Failed refresh redirects to login

### Logout

- API call to `POST /auth/logout`
- Tokens deleted from state and localStorage
- User redirected to login

## Pages

### 1. Login (`/login`)
- Email/password form
- Error handling
- No layout (full page)

### 2. Dashboard (`/dashboard`)
- Overview cards with stats
- Getting started guide
- Quick links to modules

### 3. Identity (`/identity`)
- IKIGAI editor (4 quadrants)
- Differentiators (3-5 key points)
- Professional narrative
- Value proposition

### 4. Competencies (`/competencies`)
- Skills by category (technical, transferable, business)
- Proficiency levels
- Verification status
- Add/edit/delete functionality

### 5. Evidence (`/evidence`)
- Projects (with tech stack)
- Positions (with achievements)
- Achievements (awards, certifications)
- STAR cases (Situation, Task, Action, Result)

### 6. Job Strategies (`/job-strategies`)
- Job search strategies
- Application tracking
- Status management
- Follow-up scheduling

### 7. Networking (`/networking`)
- Professional contacts
- Opportunities
- Connection tracking
- Follow-up management

### 8. Interviews (`/interviews`)
- Question bank (behavioral, technical, domain)
- Prepared answers
- Difficulty levels
- Practice tracking

### 9. Metrics (`/metrics`)
- Profile completeness %
- Portal views
- Interactions
- Agent activity

## API Integration

### Available Endpoints

#### Authentication
- `POST /auth/register` — Register user
- `POST /auth/login` — Login
- `POST /auth/refresh` — Refresh token
- `POST /auth/logout` — Logout
- `POST /auth/change-password` — Change password

#### Career Modules (Development)
Endpoints will be added as modules are implemented:
- `/identity` — Professional identity
- `/competencies` — Skills management
- `/evidence` — Projects, positions, achievements
- `/job-strategies` — Job search tracking
- `/networking` — Contacts, opportunities
- `/interviews` — Interview prep
- `/metrics` — Analytics

### Making API Calls

```typescript
// Using React Query
import { useQuery } from '@tanstack/react-query'

export const useIdentity = () => {
  return useQuery({
    queryKey: ['identity'],
    queryFn: async () => {
      const { data } = await axiosInstance.get('/identity')
      return data
    },
  })
}

// In component
const { data, isLoading, error } = useIdentity()
```

## State Management

### Zustand Store

```typescript
import { useAuthStore } from '@/stores/authStore'

const { user, isAuthenticated, logout } = useAuthStore()
```

### Using Hooks

```typescript
import { useAuth } from '@/hooks/useAuth'

const { login, logout, user, isLoading, error } = useAuth()
```

## Design System

### Colors

**Primary**: Cyan
```
cyan-50, cyan-100, ..., cyan-900
Active states, buttons, highlights
```

**Neutral**: Slate
```
slate-50, slate-100, ..., slate-900
Text, backgrounds, borders
```

### Component Classes

```css
/* Buttons */
.btn-primary    /* Cyan button */
.btn-secondary  /* Slate button */
.btn-small      /* Small variant */

/* Forms */
.input-field    /* Text input */
.form-label     /* Field label */
.form-group     /* Field wrapper */

/* Cards */
.card           /* Card container */
.card-header    /* Card header */
.card-body      /* Card content */
.card-footer    /* Card footer */

/* Badges */
.badge-cyan     /* Cyan badge */
.badge-success  /* Green badge */
.badge-error    /* Red badge */
.badge-warning  /* Amber badge */
```

## Testing

### Test Structure

```
src/tests/
├── components/          # Component tests
├── hooks/              # Hook tests
├── pages/              # Page tests
├── fixtures/           # Mock data
├── utils.tsx           # Test utilities
└── setup.ts            # Vitest setup
```

### Writing Tests

```typescript
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MyComponent } from '@/components/MyComponent'

describe('MyComponent', () => {
  it('renders text', () => {
    render(<MyComponent />)
    expect(screen.getByText('Hello')).toBeInTheDocument()
  })
})
```

### Coverage Requirements

- Minimum 80% overall coverage
- All public functions tested
- Critical paths covered
- Edge cases tested

### Running Tests

```bash
npm test                # Run all tests
npm run test:ui        # Interactive UI
npm run test:coverage  # Generate report
```

## Performance Optimization

### Code Splitting

Routes are automatically code-split by React Router.

### Caching

React Query handles server state caching with intelligent invalidation.

### Memoization

Use `React.memo` for expensive components.

### Bundle Analysis

```bash
npm run build
# Analyze with bundlesize or similar
```

## Troubleshooting

### Port Already in Use

```bash
lsof -ti:8000 | xargs kill -9
```

### API Connection Failed

1. Check API is running: `curl http://api:8001/health`
2. Verify `VITE_API_BASE_URL` in `.env.local`
3. Check CORS in API configuration
4. Check browser console for CORS errors

### Tests Failing

```bash
rm -rf node_modules
npm install
npm test -- --clearCache
```

### Build Errors

```bash
npm run type-check  # Check TypeScript
npm run lint        # Check linting
npm run build       # Attempt build
```

## Environment Variables

### Development

```env
VITE_API_BASE_URL=http://api:8001/api/v1
VITE_LOG_LEVEL=debug
```

### Production

```env
VITE_API_BASE_URL=https://api.example.com/api/v1
VITE_LOG_LEVEL=warn
```

## Code Quality Standards

### TypeScript

- Strict mode enabled
- No `any` types
- Full type coverage

### ESLint Rules

- No unused variables
- No console logs (except warn/error)
- Prefer const over let
- Arrow functions for callbacks

### Prettier Formatting

- 2-space indentation
- Single quotes
- Trailing commas (ES5)
- Max line width: 100 characters

## SOLID Principles

All code follows SOLID principles:

- **Single Responsibility**: Each component/hook has one job
- **Open/Closed**: Extended via props, not modification
- **Liskov Substitution**: Type-safe substitution
- **Interface Segregation**: Specific interfaces
- **Dependency Inversion**: Depend on abstractions

## Next Steps

1. Implement CRUD hooks for each module
2. Connect components to API endpoints
3. Add comprehensive test coverage
4. Implement real-time metrics with WebSocket/SSE
5. Add PDF download integration
6. Performance optimization
7. Accessibility audit

## Support

For issues or questions:
- Email: cjhirashi@gmail.com
- GitHub: [Link to repository]
