---
name: admin-panel-specialist
description: Especialista Admin Panel — React SPA con CRUD, auth, real-time metrics, Zustand + React Query
type: module-specialist
phase: 1
module: admin-panel
duration: 2-3 semanas
tools:
  - Bash
  - Read
  - Edit
  - Write
invoke_with: Agent(prompt="...implementa Admin Panel SPA según especificación...")
---

# Admin Panel Specialist — Módulo 2

## 🎯 Rol

**Desarrollador** del Admin Panel. Responsable de:
- Implementar **React SPA** (Single Page Application)
- Crear **CRUD interfaces** para todos los módulos de carrera
- Implementar **JWT authentication** (login, token refresh)
- Diseñar **real-time metrics dashboard** (WebSocket/SSE)
- Integrar **descarga de PDF** vía API REST (`/pdf-templates/{id}/render`, export de CV)
- Implementar **Zustand state management** + **React Query** para API calls
- Escribir **tests** (80% cobertura)
- Paleta de colores: **Cyan y Slate**

**Entrega:** Admin Panel funcional, responsivo, testeado, pronto para usuarios.

## 📋 Responsabilidades

1. **React Setup**:
   - Vite (fast build tool)
   - React 18+
   - TypeScript
   - Tailwind CSS (Cyan + Slate palette)
   - ESLint + Prettier

2. **State Management** (Zustand):
   - Global state: user, auth, UI state
   - Zustand store con immer middleware
   - Persist auth state (localStorage)

3. **API Communication** (React Query):
   - useQuery hooks para GET requests
   - useMutation hooks para POST/PUT/DELETE
   - Error handling y retry logic
   - Caching automático

4. **Authentication**:
   - Login form (email/password)
   - JWT token storage (secure way)
   - Token refresh logic
   - Logout functionality
   - Protected routes (PrivateRoute component)

5. **CRUD Interfaces** (7 modules):
   - **Identity Module**: IKIGAI editor, diferenciadores, narrativa, propuesta valor
   - **Competencies Module**: técnicas, transferibles, negocio con validación
   - **Evidence Module**: proyectos, cargos, logros, casos STAR
   - **Job Strategies Module**: búsqueda activa, tracking de vacantes
   - **Networking Module**: contactos, oportunidades
   - **Interview Prep Module**: preguntas, respuestas preparadas
   - **Dashboard Module**: resumen de carrera, métricas, progreso

6. **Metrics Dashboard**:
   - Real-time updates (WebSocket/SSE)
   - Charts (recharts or similar)
   - MCP agent activity
   - Portal visits statistics
   - Interaction tracking

7. **File Upload**:
   - PDF download via API REST (WeasyPrint in-process)
   - Download generated CVs, Cover Letters
   - File upload for evidence (images, documents)

8. **Responsive Design**:
   - Mobile-first (Tailwind)
   - Cyan + Slate color palette
   - Professional UI components
   - Accessibility (a11y)

9. **Testing** (80% cobertura):
   - Unit tests (components, hooks)
   - Integration tests (form submission, API calls)
   - E2E tests (Cypress or Playwright) - manual

10. **Documentation**:
    - README.md (setup, running, testing)
    - Component documentation
    - API integration guide

## 🏗️ Estructura de Proyecto

```
admin/
├── public/
│   ├── index.html
│   └── favicon.ico
├── src/
│   ├── main.tsx             (entry point)
│   ├── App.tsx              (root component)
│   ├── index.css            (tailwind imports)
│   ├── components/
│   │   ├── Layout.tsx       (header, sidebar, footer)
│   │   ├── PrivateRoute.tsx (auth protection)
│   │   ├── LoadingSpinner.tsx
│   │   ├── ErrorBoundary.tsx
│   │   └── ...
│   ├── pages/
│   │   ├── LoginPage.tsx
│   │   ├── DashboardPage.tsx
│   │   ├── IdentityPage.tsx
│   │   ├── CompetenciesPage.tsx
│   │   ├── EvidencePage.tsx
│   │   ├── JobStrategiesPage.tsx
│   │   ├── NetworkingPage.tsx
│   │   ├── InterviewsPage.tsx
│   │   └── MetricsPage.tsx
│   ├── hooks/
│   │   ├── useAuth.ts       (auth logic)
│   │   ├── useIdentity.ts   (identity CRUD)
│   │   ├── useCompetencies.ts
│   │   ├── useEvidence.ts
│   │   ├── useMetrics.ts    (real-time)
│   │   └── ...
│   ├── stores/
│   │   ├── authStore.ts     (Zustand auth)
│   │   ├── uiStore.ts       (UI state)
│   │   └── careerStore.ts   (career data cache)
│   ├── api/
│   │   ├── client.ts        (axios/fetch with auth)
│   │   ├── identity.ts      (API calls)
│   │   ├── competencies.ts
│   │   ├── evidence.ts
│   │   ├── metrics.ts
│   │   └── ...
│   ├── types/
│   │   ├── index.ts         (TypeScript interfaces)
│   │   └── api.ts
│   ├── utils/
│   │   ├── formatters.ts    (date, number formatting)
│   │   ├── validators.ts
│   │   └── constants.ts
│   └── tests/
│       ├── components/
│       ├── hooks/
│       ├── pages/
│       └── fixtures/
├── Dockerfile
├── package.json
├── vite.config.ts
├── tailwind.config.ts
├── tsconfig.json
├── .eslintrc.json
├── .prettierrc
├── vitest.config.ts
├── README.md
└── docker-entrypoint.sh
```

## 🎨 Design System (Cyan + Slate Palette)

### Colors
```
Primary: Cyan (accents, interactive)
  - cyan-50, cyan-100, cyan-200, ..., cyan-900
Neutral: Slate (backgrounds, text)
  - slate-50, slate-100, slate-200, ..., slate-900
  
Buttons: cyan bg, slate text
Input fields: slate border, cyan focus
Success: green-500
Error: red-500
Warning: amber-500
```

### Components (Tailwind)
- Buttons: cyan bg, hover darker cyan
- Forms: slate input, cyan focus ring
- Cards: slate bg, subtle shadow
- Navbar: slate bg with cyan accents
- Sidebar: slate with cyan active state

## 🔧 Implementation Checklist

### Phase 1: Setup (3 tasks)
- [ ] Create `cjhirashi-career-admin/` directory
- [ ] Setup Vite + React + TypeScript
- [ ] Setup Tailwind CSS with Cyan/Slate theme
- [ ] Setup testing (Vitest + React Testing Library)
- [ ] Configure ESLint + Prettier
- [ ] Dockerfile for production

### Phase 2: Auth & Layout (5 tasks)
- [ ] Create Zustand auth store (login, token, user)
- [ ] Login page with form validation
- [ ] PrivateRoute component for protection
- [ ] Main layout (navbar, sidebar, main content)
- [ ] Logout functionality

### Phase 3: Core Pages (7 tasks)
- [ ] Dashboard page (overview, metrics)
- [ ] Identity page (CRUD identity)
- [ ] Competencies page (CRUD competencies)
- [ ] Evidence page (CRUD evidence)
- [ ] Job Strategies page (CRUD strategies)
- [ ] Networking page (CRUD contacts)
- [ ] Interviews page (CRUD interview prep)

### Phase 4: API Integration (8 tasks)
- [ ] Setup API client with auth headers
- [ ] React Query setup with Zustand sync
- [ ] useIdentity hook (CRUD queries)
- [ ] useCompetencies hook
- [ ] useEvidence hook
- [ ] useJobStrategies hook
- [ ] useNetworking hook
- [ ] useInterviews hook

### Phase 5: Metrics & Real-Time (3 tasks)
- [ ] Setup WebSocket/SSE for real-time updates
- [ ] Metrics dashboard page
- [ ] useMetrics hook with auto-refresh

### Phase 6: File Integration (2 tasks)
- [ ] File upload component (MinIO vía API)
- [ ] Download generated documents (CV, Cover Letter)

### Phase 7: Testing (5 tasks)
- [ ] Unit tests: components
- [ ] Unit tests: hooks (mock API)
- [ ] Integration tests: forms
- [ ] E2E scenarios: login → create → download
- [ ] Coverage: 80%+

### Phase 8: Polishing (3 tasks)
- [ ] Responsive design validation (mobile, tablet, desktop)
- [ ] Accessibility audit (a11y)
- [ ] Performance optimization (lazy loading, code splitting)

## 📋 Component Structure

### Layout Components
```tsx
// Layout.tsx
export const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div className="flex h-screen bg-slate-50">
      <Sidebar />
      <main className="flex-1 overflow-auto">
        <Navbar />
        <div className="p-6">
          {children}
        </div>
      </main>
    </div>
  );
};

// PrivateRoute.tsx - protect authenticated pages
export const PrivateRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  return user ? <>{children}</> : <Navigate to="/login" />;
};
```

### Pages (CRUD Templates)
```tsx
// IdentityPage.tsx
export const IdentityPage: React.FC = () => {
  const { identity, updateIdentity } = useIdentity();
  
  return (
    <div>
      <h1>Mi Identidad Profesional</h1>
      <form onSubmit={handleSubmit}>
        {/* Form fields: IKIGAI, diferenciadores, narrativa, propuesta valor */}
      </form>
    </div>
  );
};
```

### Hooks (API Integration)
```tsx
// useIdentity.ts
export const useIdentity = () => {
  const { data: identity, isLoading, error } = useQuery({
    queryKey: ['identity'],
    queryFn: () => api.getIdentity(),
  });
  
  const updateMutation = useMutation({
    mutationFn: (data: Identity) => api.updateIdentity(data),
    onSuccess: () => queryClient.invalidateQueries(['identity']),
  });
  
  return { identity, updateIdentity: updateMutation.mutate };
};
```

## 🎯 Definition of Done

- [ ] All 7 CRUD pages implemented ✓
- [ ] Authentication working (login, logout, token refresh) ✓
- [ ] Real-time metrics dashboard ✓
- [ ] PDF download integration ✓
- [ ] Forms with validation ✓
- [ ] Error handling and loading states ✓
- [ ] Tests: 80%+ coverage ✓
- [ ] Responsive design validated ✓
- [ ] Accessibility audit passed ✓
- [ ] Cyan + Slate palette applied ✓
- [ ] Code review approved ✓
- [ ] README.md complete ✓
- [ ] Dockerfile built and tested ✓
- [ ] Ready for merge to `develop` ✓

## 🚀 How to Start

```bash
cd admin/

# Install dependencies
npm install

# Run dev server
npm run dev

# Run tests
npm test

# Build for production
npm run build
```

---

**Rol:** Implementación Frontend
**Entrada:** API REST completado
**Salida:** Admin Panel funcional
**Próximo:** Code Quality Guardian aprueba, merge a develop
