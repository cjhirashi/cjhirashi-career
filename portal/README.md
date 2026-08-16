# Portal Público - Read-Only React SPA

Public portfolio and career showcase for Carlos Jiménez Hirashi. A modern, performant React SPA built with TypeScript, Vite, and Tailwind CSS.

## Features

- **Read-Only Interface**: Secure public portfolio display
- **Responsive Design**: Mobile-first, fully responsive
- **SEO Optimized**: Meta tags, structured data, semantic HTML
- **Performance First**: Lighthouse > 90, code splitting, lazy loading
- **Event Tracking**: Track pageviews, clicks, downloads
- **Accessible**: WCAG 2.1 AA compliance

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling (Cyan + Slate palette)
- **React Router** - Client-side routing
- **React Query** - Data fetching and caching
- **Zustand** - Lightweight state management
- **Vitest** - Unit testing
- **ESLint + Prettier** - Code quality

## Project Structure

```
src/
├── pages/              # Page components (Home, About, Projects, etc.)
├── components/         # Reusable components
│   ├── Layout/        # Header, Footer, Layout wrapper
│   ├── Common/        # ProjectCard, BlogCard, LoadingSpinner, etc.
│   └── Features/      # Feature-specific components
├── hooks/             # Custom React hooks
│   ├── useIdentity.ts
│   ├── useProjects.ts
│   ├── useBlog.ts
│   └── useTracking.ts
├── api/               # API client and endpoints
│   ├── client.ts
│   ├── identity.ts
│   ├── projects.ts
│   ├── blog.ts
│   └── tracking.ts
├── stores/            # Zustand stores
├── types/             # TypeScript types
├── utils/             # Utility functions
├── tests/             # Test files
└── App.tsx            # Root component
```

## Getting Started

### Prerequisites

- Node.js >= 18
- npm or yarn

### Installation

```bash
cd portal
npm install
```

### Development

```bash
npm run dev
```

Server runs at `http://localhost:8000` (with proxy to API at http://api:8001)

### Build

```bash
npm run build
```

### Testing

```bash
# Run tests
npm test

# Watch mode
npm run test:ui

# Coverage report
npm run test:coverage
```

### Code Quality

```bash
# Lint
npm run lint

# Fix lint issues
npm run lint:fix

# Format code
npm run format

# Type checking
npm run type-check
```

## Pages

### HomePage (Entry Point)
- Hero section with professional branding
- Quick stats and value proposition
- Featured projects showcase
- Call-to-action buttons
- SEO optimized

### AboutPage
- Detailed professional biography
- IKIGAI explanation
- Technical competencies
- Experience timeline
- Core values

### ProjectsPage
- Complete project portfolio
- Filterable by technology
- Project cards with descriptions
- Links to live projects and GitHub

### BlogPage
- Technical articles
- Search functionality
- Tag-based filtering
- Article previews

### ContactPage
- Contact form
- Social media links
- Email contact
- Response time indicator

### NotFoundPage
- 404 error handling
- Navigation back to main site

## API Integration

The portal consumes a read-only API with the following endpoints:

- `GET /api/v1/identity` - Profile information
- `GET /api/v1/competencies` - List of skills
- `GET /api/v1/evidence` - Projects/portfolio items
- `GET /api/v1/networking` - Blog posts/articles
- `POST /api/v1/events/track` - Event tracking

**Authentication**: None (public endpoints only)

## Event Tracking

Tracks user interactions:

- **Pageviews**: Each page navigation
- **Clicks**: CTA buttons, project links, social links
- **Downloads**: CV, documents
- **Form Submissions**: Contact form

Disable tracking by setting `VITE_TRACKING_ENABLED=false` in `.env`

## Design System

### Palette

- **Primary**: Cyan (e.g., #065f73)
- **Neutral**: Slate (e.g., #0f172a)
- **Success**: Green
- **Error**: Red

### Typography

- **Headings**: Bold, scale-based sizing
- **Body**: Regular, readable line-height
- **Code**: Monospace with contrast

### Components

- Buttons, cards, forms follow consistent patterns
- Hover and focus states for accessibility
- Responsive spacing and sizing

## Performance

- **Lighthouse Score**: Target > 90
- **Code Splitting**: Route-based chunks
- **Image Optimization**: Lazy loading, responsive sizes
- **Caching**: React Query stale times configured
- **Bundle Size**: Optimized with tree-shaking

## Accessibility

- **WCAG 2.1 AA**: Level AA compliance
- **Keyboard Navigation**: Full keyboard support
- **Screen Readers**: Semantic HTML, ARIA labels
- **Color Contrast**: 4.5:1 minimum
- **Focus Management**: Visible focus indicators

## Testing

### Coverage Goals

- **Unit Tests**: 60% (components, hooks, utils)
- **Integration Tests**: 30% (pages, API flows)
- **E2E Tests**: 10% (critical user paths)
- **Overall**: 80%+ minimum

### Test Structure

```
tests/
├── components/  # Component unit tests
├── pages/       # Page integration tests
├── hooks/       # Hook tests
└── fixtures/    # Mock data
```

## Deployment

### Docker

Build image:

```bash
docker build -t portal-publico .
```

Run container:

```bash
docker run -p 8003:8000 portal-publico
```

### Docker Compose

Included in root project `docker-compose.yml`:

```bash
docker-compose up portal
```

Accessible at `http://localhost:8003`

## Environment Variables

```env
# API Configuration
VITE_API_URL=http://localhost:8001/api/v1

# Feature Flags
VITE_TRACKING_ENABLED=true
```

## Code Quality Standards

- **TypeScript**: No `any` types, strict mode enabled
- **SOLID Principles**: Single responsibility, dependency injection
- **Clean Code**: Descriptive names, DRY, small functions
- **No Comments**: Self-documenting code preferred
- **Error Handling**: Try-catch with user-friendly messages
- **Logging**: Minimal, for debugging only

## SEO

- Meta tags (title, description, keywords)
- Open Graph for social sharing
- Schema.org structured data
- Semantic HTML
- Sitemap and robots.txt
- Mobile-friendly

## Performance Optimization

- Code splitting by route
- Lazy loading of images
- Caching with React Query
- Service worker (optional)
- Minification and compression
- CDN-friendly headers

## Contributing

When adding features:

1. Follow TypeScript strict mode
2. Add tests (aim for 80%+ coverage)
3. Update documentation
4. Run linter and formatter
5. Test responsiveness
6. Validate accessibility

## License

Private project.

## Support

For issues, contact: cjhirashi@gmail.com

---

**Version**: 0.1.0  
**Last Updated**: 2024  
**Maintainer**: Carlos Jiménez Hirashi
