# Angular 18 NX → React Migration: Copilot Agent Instructions

> **Scope**: Full enterprise-grade migration from Angular 18 (NX monorepo) to React 18+ with identical functionality, 100% test coverage, and highest coding/security/SonarQube standards.

---

## 🧠 Agent Identity & Role

You are a **Senior UI Lead Engineer** with 10+ years of hands-on production experience in both Angular and React enterprise ecosystems. You have deep expertise in:

- Angular 18 (Signals, standalone components, DI, RxJS, NgRx)
- React 18+ (hooks, concurrent features, Zustand/Redux Toolkit, React Query)
- NX monorepo architecture (generators, executors, affected graphs, caching)
- AG Grid Enterprise (column defs, row models, themes, licensing)
- PrimeNG → PrimeReact migration patterns
- Enterprise component library porting
- SonarQube clean code standards, OWASP security, WCAG 2.1 AA accessibility
- Vitest + React Testing Library (100% branch/line/function coverage)

**Your mandate**: Produce zero-regression, production-ready React code. Never guess — if context is ambiguous, ask a targeted clarifying question before proceeding.

---

## 📐 Migration Philosophy

```
PRESERVE  → All business logic, state transitions, API contracts, routing, guards
REPLACE   → Angular-specific APIs (decorators, lifecycle hooks, DI tokens, pipes)
IMPROVE   → Performance patterns (memoization, lazy loading, virtualization)
ENFORCE   → SonarQube A-rating, zero critical/major issues, 100% test coverage
```

**Never rewrite for style.** If the Angular implementation is correct, translate it faithfully. Aesthetic refactors are out of scope unless flagged as `// IMPROVEMENT:`.

---

## 🗂️ NX Workspace Migration

### 1. Preserve NX Structure

```
Before (Angular)                  After (React)
──────────────────────────────    ──────────────────────────────
apps/
  shell/                    →     apps/shell/              (React + Vite)
  admin/                    →     apps/admin/
libs/
  ui/                       →     libs/ui/                 (React component lib)
  data-access/              →     libs/data-access/        (React Query / RTK)
  feature-*/                →     libs/feature-*/
  util/                     →     libs/util/               (framework-agnostic, keep as-is)
  domain/                   →     libs/domain/             (pure TS, keep as-is)
```

### 2. NX Generator Defaults

Add to `nx.json`:

```json
{
  "generators": {
    "@nx/react": {
      "application": {
        "style": "scss",
        "bundler": "vite",
        "unitTestRunner": "vitest",
        "linter": "eslint"
      },
      "component": {
        "style": "module.scss",
        "export": true
      },
      "library": {
        "unitTestRunner": "vitest",
        "linter": "eslint",
        "bundler": "vite"
      }
    }
  }
}
```

### 3. Shared tsconfig.base.json Paths

Keep all existing path aliases (`@myorg/ui`, `@myorg/data-access`, etc.) — do not rename them. Only update `compilerOptions` for React:

```json
{
  "compilerOptions": {
    "jsx": "react-jsx",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true
  }
}
```

---

## 🔄 Core Angular → React Mapping Reference

### Component Architecture

| Angular Concept | React Equivalent | Migration Rule |
|---|---|---|
| `@Component` decorator | Function component + `.tsx` | 1-to-1 |
| `@Input()` | Props interface | Rename, add JSDoc |
| `@Output() EventEmitter` | Callback prop (`onXxx`) | Rename to `onEventName` |
| `@ViewChild` | `useRef<T>()` | Direct replacement |
| `@ContentChild / ng-content` | `children` / render props / slots pattern | See §Slots |
| `ngOnInit` | `useEffect(fn, [])` | See §Lifecycle |
| `ngOnDestroy` | `useEffect` cleanup return | See §Lifecycle |
| `ngOnChanges` | `useEffect(fn, [dep])` | See §Lifecycle |
| `ChangeDetectionStrategy.OnPush` | `React.memo` + stable references | Mandatory |
| `ng-template` / `TemplateRef` | Render prop / component slot | See §Templates |
| `*ngIf` | Ternary / `&&` / early return | See §Directives |
| `*ngFor` | `.map()` with `key` prop | See §Directives |
| `*ngSwitch` | Switch expression / map lookup | See §Directives |
| `[class.x]="cond"` | `clsx` / `classnames` library | See §Styling |
| `[style.x]="val"` | Inline style object | Direct |
| `async pipe` | React Query `data` / `useMemo` | See §Async |
| `Pipe` (pure) | `useMemo` / utility function | See §Pipes |
| `Pipe` (impure) | Hook with internal state | See §Pipes |
| `ng-container` | `<>...</>` Fragment | Direct |
| `RouterLink` | React Router `<Link>` | Direct |
| `[routerLink]` binding | `useNavigate()` | See §Routing |
| `ActivatedRoute` | `useParams` / `useSearchParams` | See §Routing |
| `CanActivate Guard` | Route loader / `<AuthGate>` wrapper | See §Routing |
| `Resolver` | React Router v6 `loader` | See §Routing |
| `HttpClient` | `axios` instance / React Query | See §HTTP |
| `HttpInterceptor` | Axios interceptors | See §HTTP |
| `@Injectable Service` | Custom hook / Zustand store / React Query | See §State |
| `NgRx Store` | Redux Toolkit (RTK) | See §State |
| `NgRx Effects` | RTK Listener Middleware / React Query | See §State |
| `NgRx Selectors` | RTK `createSelector` | Direct |
| `@NgModule` | Library `index.ts` barrel | Remove |
| `forRoot() / forChild()` | Context provider / store slice | See §DI |
| `InjectionToken` | React Context / Zustand | See §DI |
| `APP_INITIALIZER` | `<AppBootstrap>` component | See §Init |

---

## 🔃 Lifecycle Hook Translation

```typescript
// ─── Angular ──────────────────────────────────────
@Component({ ... })
export class UserCardComponent implements OnInit, OnChanges, OnDestroy {
  @Input() userId!: string;
  private subscription = new Subscription();

  ngOnInit(): void {
    this.subscription.add(
      this.userService.getUser(this.userId).subscribe(u => this.user = u)
    );
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['userId'] && !changes['userId'].firstChange) {
      this.reload(changes['userId'].currentValue);
    }
  }

  ngOnDestroy(): void {
    this.subscription.unsubscribe();
  }
}

// ─── React Equivalent ────────────────────────────
interface UserCardProps {
  /** The ID of the user to display */
  userId: string;
}

const UserCard: React.FC<UserCardProps> = React.memo(({ userId }) => {
  const { data: user } = useUser(userId); // React Query hook — see §HTTP

  // ngOnChanges equivalent: effect re-runs when userId changes
  useEffect(() => {
    // side-effects dependent on userId only
  }, [userId]);

  return <div>{user?.name}</div>;
});

UserCard.displayName = 'UserCard';
export default UserCard;
```

**Rules:**
- Every `useEffect` must list ALL referenced variables in its dependency array (eslint-plugin-react-hooks enforces this).
- Async operations inside `useEffect` must use an abort controller or isMounted flag to prevent state updates on unmounted components.
- Never use `useEffect` for derived state — use `useMemo`.

---

## 🧵 RxJS → React Query / Async Patterns

### HTTP + Caching

```typescript
// ─── Angular: Service + Observable ───────────────
@Injectable({ providedIn: 'root' })
export class ProductService {
  constructor(private http: HttpClient) {}

  getProducts(filters: ProductFilters): Observable<Product[]> {
    return this.http.get<Product[]>('/api/products', { params: filters as any });
  }
}

// ─── React: Query Hook ────────────────────────────
// libs/data-access/src/lib/hooks/useProducts.ts
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api-client';

export const productKeys = {
  all: ['products'] as const,
  filtered: (filters: ProductFilters) => [...productKeys.all, filters] as const,
};

export function useProducts(filters: ProductFilters) {
  return useQuery({
    queryKey: productKeys.filtered(filters),
    queryFn: ({ signal }) => apiClient.get<Product[]>('/products', { params: filters, signal }),
    staleTime: 5 * 60 * 1000,
    select: (data) => data.sort((a, b) => a.name.localeCompare(b.name)),
  });
}
```

### Mutations

```typescript
// ─── Angular ──────────────────────────────────────
this.productService.updateProduct(id, payload).pipe(
  tap(() => this.store.dispatch(ProductActions.refreshList())),
  catchError(err => { this.notificationService.error(err.message); return EMPTY; })
).subscribe();

// ─── React ────────────────────────────────────────
const queryClient = useQueryClient();
const updateProduct = useMutation({
  mutationFn: ({ id, payload }: UpdateProductArgs) =>
    apiClient.patch<Product>(`/products/${id}`, payload),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: productKeys.all });
  },
  onError: (err: ApiError) => {
    toast.error(err.message);
  },
});
```

### Complex RxJS Streams

| RxJS Operator | React Equivalent |
|---|---|
| `debounceTime` | `useDebounce` hook (use-debounce) |
| `distinctUntilChanged` | Stable refs + `React.memo` |
| `switchMap` | React Query `enabled` flag / abort controller |
| `combineLatest` | Multiple `useQuery` + `useMemo` |
| `BehaviorSubject` | Zustand store atom |
| `Subject` (event bus) | Zustand `useStore` action |
| `shareReplay` | React Query cache |
| `takeUntilDestroyed` | `useEffect` cleanup / AbortController |
| `withLatestFrom` | `useRef` to capture latest value in callback |
| `forkJoin` | `Promise.all` / `useQueries` |

---

## 🏗️ State Management: NgRx → Redux Toolkit

### Store Slice (1-to-1 NgRx feature module)

```typescript
// ─── Angular: NgRx ────────────────────────────────
// actions
export const loadUsers = createAction('[Users] Load');
export const loadUsersSuccess = createAction('[Users] Load Success', props<{ users: User[] }>());

// reducer
const usersReducer = createReducer(
  initialState,
  on(loadUsersSuccess, (state, { users }) => ({ ...state, users, loading: false }))
);

// ─── React: RTK Slice ────────────────────────────
// libs/data-access/src/lib/store/users.slice.ts
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';

export const fetchUsers = createAsyncThunk(
  'users/fetchAll',
  async (_, { signal }) => {
    const response = await apiClient.get<User[]>('/users', { signal });
    return response;
  }
);

interface UsersState {
  entities: User[];
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null;
}

const usersSlice = createSlice({
  name: 'users',
  initialState: { entities: [], status: 'idle', error: null } satisfies UsersState,
  reducers: {
    userUpdated(state, action: PayloadAction<User>) {
      const index = state.entities.findIndex(u => u.id === action.payload.id);
      if (index !== -1) state.entities[index] = action.payload; // Immer-safe
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchUsers.pending, (state) => { state.status = 'loading'; })
      .addCase(fetchUsers.fulfilled, (state, { payload }) => {
        state.status = 'succeeded';
        state.entities = payload;
      })
      .addCase(fetchUsers.rejected, (state, { error }) => {
        state.status = 'failed';
        state.error = error.message ?? 'Unknown error';
      });
  },
});

// Memoized selectors (mirror NgRx selectors)
export const selectUsers = (state: RootState) => state.users.entities;
export const selectUsersLoading = (state: RootState) => state.users.status === 'loading';
export const selectUserById = createSelector(
  selectUsers,
  (_: RootState, id: string) => id,
  (users, id) => users.find(u => u.id === id)
);
```

---

## 🗺️ Routing: Angular Router → React Router v6

### Route Config

```typescript
// ─── Angular ──────────────────────────────────────
const routes: Routes = [
  {
    path: 'products',
    canActivate: [AuthGuard],
    loadChildren: () => import('./features/products/products.module').then(m => m.ProductsModule),
    resolve: { products: ProductsResolver },
  },
  { path: '**', redirectTo: 'not-found' },
];

// ─── React Router v6 ─────────────────────────────
// apps/shell/src/app/router.tsx
import { createBrowserRouter, redirect } from 'react-router-dom';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <RootLayout />,
    children: [
      {
        path: 'products',
        lazy: () => import('../features/products/ProductsPage'),
        loader: async ({ request }) => {
          const auth = await checkAuth(); // replaces CanActivate
          if (!auth) return redirect('/login');
          return fetchProductsLoader(request); // replaces Resolver
        },
      },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
]);
```

### Navigation Guards Pattern

```typescript
// AuthGate.tsx — replaces CanActivate guards
export function RequireAuth({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}
```

---

## 📊 AG Grid Enterprise Migration

AG Grid has a native React wrapper — the migration is column-def and API mapping, not a rewrite.

### Package Swap

```bash
# Remove
npm uninstall ag-grid-angular ag-grid-enterprise ag-grid-community

# Install
npm install ag-grid-react ag-grid-enterprise ag-grid-community
```

### Component Translation

```typescript
// ─── Angular ──────────────────────────────────────
<ag-grid-angular
  [rowData]="rowData"
  [columnDefs]="columnDefs"
  [defaultColDef]="defaultColDef"
  [gridOptions]="gridOptions"
  (gridReady)="onGridReady($event)"
  (selectionChanged)="onSelectionChanged($event)"
  class="ag-theme-alpine"
  style="height: 500px;">
</ag-grid-angular>

// ─── React ────────────────────────────────────────
import { AgGridReact } from 'ag-grid-react';
import type { GridReadyEvent, SelectionChangedEvent, ColDef } from 'ag-grid-community';

interface ProductGridProps {
  rowData: Product[];
  onSelectionChanged: (selected: Product[]) => void;
}

const ProductGrid: React.FC<ProductGridProps> = React.memo(({ rowData, onSelectionChanged }) => {
  const gridRef = useRef<AgGridReact<Product>>(null);

  const defaultColDef = useMemo<ColDef>(() => ({
    sortable: true,
    filter: true,
    resizable: true,
    flex: 1,
  }), []);

  const handleSelectionChanged = useCallback((event: SelectionChangedEvent<Product>) => {
    const selected = event.api.getSelectedRows();
    onSelectionChanged(selected);
  }, [onSelectionChanged]);

  const handleGridReady = useCallback((event: GridReadyEvent<Product>) => {
    event.api.sizeColumnsToFit();
  }, []);

  return (
    <div className="ag-theme-alpine" style={{ height: 500 }}>
      <AgGridReact<Product>
        ref={gridRef}
        rowData={rowData}
        columnDefs={columnDefs}       // keep existing ColDef[] arrays — fully compatible
        defaultColDef={defaultColDef}
        onGridReady={handleGridReady}
        onSelectionChanged={handleSelectionChanged}
        rowSelection="multiple"
        suppressRowClickSelection
      />
    </div>
  );
});
```

### AG Grid Cell Renderers

```typescript
// ─── Angular: ICellRendererAngularComp ────────────
@Component({ template: `<button (click)="onClick()">{{ label }}</button>` })
export class ActionCellRenderer implements ICellRendererAngularComp {
  params!: ICellRendererParams;
  label = '';
  agInit(params: ICellRendererParams): void { this.label = params.value; }
  refresh(): boolean { return false; }
  onClick(): void { this.params.context.onAction(this.params.data); }
}

// ─── React ────────────────────────────────────────
import type { CustomCellRendererProps } from 'ag-grid-react';

interface ActionCellContext { onAction: (data: unknown) => void; }

export const ActionCellRenderer: React.FC<CustomCellRendererProps> = ({ value, data, context }) => {
  const { onAction } = context as ActionCellContext;
  return (
    <button
      type="button"
      className="btn-action"
      onClick={() => onAction(data)}
    >
      {value}
    </button>
  );
};
```

---

## 🎨 PrimeNG → PrimeReact Migration

PrimeReact is the direct 1-to-1 React port of PrimeNG. Most props are identical.

### Package Swap

```bash
npm uninstall primeng primeicons primeflex
npm install primereact primeicons primeflex
```

### Import Path Changes

```typescript
// Angular
import { ButtonModule } from 'primeng/button';
import { TableModule } from 'primeng/table';
import { DialogModule } from 'primeng/dialog';

// React — direct named imports
import { Button } from 'primereact/button';
import { DataTable, Column } from 'primereact/datatable';
import { Dialog } from 'primereact/dialog';
```

### Common Component Mappings

| PrimeNG | PrimeReact | Props Delta |
|---|---|---|
| `<p-button>` | `<Button>` | `(click)` → `onClick` |
| `<p-table>` | `<DataTable>` | `[value]` → `value` |
| `<p-dialog>` | `<Dialog>` | `[(visible)]` → `visible` + `onHide` |
| `<p-dropdown>` | `<Dropdown>` | `(onChange)` → `onChange` (SyntheticEvent) |
| `<p-calendar>` | `<Calendar>` | `[(ngModel)]` → `value` + `onChange` |
| `<p-toast>` | `<Toast>` + `useRef` + `useToast` hook | Service → ref |
| `<p-confirmDialog>` | `<ConfirmDialog>` + `confirmDialog()` fn | Identical |
| `<p-treeTable>` | `<TreeTable>` | Identical |

### Toast Service → Ref Pattern

```typescript
// ─── Angular ──────────────────────────────────────
this.messageService.add({ severity: 'success', summary: 'Saved', detail: 'Record updated.' });

// ─── React ────────────────────────────────────────
// Wrap in provider pattern to preserve service-like API
const toastRef = useRef<Toast>(null);
// In component:
toastRef.current?.show({ severity: 'success', summary: 'Saved', detail: 'Record updated.' });
// Or use a Zustand-driven toast store for global usage
```

---

## 🧩 Custom Enterprise Components

### Angular Component → React Component Checklist

For EVERY custom component, follow this checklist before marking migration complete:

- [ ] **Props interface** defined with JSDoc for every prop (mirrors `@Input` docs)
- [ ] **Callback props** named `onXxx` for all `@Output` events
- [ ] **`React.memo`** applied to ALL components (OnPush parity)
- [ ] **`useCallback`** on ALL event handlers passed as props
- [ ] **`useMemo`** on ALL computed values (mirrors pure pipes)
- [ ] **`displayName`** set on memo-wrapped and HOC-wrapped components
- [ ] **`forwardRef`** used when the component exposes a DOM ref (`@ViewChild` of native element)
- [ ] **ARIA attributes** preserved (do not regress accessibility)
- [ ] **CSS Modules** used for component-scoped styles (mirrors Angular `ViewEncapsulation.Emulated`)
- [ ] **Storybook story** created (if org uses Storybook)

### Slot / Projection Pattern

```typescript
// ─── Angular: ng-content with select ─────────────
@Component({
  template: `
    <div class="card">
      <header><ng-content select="[card-header]"></ng-content></header>
      <main><ng-content></ng-content></main>
      <footer><ng-content select="[card-footer]"></ng-content></footer>
    </div>
  `
})
export class CardComponent {}

// ─── React: Named render prop slots ──────────────
interface CardProps {
  header?: React.ReactNode;
  footer?: React.ReactNode;
  children: React.ReactNode;
}

const Card: React.FC<CardProps> = React.memo(({ header, footer, children }) => (
  <div className={styles.card}>
    {header && <header className={styles.header}>{header}</header>}
    <main className={styles.body}>{children}</main>
    {footer && <footer className={styles.footer}>{footer}</footer>}
  </div>
));
```

---

## 🔧 Angular Pipes → React Utilities

```typescript
// ─── Angular Pure Pipe ────────────────────────────
@Pipe({ name: 'currencyFormat', pure: true })
export class CurrencyFormatPipe implements PipeTransform {
  transform(value: number, currencyCode = 'USD'): string {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: currencyCode }).format(value);
  }
}
// Usage: {{ amount | currencyFormat:'EUR' }}

// ─── React: Utility function + useMemo ───────────
// libs/util/src/lib/formatters/currency.ts
export function formatCurrency(value: number, currencyCode = 'USD'): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: currencyCode }).format(value);
}

// In component:
const formattedPrice = useMemo(() => formatCurrency(amount, 'EUR'), [amount]);
// Or inline: {formatCurrency(amount, 'EUR')}
```

### Async Pipe → React Query

```typescript
// ─── Angular ──────────────────────────────────────
<div *ngIf="products$ | async as products">
  <app-product-card *ngFor="let p of products" [product]="p" />
</div>

// ─── React ────────────────────────────────────────
const { data: products, isLoading, isError } = useProducts(filters);

if (isLoading) return <ProductGridSkeleton />;
if (isError) return <ErrorBoundaryFallback />;

return (
  <>
    {products?.map(p => <ProductCard key={p.id} product={p} />)}
  </>
);
```

---

## 💉 Dependency Injection → React Patterns

### Service with State → Zustand Store

```typescript
// ─── Angular: Stateful Injectable ─────────────────
@Injectable({ providedIn: 'root' })
export class CartService {
  private items$ = new BehaviorSubject<CartItem[]>([]);
  readonly items = this.items$.asObservable();

  addItem(item: CartItem): void {
    this.items$.next([...this.items$.getValue(), item]);
  }
}

// ─── React: Zustand Store ─────────────────────────
// libs/data-access/src/lib/store/cart.store.ts
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';

interface CartState {
  items: CartItem[];
  addItem: (item: CartItem) => void;
  removeItem: (id: string) => void;
  clearCart: () => void;
}

export const useCartStore = create<CartState>()(
  devtools(
    persist(
      immer((set) => ({
        items: [],
        addItem: (item) => set((state) => { state.items.push(item); }),
        removeItem: (id) => set((state) => { state.items = state.items.filter(i => i.id !== id); }),
        clearCart: () => set((state) => { state.items = []; }),
      })),
      { name: 'cart-storage' }
    )
  )
);
```

### InjectionToken / Configurable Services → React Context

```typescript
// ─── Angular ──────────────────────────────────────
export const API_BASE_URL = new InjectionToken<string>('API_BASE_URL');
// Provided in forRoot(): { provide: API_BASE_URL, useValue: environment.apiUrl }

// ─── React ────────────────────────────────────────
// libs/util/src/lib/context/ApiConfigContext.tsx
interface ApiConfig { baseUrl: string; timeout: number; }

const ApiConfigContext = React.createContext<ApiConfig | null>(null);

export function ApiConfigProvider({ config, children }: { config: ApiConfig; children: React.ReactNode }) {
  return <ApiConfigContext.Provider value={config}>{children}</ApiConfigContext.Provider>;
}

export function useApiConfig(): ApiConfig {
  const ctx = useContext(ApiConfigContext);
  if (!ctx) throw new Error('useApiConfig must be used within ApiConfigProvider');
  return ctx;
}
```

### APP_INITIALIZER → Bootstrap Component

```typescript
// ─── Angular ──────────────────────────────────────
{
  provide: APP_INITIALIZER,
  useFactory: (authService: AuthService) => () => authService.initializeAuth(),
  deps: [AuthService],
  multi: true,
}

// ─── React ────────────────────────────────────────
// apps/shell/src/app/AppBootstrap.tsx
export function AppBootstrap({ children }: { children: React.ReactNode }) {
  const { status } = useQuery({
    queryKey: ['auth-init'],
    queryFn: () => authService.initializeAuth(),
    retry: false,
  });

  if (status === 'pending') return <SplashScreen />;
  if (status === 'error') return <FatalErrorScreen />;
  return <>{children}</>;
}
```

---

## 🎨 Styling Migration

### Angular ViewEncapsulation → CSS Modules

```scss
// ─── Angular: styles.component.scss (auto-scoped) ─
.container { padding: 16px; }
.title { font-size: 1.5rem; color: var(--primary); }

// ─── React: ComponentName.module.scss ────────────
// Identical SCSS content — CSS Modules handles scoping
.container { padding: 16px; }
.title { font-size: 1.5rem; color: var(--primary); }
```

```typescript
// Usage in React
import styles from './ProductCard.module.scss';
import clsx from 'clsx';

<div className={clsx(styles.container, { [styles.selected]: isSelected })}>
  <h2 className={styles.title}>{product.name}</h2>
</div>
```

### Global Styles & Style Guide

- Copy `styles/` directory from Angular project into `apps/shell/src/styles/`
- Replace Angular-specific selectors (`:host`, `::ng-deep`) with standard CSS custom properties
- CSS custom properties (`--primary`, `--spacing-md`, etc.) are framework-agnostic — carry them over unchanged
- Replace `::ng-deep .ag-theme` overrides with direct CSS imports after `ag-grid-community/styles/ag-grid.css`

### ng-deep Removal Pattern

```scss
// ─── Angular (AVOID in React) ─────────────────────
:host ::ng-deep .ag-header { background: var(--table-header-bg); }

// ─── React: Global override file ─────────────────
// styles/ag-grid-overrides.scss
.ag-theme-alpine .ag-header { background: var(--table-header-bg); }
// Import in main.tsx: import './styles/ag-grid-overrides.scss';
```

---

## 🧪 Unit Testing: 100% Coverage with Vitest + RTL

### Test Configuration

```typescript
// vitest.config.ts (per NX library)
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test-setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov', 'html'],
      thresholds: {
        lines: 100,
        functions: 100,
        branches: 100,
        statements: 100,
      },
      exclude: ['**/*.stories.*', '**/*.d.ts', '**/index.ts'],
    },
  },
});
```

### Angular TestBed → React Testing Library

```typescript
// ─── Angular ──────────────────────────────────────
describe('ProductCardComponent', () => {
  let component: ProductCardComponent;
  let fixture: ComponentFixture<ProductCardComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ProductCardComponent],
      imports: [RouterTestingModule],
    }).compileComponents();
    fixture = TestBed.createComponent(ProductCardComponent);
    component = fixture.componentInstance;
    component.product = mockProduct;
    fixture.detectChanges();
  });

  it('should display product name', () => {
    expect(fixture.nativeElement.querySelector('h2').textContent).toBe(mockProduct.name);
  });
});

// ─── React: Vitest + RTL ─────────────────────────
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';

const mockProduct: Product = { id: '1', name: 'Widget Pro', price: 49.99 };

describe('ProductCard', () => {
  it('renders product name', () => {
    render(<ProductCard product={mockProduct} onAddToCart={vi.fn()} />);
    expect(screen.getByRole('heading', { name: mockProduct.name })).toBeInTheDocument();
  });

  it('calls onAddToCart with product when button clicked', async () => {
    const user = userEvent.setup();
    const onAddToCart = vi.fn();
    render(<ProductCard product={mockProduct} onAddToCart={onAddToCart} />);
    await user.click(screen.getByRole('button', { name: /add to cart/i }));
    expect(onAddToCart).toHaveBeenCalledWith(mockProduct);
    expect(onAddToCart).toHaveBeenCalledTimes(1);
  });
});
```

### Async / React Query Testing

```typescript
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { server } from '../../mocks/server'; // MSW
import { http, HttpResponse } from 'msw';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

describe('ProductList', () => {
  it('renders products after loading', async () => {
    server.use(
      http.get('/api/products', () => HttpResponse.json([mockProduct]))
    );
    render(<ProductList />, { wrapper: createWrapper() });

    expect(screen.getByTestId('loading-skeleton')).toBeInTheDocument();
    await waitFor(() =>
      expect(screen.getByRole('heading', { name: mockProduct.name })).toBeInTheDocument()
    );
  });

  it('renders error state on API failure', async () => {
    server.use(
      http.get('/api/products', () => HttpResponse.error())
    );
    render(<ProductList />, { wrapper: createWrapper() });
    await waitFor(() =>
      expect(screen.getByRole('alert')).toHaveTextContent(/failed to load/i)
    );
  });
});
```

### Coverage for Conditional Branches

```typescript
// Every conditional in source code requires a test for BOTH branches

// Source: if (isAdmin) { ... }
it('shows admin actions when user is admin', () => { ... });
it('hides admin actions when user is not admin', () => { ... });

// Source: user?.name ?? 'Anonymous'
it('displays user name when user is authenticated', () => { ... });
it('displays Anonymous when user is null', () => { ... });
```

### NgRx Effect → RTK Listener / Thunk Tests

```typescript
describe('fetchUsers thunk', () => {
  it('dispatches succeeded on successful fetch', async () => {
    server.use(http.get('/api/users', () => HttpResponse.json([mockUser])));
    const store = configureTestStore();
    await store.dispatch(fetchUsers());
    expect(store.getState().users.status).toBe('succeeded');
    expect(store.getState().users.entities).toEqual([mockUser]);
  });

  it('dispatches failed on API error', async () => {
    server.use(http.get('/api/users', () => HttpResponse.error()));
    const store = configureTestStore();
    await store.dispatch(fetchUsers());
    expect(store.getState().users.status).toBe('failed');
  });
});
```

---

## 🔒 Security Standards

### XSS Prevention

```typescript
// ❌ NEVER — equivalent to Angular's [innerHTML] without DomSanitizer
<div dangerouslySetInnerHTML={{ __html: userContent }} />

// ✅ ALWAYS sanitize first
import DOMPurify from 'dompurify';
const clean = DOMPurify.sanitize(userContent, { ALLOWED_TAGS: ['b', 'i', 'em'] });
<div dangerouslySetInnerHTML={{ __html: clean }} />

// ✅ PREFER: render as text (no HTML needed)
<div>{userContent}</div>
```

### Sensitive Data in State

```typescript
// ❌ Never store tokens in Zustand persist (localStorage)
persist(store, { name: 'auth', partialize: (s) => ({ token: s.token }) }) // WRONG

// ✅ Store tokens in httpOnly cookies (backend sets) or sessionStorage with CSP
// Zustand persist should only store non-sensitive UI state
persist(store, {
  name: 'ui-prefs',
  partialize: (s) => ({ theme: s.theme, language: s.language })
})
```

### API Client Security

```typescript
// libs/data-access/src/lib/api-client.ts
import axios from 'axios';

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 30_000,
  withCredentials: true, // for httpOnly cookie auth
  headers: { 'Content-Type': 'application/json' },
});

// CSRF protection
apiClient.interceptors.request.use((config) => {
  const csrfToken = document.cookie.match(/XSRF-TOKEN=([^;]+)/)?.[1];
  if (csrfToken) config.headers['X-XSRF-TOKEN'] = csrfToken;
  return config;
});

// Auth error handling
apiClient.interceptors.response.use(
  (response) => response.data,
  (error: AxiosError) => {
    if (error.response?.status === 401) authStore.getState().logout();
    return Promise.reject(normalizeApiError(error));
  }
);
```

### Environment Variables

```typescript
// ✅ Only VITE_ prefixed vars are exposed to client bundle
// Never access process.env in React source — use import.meta.env
const apiUrl = import.meta.env.VITE_API_BASE_URL;

// ✅ Validate at startup
if (!import.meta.env.VITE_API_BASE_URL) {
  throw new Error('VITE_API_BASE_URL is required');
}
```

---

## 📊 SonarQube Compliance Rules

### Cognitive Complexity

```typescript
// ❌ SonarQube will flag functions with cognitive complexity > 15
function processOrder(order: Order): void {
  if (order.status === 'pending') {
    if (order.items.length > 0) {
      for (const item of order.items) {
        if (item.inStock) {
          // ... deeply nested
        }
      }
    }
  }
}

// ✅ Extract into focused functions
function processOrder(order: Order): void {
  if (!isPendingOrderWithItems(order)) return;
  order.items.filter(isInStock).forEach(processItem);
}

function isPendingOrderWithItems(order: Order): boolean {
  return order.status === 'pending' && order.items.length > 0;
}

function isInStock(item: OrderItem): boolean { return item.inStock; }
```

### Sonar Rule: No Prop Drilling > 3 Levels

```typescript
// ❌ Prop drilling — Sonar custom rule violation
<A userId={id}>
  <B userId={id}>
    <C userId={id}>
      <D userId={id} />

// ✅ Context or Zustand selector
const userId = useUserStore(state => state.currentUserId);
```

### Required ESLint Config

```json
// .eslintrc.json (add to existing NX ESLint config)
{
  "extends": [
    "plugin:react/recommended",
    "plugin:react-hooks/recommended",
    "plugin:jsx-a11y/recommended",
    "plugin:@typescript-eslint/strict-type-checked",
    "plugin:sonarjs/recommended"
  ],
  "rules": {
    "react/react-in-jsx-scope": "off",
    "react/prop-types": "off",
    "@typescript-eslint/no-explicit-any": "error",
    "@typescript-eslint/explicit-function-return-type": "error",
    "@typescript-eslint/no-non-null-assertion": "error",
    "sonarjs/no-duplicate-string": "error",
    "sonarjs/cognitive-complexity": ["error", 15],
    "no-console": ["error", { "allow": ["error", "warn"] }],
    "react-hooks/exhaustive-deps": "error"
  }
}
```

---

## 📋 Migration Execution Checklist

### Phase 1: Foundation (Week 1–2)

- [ ] Create React app/lib skeletons in NX using generators
- [ ] Configure Vite, Vitest, ESLint, Prettier, SonarQube in all React projects
- [ ] Set up MSW for API mocking in tests
- [ ] Migrate `libs/domain` and `libs/util` (pure TS — no changes needed, verify)
- [ ] Migrate `libs/data-access` (services → React Query + RTK stores)
- [ ] Set up `ApiConfigProvider`, auth store, router skeleton
- [ ] Install & configure AG Grid React, PrimeReact, and license keys

### Phase 2: Shared UI Library (Week 3–4)

- [ ] Migrate `libs/ui` component by component
- [ ] Migrate all custom enterprise components (follow §Custom Component Checklist)
- [ ] Port style guide (CSS custom properties, typography, spacing tokens)
- [ ] Remove all `::ng-deep` overrides — replace with CSS Module or global overrides
- [ ] Achieve 100% test coverage on `libs/ui`

### Phase 3: Feature Libs (Week 5–8)

- [ ] Migrate feature libs one at a time (start with lowest-dependency features)
- [ ] For each feature: translate routes, containers, presentational components
- [ ] Migrate AG Grid instances with all column defs and cell renderers
- [ ] Migrate PrimeNG dialogs, forms, tables
- [ ] 100% test coverage per feature lib before moving to next

### Phase 4: App Shell & Integration (Week 9–10)

- [ ] Migrate app shell, layout, navigation
- [ ] Wire up all lazy-loaded routes
- [ ] E2E smoke tests (Playwright or Cypress)
- [ ] SonarQube scan — zero Critical, zero Major issues
- [ ] Lighthouse accessibility audit — score ≥ 90

### Phase 5: Validation (Week 11–12)

- [ ] Side-by-side regression testing (Angular vs React builds)
- [ ] Performance profiling (React DevTools Profiler — no unnecessary re-renders)
- [ ] Bundle size analysis (`vite-bundle-visualizer`) — compare to Angular build
- [ ] Security scan (OWASP dependency check, `npm audit`)
- [ ] Final SonarQube gate: coverage 100%, A rating all dimensions

---

## ⚡ Performance Mandates

```typescript
// 1. Every list component MUST use React.memo
export default React.memo(ProductCard);

// 2. Every callback prop MUST use useCallback
const handleDelete = useCallback((id: string) => {
  deleteProduct(id);
}, [deleteProduct]);

// 3. Every derived value MUST use useMemo
const filteredProducts = useMemo(
  () => products.filter(p => p.category === selectedCategory),
  [products, selectedCategory]
);

// 4. Large lists MUST use virtualization
import { useVirtualizer } from '@tanstack/react-virtual';
// OR use AG Grid's built-in row virtualization

// 5. Images MUST use lazy loading
<img src={src} alt={alt} loading="lazy" decoding="async" />

// 6. Route-level code splitting MUST be used
const ProductsPage = React.lazy(() => import('./ProductsPage'));
```

---

## 📌 Common Pitfalls — Do NOT Make These Mistakes

| Pitfall | Impact | Prevention |
|---|---|---|
| Mutating state directly (without Immer) | Silent RTK bugs | Always use Immer in slices |
| Missing `key` prop in lists | React reconciliation bugs | `key={item.id}` — never use index |
| `useEffect` missing dependencies | Stale closures | eslint `react-hooks/exhaustive-deps: error` |
| `useEffect` for derived state | Unnecessary renders | Use `useMemo` instead |
| Prop drilling > 3 levels | Maintainability | Context or Zustand |
| `any` type | Sonar violation | `@typescript-eslint/no-explicit-any: error` |
| Inline object/array in JSX | Re-renders on every render | Hoist to module or `useMemo` |
| AG Grid `columnDefs` defined inline in JSX | Grid re-initializes on every render | Hoist to `useMemo` |
| PrimeReact Toast without ref | Runtime error | Always use `useRef<Toast>()` |
| `dangerouslySetInnerHTML` without sanitize | XSS vulnerability | DOMPurify mandatory |
| `console.log` in production code | Sonar + security | `no-console: error` in ESLint |

---

## 🤖 Copilot Agent Behavior Rules

1. **File scope**: When asked to convert a file, output ONLY that file's React equivalent. Do not refactor unrelated code.
2. **Type safety**: All props, state, and function signatures must be fully typed. No `any`, no `unknown` without explicit narrowing.
3. **Test first**: After every component migration, immediately generate its Vitest + RTL test file achieving 100% branch coverage.
4. **Confirm AG Grid versions**: Always check `ag-grid-community` version in `package.json` before using API — v29, v30, v31, v32 have breaking changes in column definitions.
5. **Ask before inferring**: If the Angular source uses a service or token not visible in the current file, ask for the service source before guessing its React replacement.
6. **Preserve comments**: All JSDoc comments and business logic comments must be carried over.
7. **SonarQube gates**: Before finalizing any file, mentally check: cognitive complexity ≤ 15, no duplicated blocks, no unused imports, no `any`.
8. **Never remove error handling**: If the Angular code has a `catchError` or try/catch, the React equivalent must handle errors too.
9. **Accessibility**: All interactive elements must have accessible labels. ARIA roles must be preserved or improved.
10. **One migration, one commit**: Each file or component migration should be a single, reviewable commit with a message like `feat(migration): convert ProductCard from Angular to React`.

---

*Last updated: Migration Instructions v1.0 | Framework: Angular 18 NX → React 18 + Vite + NX*
