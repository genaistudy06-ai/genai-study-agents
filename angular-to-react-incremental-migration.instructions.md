# Angular 18 NX → React: Incremental Module-by-Module Migration
# Copilot Agent Addendum — Strangler Fig + Module Federation Strategy

> **Companion to**: `angular-to-react-migration.instructions.md`
> **Pattern**: Strangler Fig — Angular shell stays alive; React modules replace Angular feature areas one at a time. Users never see a big-bang cutover. Both frameworks coexist in production until migration is 100% complete.

---

## 🧠 Agent Context for Incremental Mode

When the user says **"migrate [module name]"**, you operate in **Module Migration Mode**:

1. Confirm the module name and locate its Angular source files
2. Run the **Pre-Migration Checklist** (§PRE)
3. Produce React output files following all rules from the main instructions file
4. Run the **Post-Migration Checklist** (§POST)
5. Output a **Module Migration Report** (§REPORT)

You migrate **one module at a time**. Never touch files outside the stated module scope unless they are shared utilities that block the migration.

---

## 🏗️ Architecture: How Angular + React Coexist

### The Strangler Fig Model

```
┌─────────────────────────────────────────────────────────────┐
│                   Angular Shell App (Host)                   │
│   (routing, auth shell, global nav, layout — stays Angular) │
│                                                              │
│  ┌───────────────┐  ┌───────────────┐  ┌────────────────┐  │
│  │ Feature A     │  │ Feature B     │  │  Feature C     │  │
│  │ ❌ Angular    │  │ ✅ React MFE  │  │ ✅ React MFE   │  │
│  │ (not yet)     │  │ (migrated)    │  │  (migrated)    │  │
│  └───────────────┘  └───────────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         │            NX Module Federation         │
         └────────────────────┴────────────────────┘
```

### Two Implementation Options

| Option | When to Use | Complexity |
|---|---|---|
| **A: Module Federation** (Webpack/Vite) | Separate deployable bundles per feature | High — but true micro-frontend isolation |
| **B: Angular Element Wrapper** | Embed React component inside existing Angular route | Medium — fastest to start |
| **C: Route Takeover** | React app takes over an entire URL segment from Angular | Low — simplest, recommended for most teams |

**Recommended: Option C (Route Takeover)** — one React app per major feature area, Angular router delegates the route to React Router. Start here unless your team already uses Module Federation.

---

## 🚦 Option C: Route Takeover (Recommended Start)

### Step 1 — Scaffold React App in NX Alongside Angular

```bash
# Create React app for the feature being migrated
nx g @nx/react:application --name=feature-products \
  --bundler=vite \
  --style=scss \
  --unitTestRunner=vitest \
  --e2eTestRunner=none \
  --routing=true \
  --directory=apps/feature-products

# Output:
# apps/feature-products/        ← New React app
# apps/feature-products-e2e/    ← Optional E2E
```

### Step 2 — Angular Shell Delegates the Route

In the Angular shell `AppRoutingModule`, redirect the feature route to the React app URL:

```typescript
// apps/shell/src/app/app-routing.module.ts

// BEFORE — Angular handled this route
{
  path: 'products',
  loadChildren: () =>
    import('./features/products/products.module').then(m => m.ProductsModule),
}

// AFTER — React app handles this route (served on different port in dev, same domain in prod)
{
  path: 'products',
  component: ReactMfeWrapperComponent,  // thin wrapper (see below)
}
```

### Step 3 — Angular Wrapper for React App (Bridge Component)

```typescript
// apps/shell/src/app/shared/react-mfe-wrapper/react-mfe-wrapper.component.ts
// This is a TEMPORARY Angular component — deleted when migration is complete

import { Component, Input, OnDestroy } from '@angular/core';
import { Router, NavigationEnd } from '@angular/router';
import { filter, takeUntil } from 'rxjs/operators';
import { Subject } from 'rxjs';

@Component({
  standalone: true,
  selector: 'app-react-mfe-wrapper',
  template: `
    <iframe
      [src]="mfeUrl"
      style="width:100%;height:calc(100vh - 64px);border:none;"
      title="Products Module">
    </iframe>
  `,
})
export class ReactMfeWrapperComponent implements OnDestroy {
  private destroy$ = new Subject<void>();

  // In dev: React Vite dev server port. In prod: same domain, different path via reverse proxy.
  readonly mfeUrl = '/react/products';

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }
}
```

> **Note**: For deeper integration (shared auth tokens, cross-frame events), use `postMessage` bridge (§BRIDGE section below). For most read-heavy modules, the iframe approach is sufficient.

---

## 🏗️ Option A: NX Module Federation (Full Micro-Frontend)

Use this when you need shared state, no iframe, and independent deployments.

### Step 1 — Convert Angular Shell to Module Federation Host

```bash
nx add @nx/angular
nx g @nx/angular:setup-mf --appName=shell --mfType=host --federationType=dynamic
```

### Step 2 — Scaffold React Remote

```bash
nx g @nx/react:application --name=feature-products \
  --bundler=webpack \
  --mf \
  --mfType=remote \
  --host=shell \
  --port=4201
```

### Step 3 — React Remote Entry Point

```typescript
// apps/feature-products/src/app/remote-entry/entry.module.ts
import React from 'react';
import { createRoot } from 'react-dom/client';
import { RouterProvider } from 'react-router-dom';
import { productsRouter } from './products.router';

const mount = (el: HTMLElement): void => {
  const root = createRoot(el);
  root.render(<RouterProvider router={productsRouter} />);
};

// Expose mount function for Angular host
export { mount };
```

### Step 4 — Angular Host Loads React Remote

```typescript
// apps/shell/src/app/products-mfe/products-mfe.component.ts
import { Component, ElementRef, OnInit, OnDestroy } from '@angular/core';

@Component({
  standalone: true,
  selector: 'app-products-mfe',
  template: `<div #mountPoint style="height: 100%;"></div>`,
})
export class ProductsMfeComponent implements OnInit, OnDestroy {
  private mountPoint!: ElementRef<HTMLDivElement>;
  private unmount?: () => void;

  async ngOnInit(): Promise<void> {
    // Dynamically load React MFE
    const { mount } = await import('feature-products/Module') as any;
    this.unmount = mount(this.mountPoint.nativeElement, {
      // Pass Angular-owned shared state as initial props
      authToken: this.authService.getToken(),
      theme: this.themeService.current(),
    });
  }

  ngOnDestroy(): void {
    this.unmount?.();
  }
}
```

### Module Federation Webpack Config (React Remote)

```javascript
// apps/feature-products/webpack.config.js
const { withModuleFederation } = require('@nx/react/module-federation');
const config = require('./module-federation.config');

module.exports = withModuleFederation({
  ...config,
  shared: (libraryName, defaultConfig) => {
    // Force singleton for React — critical for hooks to work correctly
    if (['react', 'react-dom', 'react-router-dom'].includes(libraryName)) {
      return { ...defaultConfig, singleton: true, strictVersion: true };
    }
    // Share React Query client so cache is shared between remotes
    if (libraryName === '@tanstack/react-query') {
      return { ...defaultConfig, singleton: true };
    }
    return defaultConfig;
  },
});
```

---

## 🌉 Cross-Framework Communication Bridge

When Angular and React modules need to share data (user session, theme, notifications), use a framework-agnostic event bus.

### Shared Event Bus (Pure TypeScript — no framework)

```typescript
// libs/util/src/lib/migration-bridge/event-bus.ts
// Framework-agnostic. Works in Angular services AND React hooks.

type EventMap = {
  'auth:login': { userId: string; token: string };
  'auth:logout': void;
  'theme:change': { theme: 'light' | 'dark' };
  'notification:show': { type: 'success' | 'error' | 'info'; message: string };
  'cart:updated': { itemCount: number };
};

type EventKey = keyof EventMap;
type Handler<K extends EventKey> = (payload: EventMap[K]) => void;

class MigrationEventBus {
  private listeners = new Map<EventKey, Set<Handler<any>>>();

  emit<K extends EventKey>(event: K, payload: EventMap[K]): void {
    this.listeners.get(event)?.forEach(h => h(payload));
  }

  on<K extends EventKey>(event: K, handler: Handler<K>): () => void {
    if (!this.listeners.has(event)) this.listeners.set(event, new Set());
    this.listeners.get(event)!.add(handler);
    return () => this.listeners.get(event)?.delete(handler); // returns unsubscribe fn
  }
}

// Singleton on window — accessible from both frameworks
declare global {
  interface Window { __migrationBus: MigrationEventBus; }
}

window.__migrationBus ??= new MigrationEventBus();
export const migrationBus = window.__migrationBus;
```

### Angular Side: Emit to React

```typescript
// Angular service — emits events when auth state changes
@Injectable({ providedIn: 'root' })
export class AuthService {
  login(credentials: Credentials): Observable<void> {
    return this.http.post<AuthResponse>('/api/auth/login', credentials).pipe(
      tap(({ userId, token }) => {
        migrationBus.emit('auth:login', { userId, token });
      })
    );
  }

  logout(): void {
    migrationBus.emit('auth:logout', undefined);
    // ... Angular cleanup
  }
}
```

### React Side: Subscribe to Angular Events

```typescript
// libs/data-access/src/lib/hooks/useMigrationAuth.ts
// React hook that listens to Angular-emitted auth events

export function useMigrationAuth(): void {
  const login = useAuthStore(s => s.login);
  const logout = useAuthStore(s => s.logout);

  useEffect(() => {
    const unsubLogin = migrationBus.on('auth:login', ({ userId, token }) => {
      login(userId, token);
    });
    const unsubLogout = migrationBus.on('auth:logout', () => {
      logout();
    });

    return () => {
      unsubLogin();
      unsubLogout();
    };
  }, [login, logout]);
}

// Use in React app root:
// function App() {
//   useMigrationAuth(); // sync auth from Angular shell
//   return <RouterProvider router={router} />;
// }
```

### Shared LocalStorage State (Simpler Alternative)

```typescript
// libs/util/src/lib/migration-bridge/shared-state.ts
// For simple read-only state Angular → React (theme, locale, user prefs)

const SHARED_KEYS = {
  USER: '__shared_user',
  THEME: '__shared_theme',
  LOCALE: '__shared_locale',
} as const;

export function getSharedUser(): SharedUser | null {
  try {
    const raw = sessionStorage.getItem(SHARED_KEYS.USER);
    return raw ? (JSON.parse(raw) as SharedUser) : null;
  } catch {
    return null;
  }
}

// Angular sets this on login; React reads on boot
export function setSharedUser(user: SharedUser): void {
  sessionStorage.setItem(SHARED_KEYS.USER, JSON.stringify(user));
}
```

---

## 📦 Per-Module Migration Workflow

When Copilot receives **"migrate the [X] module"**, execute exactly these steps:

### STEP 0 — Module Discovery (Always Run First)

Copilot must ask for or locate these files before writing any code:

```
□ List all Angular files in the module:
    apps/shell/src/app/features/[module-name]/
    libs/feature-[module-name]/src/

□ Identify:
    - Entry component (routed component)
    - Child/presentational components
    - Services used
    - NgRx feature state (actions, reducers, effects, selectors)
    - Pipes used
    - Route guards
    - AG Grid instances
    - PrimeNG components used
    - External API endpoints called
    - Shared lib dependencies

□ Map to React equivalents before writing any code
```

### STEP 1 — Scaffold React Feature Lib

```bash
# Run this NX command first
nx g @nx/react:library \
  --name=feature-[module-name] \
  --directory=libs/feature-[module-name] \
  --style=module.scss \
  --unitTestRunner=vitest \
  --bundler=vite

# Creates:
# libs/feature-[module-name]/
#   src/
#     lib/
#       components/   ← Presentational components
#       containers/   ← Connected/smart components
#       hooks/        ← Custom hooks (data fetching, local state)
#       store/        ← RTK slices (if module has its own state)
#       types/        ← Module-specific TypeScript interfaces
#       utils/        ← Module-specific pure functions
#     index.ts        ← Public API barrel
```

### STEP 2 — Module File Generation Order

Copilot MUST migrate files in this exact dependency order (bottom-up):

```
1. types/              ← TypeScript interfaces (copy from Angular, strip decorators)
2. utils/              ← Pure functions (pipes, formatters, validators)
3. store/              ← RTK slice (from NgRx feature module)
4. hooks/              ← React Query hooks (from Angular services)
5. components/         ← Presentational components (leaf nodes first)
6. containers/         ← Smart/connected components (depend on hooks + store)
7. [module].routes.tsx ← React Router route config (from Angular routes)
8. index.ts            ← Barrel exports
9. *.spec.tsx          ← Test files (100% coverage)
```

### STEP 3 — Feature Flag Gating (Safe Rollout)

Every migrated React module MUST be behind a feature flag during transition:

```typescript
// libs/util/src/lib/feature-flags/flags.ts
export type FeatureFlag =
  | 'USE_REACT_PRODUCTS'
  | 'USE_REACT_ORDERS'
  | 'USE_REACT_ADMIN'
  | 'USE_REACT_REPORTING';

const FLAGS: Record<FeatureFlag, boolean> = {
  USE_REACT_PRODUCTS:  import.meta.env.VITE_FF_REACT_PRODUCTS === 'true',
  USE_REACT_ORDERS:    import.meta.env.VITE_FF_REACT_ORDERS === 'true',
  USE_REACT_ADMIN:     import.meta.env.VITE_FF_REACT_ADMIN === 'true',
  USE_REACT_REPORTING: import.meta.env.VITE_FF_REACT_REPORTING === 'true',
};

export const isEnabled = (flag: FeatureFlag): boolean => FLAGS[flag];
```

```typescript
// Angular routing — conditionally load React or Angular feature
{
  path: 'products',
  loadChildren: isEnabled('USE_REACT_PRODUCTS')
    ? () => import('./react-bridge/products-react-bridge.module')
            .then(m => m.ProductsReactBridgeModule)
    : () => import('./features/products/products.module')
            .then(m => m.ProductsModule),
}
```

---

## 📋 Per-Module Checklists

### § PRE — Pre-Migration Checklist

Before writing a single line of React:

```
□ SOURCE AUDIT
  □ All Angular component files listed (*.component.ts, *.component.html, *.component.scss)
  □ All services used by this module identified
  □ All NgRx actions/reducers/effects/selectors for this module identified
  □ All routes in this module mapped (including child routes, guards, resolvers)
  □ All third-party components identified (AG Grid, PrimeNG, custom lib)
  □ API endpoints called by this module documented
  □ Unit test coverage of Angular module confirmed (baseline)

□ DEPENDENCY CHECK
  □ No circular dependencies to other unmigrated modules
  □ Shared libs this module depends on are already migrated OR are pure TS
  □ If shared lib needs migration first → flag and pause, migrate dependency first

□ SCAFFOLD
  □ NX library or app scaffolded for this feature
  □ Vitest config with 100% coverage thresholds in place
  □ ESLint + Prettier config inherited from workspace
  □ Feature flag added to flags.ts and .env.example
```

### § POST — Post-Migration Checklist

Before marking a module as DONE:

```
□ FUNCTIONALITY
  □ All routes from Angular module exist in React router config
  □ All route guards have React equivalents (RequireAuth, RequireRole, etc.)
  □ All Angular component @Inputs have corresponding React props
  □ All Angular component @Outputs have corresponding onXxx callback props
  □ All service API calls are covered by React Query hooks
  □ All NgRx state has RTK slice equivalents
  □ All AG Grid column defs and cell renderers migrated
  □ All PrimeNG components replaced with PrimeReact equivalents
  □ All pipes converted to utility functions or useMemo
  □ All form validations (Angular Reactive Forms → React Hook Form)

□ QUALITY
  □ 100% line/branch/function/statement coverage via Vitest
  □ Zero ESLint errors or warnings
  □ SonarQube scan: zero Critical, zero Major issues
  □ No 'any' types in migrated files
  □ No inline object/array literals passed as props (causes re-renders)
  □ All callbacks wrapped in useCallback
  □ All derived values wrapped in useMemo
  □ React.memo applied to all components

□ SECURITY
  □ No dangerouslySetInnerHTML without DOMPurify
  □ No sensitive data in localStorage via Zustand persist
  □ All API calls use the shared apiClient (interceptors applied)
  □ Environment variables accessed via import.meta.env.VITE_*

□ INTEGRATION
  □ Feature flag configured in all environments
  □ migrationBus subscriptions set up for auth/theme/notifications
  □ Angular shell can navigate to and from the React module
  □ Browser back/forward works correctly across the boundary
  □ Page title updates correctly (document.title or React Router handle)
  □ Deep links work (bookmarking a React sub-route and refreshing)

□ ACCESSIBILITY
  □ All interactive elements have accessible labels
  □ Keyboard navigation works (Tab order, Enter/Space on buttons)
  □ Screen reader tested for key flows
  □ Color contrast passes WCAG 2.1 AA
```

### § REPORT — Module Migration Report Template

After each module migration, Copilot outputs this summary:

```markdown
## Module Migration Report: [MODULE_NAME]

### Files Migrated
| Angular Source | React Output | Status |
|---|---|---|
| products.component.ts | containers/ProductsContainer.tsx | ✅ |
| product-card.component.ts | components/ProductCard/ProductCard.tsx | ✅ |
| products.service.ts | hooks/useProducts.ts | ✅ |
| products.actions.ts / .reducer.ts / .effects.ts | store/products.slice.ts | ✅ |
| currency-format.pipe.ts | utils/formatCurrency.ts | ✅ |

### State Changes
- NgRx feature `products` → RTK slice `productsSlice`
- 3 BehaviorSubjects → 2 Zustand atoms + 1 React Query cache

### API Contracts (Unchanged)
- GET /api/products ✅
- POST /api/products/:id/archive ✅

### Test Coverage
| Metric | Angular (Before) | React (After) |
|---|---|---|
| Lines | 100% | 100% |
| Branches | 100% | 100% |
| Functions | 100% | 100% |

### Risks / Notes
- ProductGrid uses AG Grid Server-Side Row Model — verify license key in React env
- AdminProductsView has complex form validation — migrated to React Hook Form + Zod

### Feature Flag
- Flag: `USE_REACT_PRODUCTS`
- Env var: `VITE_FF_REACT_PRODUCTS=true`
- Enable in: dev ✅ | staging ✅ | prod ❌ (pending QA sign-off)
```

---

## 🗺️ Module Dependency Graph (Migration Order)

Copilot must respect this ordering: always migrate **leaves before consumers**.

```
Step 1:  libs/util          ← Pure TS (no migration needed — verify only)
Step 2:  libs/domain        ← Pure TS (no migration needed — verify only)
Step 3:  libs/ui            ← Shared component library (migrate first, everything depends on it)
Step 4:  libs/data-access   ← Shared API hooks and RTK store (migrate before features)
         │
         ├── Step 5a: libs/feature-auth        ← Login, session (other features depend on auth)
         ├── Step 5b: libs/feature-[leaf-A]    ← No deps on other features
         ├── Step 5c: libs/feature-[leaf-B]    ← No deps on other features
         │
         ├── Step 6a: libs/feature-[mid-A]     ← Depends on leaf-A
         ├── Step 6b: libs/feature-[mid-B]     ← Depends on leaf-B
         │
         └── Step 7:  apps/shell               ← Last: replace Angular shell with React shell
```

**How to determine dependency order:**

```bash
# NX can generate the dep graph for you
nx dep-graph

# Or show deps for a specific lib
nx show project feature-orders --json | jq '.dependencies'
```

---

## 🔁 React Hook Form: Replacing Angular Reactive Forms

Angular Reactive Forms has the most complex 1-to-1 mapping. Use this template:

```typescript
// ─── Angular ──────────────────────────────────────
this.form = this.fb.group({
  name:     ['', [Validators.required, Validators.minLength(2)]],
  email:    ['', [Validators.required, Validators.email]],
  role:     ['viewer', Validators.required],
  notifyOn: this.fb.array([]),
});

// ─── React: React Hook Form + Zod ────────────────
import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const userFormSchema = z.object({
  name:     z.string().min(2, 'Name must be at least 2 characters'),
  email:    z.string().email('Invalid email address'),
  role:     z.enum(['viewer', 'editor', 'admin']),
  notifyOn: z.array(z.string()).min(0),
});

type UserFormValues = z.infer<typeof userFormSchema>;

function UserForm({ onSubmit }: { onSubmit: (values: UserFormValues) => void }) {
  const {
    register,
    handleSubmit,
    control,
    formState: { errors, isSubmitting, isDirty },
  } = useForm<UserFormValues>({
    resolver: zodResolver(userFormSchema),
    defaultValues: { name: '', email: '', role: 'viewer', notifyOn: [] },
  });

  const { fields, append, remove } = useFieldArray({ control, name: 'notifyOn' });

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate>
      <div className={styles.field}>
        <label htmlFor="name">Name</label>
        <input id="name" {...register('name')} aria-invalid={!!errors.name} />
        {errors.name && <span role="alert" className={styles.error}>{errors.name.message}</span>}
      </div>

      <div className={styles.field}>
        <label htmlFor="email">Email</label>
        <input id="email" type="email" {...register('email')} aria-invalid={!!errors.email} />
        {errors.email && <span role="alert" className={styles.error}>{errors.email.message}</span>}
      </div>

      <button type="submit" disabled={isSubmitting || !isDirty}>
        {isSubmitting ? 'Saving…' : 'Save'}
      </button>
    </form>
  );
}
```

### Angular Validator → Zod Schema Mapping

| Angular Validator | Zod Equivalent |
|---|---|
| `Validators.required` | `.min(1)` or `.nonempty()` |
| `Validators.minLength(n)` | `.min(n)` |
| `Validators.maxLength(n)` | `.max(n)` |
| `Validators.email` | `.email()` |
| `Validators.pattern(regex)` | `.regex(regex)` |
| `Validators.min(n)` | `z.number().min(n)` |
| `Validators.max(n)` | `z.number().max(n)` |
| Custom `AbstractControl` validator | `z.string().refine(fn, msg)` |
| Cross-field validator | `z.object({...}).refine(fn, { path: ['field'] })` |

---

## 🔄 Rollback Plan Per Module

Each migrated module MUST have a rollback path:

```typescript
// Angular routing — instant rollback: set env var to false
{
  path: 'products',
  loadChildren: isEnabled('USE_REACT_PRODUCTS')
    ? () => import('./react-bridge/products-react-bridge.module').then(...)
    : () => import('./features/products/products.module').then(...),
}
```

**Rollback procedure:**

```bash
# 1. Set feature flag to false (no redeploy needed with runtime flags)
VITE_FF_REACT_PRODUCTS=false

# 2. If using hardcoded flags, revert ONE line in flags.ts
USE_REACT_PRODUCTS: false,

# 3. Redeploy Angular shell only — React MFE stays deployed but unused
# 4. Zero user impact — Angular module still exists, never deleted until flag is permanent
```

**Angular source files are NEVER deleted until:**
- React module has been in production for ≥ 2 sprint cycles
- Zero rollback events in that period
- QA sign-off on React module
- Feature flag permanently enabled

---

## 📊 Migration Progress Tracker

Maintain this in `MIGRATION.md` at the workspace root:

```markdown
# Migration Progress

| Module | Angular Lines | React Lines | Coverage | Flag | Status |
|---|---|---|---|---|---|
| libs/util | 1,200 | 1,200 | 100% | N/A | ✅ Done |
| libs/domain | 800 | 800 | 100% | N/A | ✅ Done |
| libs/ui | 5,400 | — | — | — | 🔄 In Progress |
| libs/data-access | 3,100 | — | — | — | ⏳ Queued |
| feature-auth | 2,200 | — | — | — | ⏳ Queued |
| feature-products | 4,800 | — | — | — | ⏳ Queued |
| feature-orders | 6,200 | — | — | — | ⏳ Queued |
| feature-reporting | 3,700 | — | — | — | ⏳ Queued |
| apps/shell | 2,100 | — | — | — | ⏳ Queued (Last) |

**Total**: 29,500 Angular lines | Migrated: 4.1% | Est. completion: —
```

---

## 💬 Copilot Trigger Phrases

Use these exact phrases to activate specific migration behaviors:

| Phrase | Copilot Action |
|---|---|
| `"migrate the [X] module"` | Full module migration (all steps) |
| `"migrate component [X]"` | Single component only |
| `"migrate service [X]"` | Service → React Query hook |
| `"migrate store [X]"` | NgRx feature → RTK slice |
| `"migrate routes [X]"` | Angular routes → React Router config |
| `"migrate forms in [X]"` | Angular Reactive Forms → RHF + Zod |
| `"audit [X] before migration"` | Run PRE checklist only, output findings |
| `"generate migration report for [X]"` | Output REPORT template filled in |
| `"check rollback for [X]"` | Verify feature flag + Angular source still intact |
| `"what should I migrate next?"` | Output next module from dependency graph |

---

## ⚠️ Incremental Migration Anti-Patterns

These are the most common ways incremental migrations fail. Copilot must flag these if detected:

| Anti-Pattern | Risk | Correct Approach |
|---|---|---|
| Deleting Angular source before React is in prod | No rollback possible | Keep Angular source until 2-sprint soak period |
| Sharing mutable JS objects between Angular and React | State desync, hard bugs | Use migrationBus or localStorage bridge only |
| Two React versions loaded (one in shell, one in MFE) | Hook rule violations | Force singleton: `shared: { react: { singleton: true } }` |
| Migrating shell/layout first | Everything else breaks | Always migrate leaves first, shell last |
| Mixing Angular Change Detection with React state | Unpredictable renders | Strict framework boundary — no Angular DI inside React |
| Rewriting business logic while migrating | Regression risk doubles | Translate first, optimize in a separate PR |
| Merging Angular and React state stores | Impossible to roll back | Keep separate stores, bridge with events |
| Using `any` to speed up migration | Tech debt, Sonar failures | Type everything, even if it slows migration |

---

*Addendum v1.0 | Strategy: Strangler Fig + NX Module Federation | Pattern: Route Takeover (default) → MFE (advanced)*
