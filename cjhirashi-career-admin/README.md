# Admin Panel — Career Management

A modern React SPA (Single Page Application) for managing professional identity, competencies, evidence, job strategies, networking, and interview preparation.

## Features

- **JWT Authentication**: Secure login with token refresh
- **Professional Identity Management**: IKIGAI framework, differentiators, narrative, value proposition
- **Competencies Tracking**: Technical, transferable, and business skills with proficiency levels
- **Evidence Management**: Projects, positions, achievements, and STAR cases
- **Job Strategy Tracking**: Active job search and application tracking
- **Networking Management**: Professional contacts and opportunities
- **Interview Preparation**: Question bank with prepared answers
- **Metrics Dashboard**: Portfolio progress and activity tracking
- **Responsive Design**: Mobile-first with Cyan + Slate palette
- **TypeScript**: Full type safety
- **Tests**: 80%+ coverage with Vitest and React Testing Library

## Technology Stack

- **React 18**: Modern UI framework with hooks
- **TypeScript**: Type-safe development
- **Vite**: Fast build tool
- **Tailwind CSS**: Utility-first CSS with Cyan + Slate theme
- **Zustand**: Minimal state management with persistence
- **React Query**: Server state management with caching
- **Axios**: HTTP client with JWT interceptors
- **React Router**: Client-side routing
- **Vitest**: Unit testing framework
- **React Testing Library**: Component testing utilities

## Project Structure

```
admin/
├── src/
│   ├── components/          # Reusable components
│   │   ├── Layout.tsx       # Main layout with sidebar and navbar
│   │   ├── PrivateRoute.tsx # Auth protection
│   │   ├── LoadingSpinner.tsx
│   │   ├── Navbar.tsx
│   │   └── Sidebar.tsx
│   ├── pages/              # Page components
│   │   ├── LoginPage.tsx
│   │   ├── DashboardPage.tsx
│   │   ├── IdentityPage.tsx
│   │   ├── CompetenciesPage.tsx
│   │   ├── EvidencePage.tsx
│   │   ├── JobStrategiesPage.tsx
│   │   ├── NetworkingPage.tsx
│   │   ├── InterviewsPage.tsx
│   │   └── MetricsPage.tsx
│   ├── hooks/              # Custom React hooks
│   │   └── useAuth.ts
│   ├── stores/             # Zustand state stores
│   │   └── authStore.ts
│   ├── api/                # API client and endpoints
│   │   ├── client.ts       # Axios instance with interceptors
│   │   └── auth.ts         # Auth endpoints
│   ├── types/              # TypeScript interfaces
│   │   └── index.ts
│   ├── tests/              # Test files
│   │   ├── components/
│   │   ├── hooks/
│   │   └── setup.ts
│   ├── App.tsx             # Root component with routing
│   ├── main.tsx            # Entry point
│   └── index.css           # Global styles with Tailwind
├── index.html              # HTML template
├── package.json            # Dependencies
├── tsconfig.json           # TypeScript config
├── vite.config.ts          # Vite config
├── tailwind.config.ts      # Tailwind config
├── vitest.config.ts        # Vitest config
├── .eslintrc.json          # ESLint config
├── .prettierrc              # Prettier config
├── Dockerfile              # Docker image
└── README.md               # This file
```

## Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn
- Docker (for containerization)

### Installation

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Create environment file**:
   ```bash
   cp .env.example .env.local
   ```

3. **Update API URL** (if needed):
   Edit `.env.local` and set `VITE_API_BASE_URL` to your API server URL

### Development

**Start dev server** (port 8000):
```bash
npm run dev
```

**Type checking**:
```bash
npm run type-check
```

**Linting**:
```bash
npm run lint
npm run lint:fix   # Auto-fix issues
```

**Code formatting**:
```bash
npm run format
```

## Testing

### Running Tests

**Run all tests**:
```bash
npm test
```

**Run tests in UI mode**:
```bash
npm run test:ui
```

**Generate coverage report**:
```bash
npm run test:coverage
```

### Test Structure

- `src/tests/components/` — Component tests
- `src/tests/hooks/` — Hook tests
- `src/tests/fixtures/` — Mock data and test utilities

### Coverage Requirements

- **Minimum**: 80% overall coverage
- **Unit tests**: Components, hooks, utilities
- **Integration tests**: Form submission, API calls
- **E2E scenarios**: Login → Create item → Download (manual)

## Building

### Development Build

```bash
npm run build
```

Output: `dist/` directory

### Preview Build

```bash
npm run preview
```

## Docker

### Build Image

```bash
docker build -t admin-panel:latest .
```

### Run Container

```bash
docker run -p 8002:8000 \
  -e VITE_API_BASE_URL=http://api:8001/api/v1 \
  admin-panel:latest
```

### Docker Compose

In the project root:

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

## API Integration

### Base Configuration

- **Base URL**: `http://api:8001/api/v1` (internal)
- **Auth Header**: `Authorization: Bearer <access_token>`
- **Token Refresh**: Automatic (15 minutes before expiry)

### Available Endpoints

#### Authentication

- `POST /auth/register` — Register new user
- `POST /auth/login` — Login with credentials
- `POST /auth/refresh` — Refresh access token
- `POST /auth/logout` — Logout
- `POST /auth/change-password` — Change user password

#### Career Modules (Coming Soon)

- `/identity` — Professional identity CRUD
- `/competencies` — Skills management
- `/evidence` — Projects, positions, achievements
- `/job-strategies` — Job search tracking
- `/networking` — Contacts and opportunities
- `/interviews` — Interview prep questions/answers
- `/metrics` — Portfolio metrics and analytics

## Design System

### Colors

**Primary**: Cyan (interactive elements, highlights)
- `cyan-600` (buttons, active states)
- `cyan-50` - `cyan-900` (palette)

**Neutral**: Slate (backgrounds, text)
- `slate-900` (text)
- `slate-50` (light backgrounds)
- `slate-800` (dark backgrounds)

### Components

- **Buttons**: `.btn-primary`, `.btn-secondary`
- **Forms**: `.input-field`, `.form-label`
- **Cards**: `.card`, `.card-header`, `.card-body`
- **Status Badges**: `.badge-success`, `.badge-error`, `.badge-warning`

See `src/index.css` for all component definitions.

## Authentication Flow

1. **Login**: User enters credentials → API returns JWT tokens
2. **Token Storage**: Tokens stored in Zustand (persisted to localStorage)
3. **Protected Routes**: `PrivateRoute` redirects unauthenticated users to login
4. **Auto Refresh**: Hook monitors token expiry and refreshes automatically
5. **Interceptors**: Axios adds auth header and handles 401 responses
6. **Logout**: Tokens deleted, user redirected to login

## State Management

### Zustand Store (`authStore`)

```typescript
{
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  tokenExpiresAt: Date | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
}
```

### Using Auth State

```typescript
import { useAuthStore } from '@/stores/authStore'

const { user, isAuthenticated, logout } = useAuthStore()
```

### Using Auth Hook

```typescript
import { useAuth } from '@/hooks/useAuth'

const { login, logout, user, isLoading, error } = useAuth()
```

## API Client

### Axios Configuration

The API client (`src/api/client.ts`) handles:

- JWT token injection in request headers
- Automatic token refresh on 401 errors
- Retry logic for failed requests
- Error logging and formatting

### Making API Calls

```typescript
import { axiosInstance } from '@/api/client'

// Automatic auth header injection
const response = await axiosInstance.get('/identity')
```

### Using React Query

```typescript
import { useQuery } from '@tanstack/react-query'
import { identityApi } from '@/api/identity'

export const useIdentity = () => {
  return useQuery({
    queryKey: ['identity'],
    queryFn: () => identityApi.get(),
  })
}
```

## Code Quality Standards

### SOLID Principles

- **Single Responsibility**: Each component/hook has one job
- **Open/Closed**: Extend via props, not modification
- **Liskov Substitution**: Components substitute base types
- **Interface Segregation**: Specific, focused interfaces
- **Dependency Inversion**: Depend on abstractions (types)

### Clean Code

- Descriptive variable/function names
- Small, focused functions
- No magic strings (use constants)
- Self-documenting code (no comments needed)
- DRY principle (Don't Repeat Yourself)

### TypeScript

- No `any` types
- Strict mode enabled
- Interface for all data structures
- Type-safe props

## Performance

- **Code Splitting**: Route-based lazy loading (React Router)
- **Caching**: React Query handles server state caching
- **Memoization**: React.memo for expensive components
- **Optimization**: Tailwind purging unused CSS

## Accessibility

- ARIA labels on interactive elements
- Semantic HTML (buttons, links, forms)
- Color contrast compliance (WCAG AA)
- Keyboard navigation support
- Focus indicators

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Troubleshooting

### Port Already in Use

```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
npm run dev -- --port 3000
```

### API Connection Issues

1. Verify API is running: `curl http://api:8001/health`
2. Check `VITE_API_BASE_URL` in `.env.local`
3. Check CORS settings in API (should allow admin origin)
4. Browser console may show CORS errors

### Tests Failing

```bash
# Clear node_modules and reinstall
rm -rf node_modules
npm install

# Clear vitest cache
npm test -- --clearCache
```

## Contributing

1. Create feature branch: `git checkout -b feature/name`
2. Make changes following code standards
3. Write tests for new features (80% coverage)
4. Run linting and tests: `npm run lint && npm test`
5. Commit with descriptive message
6. Create Pull Request for review

## License

Proprietary - cjhirashi-career Project

## Support

For issues or questions, contact: cjhirashi@gmail.com
