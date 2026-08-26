# Portal Público — Setup Guide

## Quick Start

### Local Development

```bash
cd portal
npm install
npm run dev
```

Server runs at `http://localhost:8000` with proxy to `http://localhost:8001` (API)

### Production Build

```bash
npm run build
npm run preview
```

### Docker

```bash
docker build -t portal-publico .
docker run -p 8003:8000 -e VITE_API_URL=http://api:8001/api/v1 portal-publico
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env.local`:

```bash
cp .env.example .env.local
```

Configure:

```env
# API URL (dev uses proxy, production uses this)
VITE_API_URL=http://localhost:8001/api/v1

# Enable/disable event tracking
VITE_TRACKING_ENABLED=true
```

## API Integration

The portal is **read-only** and consumes these endpoints:

| Endpoint | Purpose | Used By |
|----------|---------|---------|
| `GET /api/v1/identity` | Profile info | HomePage, AboutPage |
| `GET /api/v1/competencies` | Skills list | HomePage, AboutPage |
| `GET /api/v1/evidence` | Projects | ProjectsPage, HomePage |
| `GET /api/v1/networking` | Blog posts | BlogPage |
| `POST /api/v1/events/track` | Tracking | All pages |

No authentication required (public endpoints).

## Project Structure

```
src/
├── pages/         # 6 page components
├── components/    # Reusable components
│   ├── Layout/    # Header, Footer, Layout
│   └── Common/    # Cards, Loaders, Errors
├── hooks/         # React hooks (data, tracking)
├── api/           # API client and endpoints
├── types/         # TypeScript interfaces
├── stores/        # Zustand state (UI)
└── tests/         # Test files
```

## Development Workflow

### Adding a New Feature

1. **Create Component**:
   ```tsx
   // src/components/MyComponent.tsx
   export const MyComponent = () => {
     return <div>...</div>
   }
   ```

2. **Write Tests**:
   ```tsx
   // src/tests/components/MyComponent.spec.tsx
   describe('MyComponent', () => {
     it('renders', () => { ... })
   })
   ```

3. **Lint & Format**:
   ```bash
   npm run lint:fix
   npm run format
   ```

4. **Run Tests**:
   ```bash
   npm test
   npm run test:coverage
   ```

### API Integration

Use hooks for data fetching:

```tsx
import { useProjects } from '@/hooks/useProjects'

export const MyPage = () => {
  const { data, isLoading, error } = useProjects()
  // ...
}
```

Hooks use React Query for automatic caching and stale time management.

### Event Tracking

Track user interactions:

```tsx
import { useTrackClick } from '@/hooks/useTracking'

export const MyButton = () => {
  const { trackClick } = useTrackClick()
  
  const handleClick = () => {
    trackClick('my-button', { extra: 'data' })
  }
  
  return <button onClick={handleClick}>Click</button>
}
```

## Performance Optimization

### Image Lazy Loading

```tsx
<img src="..." alt="..." loading="lazy" />
```

### Code Splitting

Routes are automatically code-split by React Router.

### Caching

React Query stale times:
- Identity, Competencies: 1 hour
- Projects, Blog: 1 hour
- Events: Real-time (no cache)

## Accessibility

### Guidelines

- Use semantic HTML (`<button>`, `<nav>`, `<article>`)
- Provide alt text for images
- Ensure 4.5:1 contrast ratio
- Support keyboard navigation
- Include ARIA labels when needed

### Testing

```bash
# Run tests with accessibility checks
npm test
```

## SEO Optimization

### Meta Tags

Updated in `index.html`:

```html
<meta name="description" content="..." />
<meta name="keywords" content="..." />
<meta property="og:title" content="..." />
```

### Structured Data

Add schema.org JSON-LD:

```tsx
<script type="application/ld+json">
  {JSON.stringify({ "@context": "https://schema.org", ... })}
</script>
```

### Sitemap

Add `public/sitemap.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://portafolio.cjhirashi.com/</loc></url>
  ...
</urlset>
```

## Deployment Checklist

Before deploying:

- [ ] All tests pass: `npm test`
- [ ] No lint errors: `npm run lint`
- [ ] Build succeeds: `npm run build`
- [ ] Lighthouse > 90: Run locally
- [ ] Accessibility audit: WCAG 2.1 AA
- [ ] SEO validation: Meta tags, sitemap
- [ ] Mobile responsive: Test on devices
- [ ] API integration: Verify endpoints
- [ ] Environment variables: Set correctly

## Troubleshooting

### API Connection Issues

1. Check API is running: `curl http://api:8001/health`
2. Verify proxy in `vite.config.ts`
3. Check CORS headers from API
4. Review network tab in DevTools

### Build Errors

1. Clear cache: `rm -rf node_modules package-lock.json && npm install`
2. Run type check: `npm run type-check`
3. Check for `any` types: `npm run lint`

### Performance Issues

1. Analyze bundle: `npm run build && npm run preview`
2. Check React Query devtools
3. Profile in Chrome DevTools
4. Review image sizes and formats

### Test Failures

1. Run specific test: `npm test -- MyComponent`
2. Check test coverage: `npm run test:coverage`
3. Review mocks in test files
4. Verify setup files

## Further Reading

- React: https://react.dev
- React Router: https://reactrouter.com
- React Query: https://tanstack.com/query
- Tailwind: https://tailwindcss.com
- TypeScript: https://typescriptlang.org
- Vitest: https://vitest.dev

## Support

For issues: Check README.md or contact cjhirashi@gmail.com

---

**Last Updated**: 2024
