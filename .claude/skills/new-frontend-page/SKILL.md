---
name: new-frontend-page
description: Scaffold a new React page — page JSX, route in App.jsx, navbar link, API client function, and Vitest test. Use when adding any new page to the SPA.
---

# Add a new frontend page

Follow every step in order. The architecture rule: pages own state and data fetching; child components receive data via props and handle rendering/interaction. API calls go through `apiClient` from `src/api/client.js`, never raw `fetch` or a new axios instance.

## 0. Gather requirements

Before writing code, establish (ask the user if not stated):

- **Page name** — PascalCase component name (e.g. `WatchlistPage`, `ReportsPage`). The file will be `src/pages/<Name>.jsx`.
- **URL path** — the React Router path (e.g. `/watchlist`, `/reports`). Follows the existing pattern in `App.jsx`.
- **Protected or public** — does the user need to be logged in? Portfolio-related pages → protected. Market data, analysis, info pages → public. Default to protected when in doubt.
- **Purpose** — one sentence: what does the page show or let the user do?
- **Data needed** — which API endpoint(s) does the page call, and what does it display? If none, the page is static.
- **Navbar link** — should the page appear in the navigation bar? If yes, where (always visible or only when logged in)?

## 1. Page file — `frontend/src/pages/<Name>.jsx`

### 1a. Static page (no data fetching)

```jsx
import { Navigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';  // omit if public page

function <Name>() {
  const { isLoggedIn } = useAuth();  // omit if public page
  if (!isLoggedIn) return <Navigate to="/login" />;  // omit if public page

  return (
    <div>
      <h1>Page Title</h1>
      {/* page content */}
    </div>
  );
}

export default <Name>;
```

### 1b. Page with data fetching

```jsx
import { useState, useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import { CircularProgress, Box } from '@mui/material';
import { useAuth } from '../AuthContext';  // omit if public page
import apiClient from '../api/client';

function <Name>() {
  const { isLoggedIn } = useAuth();  // omit if public page
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await apiClient.get('/api/<path>/');
        setData(response.data);
      } catch (error) {
        console.error('Failed to load <thing>:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);  // add dependency variables here if the fetch should re-run

  if (!isLoggedIn) return <Navigate to="/login" />;  // omit if public page

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <div>
      <h1>Page Title</h1>
      {/* render data */}
    </div>
  );
}

export default <Name>;
```

**Re-fetching on a dependency** (e.g. when selectedCurrency changes):
```jsx
const [selectedCurrency, setSelectedCurrency] = useState(
  () => localStorage.getItem('preferredCurrency') || 'USD'
);

useEffect(() => {
  // fetch runs again whenever selectedCurrency changes
}, [selectedCurrency]);
```

**Multiple independent fetches:**
```jsx
useEffect(() => {
  const fetchMetrics = async () => { ... };
  fetchMetrics();
}, [selectedCurrency]);

useEffect(() => {
  const fetchHistory = async () => { ... };
  fetchHistory();
}, [selectedCurrency]);
```

**localStorage persistence:**
```jsx
// Read on mount (lazy initial state)
const [value, setValue] = useState(() => localStorage.getItem('key') || 'default');

// Persist on change
const handleChange = (newVal) => {
  setValue(newVal);
  localStorage.setItem('key', newVal);
};
```

### 1c. Page with a form (create/submit action)

```jsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CircularProgress, Box } from '@mui/material';
import apiClient from '../api/client';

function <Name>() {
  const navigate = useNavigate();
  const [fieldA, setFieldA] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!fieldA) {
      alert('Field A is required.');
      return;
    }
    setSubmitting(true);
    try {
      await apiClient.post('/api/<path>/', { field_a: fieldA });
      alert('Saved successfully.');
      navigate('/');
    } catch (error) {
      alert('Error: ' + (error.response?.data?.error || error.message));
    } finally {
      setSubmitting(false);
    }
  };

  if (submitting) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <form onSubmit={handleSubmit}>
      <input value={fieldA} onChange={e => setFieldA(e.target.value)} />
      <button type="submit">Save</button>
    </form>
  );
}

export default <Name>;
```

## 2. Route — `frontend/src/App.jsx`

Open `App.jsx` and add the import at the top with the other page imports:
```jsx
import <Name> from './pages/<Name>';
```

Then add the route inside the `<Routes>` block, grouped with similar routes (protected with protected, public with public):
```jsx
<Route path="/<path>" element={<<Name> />} />
```

Public routes (no auth check at route level — the page component handles it internally if needed) look the same. Do not wrap routes in a `<PrivateRoute>` component — this app handles auth inside each page via `useAuth()`.

## 3. Navbar link — `frontend/src/components/navbar.jsx`

Only add this if the page should appear in the navigation bar. Open `navbar.jsx` and add a `<Link>` in the appropriate position:

```jsx
// Always-visible link
<Link to="/<path>">Page Name</Link>

// Logged-in only link (mirror the pattern used for the portfolio link)
{isLoggedIn && <Link to="/<path>">Page Name</Link>}
```

Match the surrounding element structure (the existing links use `<Link>` from `react-router-dom`). Do not add a new CSS class unless the design requires it — reuse existing navbar link styles.

## 4. API client function — `frontend/src/api/client.js`

Add this step only if the page calls an endpoint that doesn't already have a client helper. If `apiClient.get(...)` is called directly in the page component, skip this step.

To add a named helper for reuse across multiple components:
```js
export const get<Thing> = async (params = {}) => {
  const response = await apiClient.get('/api/<path>/', { params });
  return response.data;
};

export const create<Thing> = async (data) => {
  const response = await apiClient.post('/api/<path>/', data);
  return response.data;
};
```

Import in the page: `import { get<Thing> } from '../api/client';`

Only add named helpers when the same API call will be used in more than one component.

## 5. Child components (if the page is complex)

If the page renders a significant block of UI (a chart, a data table, a complex form section), extract it into a component in `frontend/src/components/` rather than keeping it all in the page file.

**Component that receives data via props** (page fetches, component renders):
```jsx
// frontend/src/components/<FeatureName>.jsx
function <FeatureName>({ data, onAction }) {
  if (!data) return null;
  return (
    <div>
      {/* render data */}
    </div>
  );
}

export default <FeatureName>;
```

**Component that fetches its own data** (self-contained widget):
```jsx
function <FeatureName>({ currency }) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient.get(`/api/<path>/?currency=${currency}`)
      .then(r => setData(r.data))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, [currency]);

  if (loading) return <CircularProgress />;
  return <div>{/* render */}</div>;
}
```

Prefer keeping data fetching in the page component and passing it down as props — it keeps loading/error states coordinated. Only self-fetch in a component when it's a genuinely independent widget (e.g. a stock ticker box).

If the component belongs to a feature group, put it in a subdirectory: `frontend/src/components/<feature>/`. Otherwise, place it directly in `frontend/src/components/`.

## 6. Tests — `frontend/src/<Name>.test.jsx` or `frontend/src/pages/<Name>.test.jsx`

The existing test suite focuses on unit-testing utility functions (see `client.test.js`). For new pages, write a lightweight smoke test covering the key behaviors:

```jsx
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import <Name> from './pages/<Name>';

// Mock the API client
vi.mock('./api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

// Mock AuthContext
vi.mock('./AuthContext', () => ({
  useAuth: () => ({ isLoggedIn: true, login: vi.fn(), logout: vi.fn() }),
}));

import apiClient from './api/client';

describe('<Name>', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders without crashing', () => {
    apiClient.get.mockResolvedValue({ data: [] });
    render(
      <MemoryRouter>
        <<Name> />
      </MemoryRouter>
    );
    expect(document.body).toBeTruthy();
  });

  it('shows loading state initially', () => {
    apiClient.get.mockResolvedValue({ data: [] });
    render(
      <MemoryRouter>
        <<Name> />
      </MemoryRouter>
    );
    // CircularProgress renders during loading
    expect(document.querySelector('[role="progressbar"]')).toBeTruthy();
  });

  it('renders data after fetch', async () => {
    apiClient.get.mockResolvedValue({ data: [{ id: 1, name: 'Test' }] });
    render(
      <MemoryRouter>
        <<Name> />
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(screen.getByText('Test')).toBeTruthy();
    });
  });

  it('redirects to login when not authenticated', () => {
    // Override the mock for this test only
    vi.mocked(useAuth).mockReturnValue({ isLoggedIn: false });
    // ...
  });
});
```

Skip tests for purely static pages with no data fetching — there's nothing to assert beyond a render check, which adds noise without value.

## 7. Verify

```bash
# From frontend/
npm run lint        # zero warnings required
npm run test        # all tests must pass
npm run build       # catches import errors and type issues
```

Then start the dev server and navigate to the new page manually:
```bash
npm run dev
# open http://localhost:5173/<path>
```

Confirm: the page renders, data loads (or form works), loading state appears then clears, and the navbar link (if added) is visible.

## Guardrails

- **Never use raw `fetch()`** — always `apiClient` from `src/api/client.js`. It handles JWT auth and token refresh automatically.
- **Auth guard goes at the top of the component body**, before any hooks that depend on `isLoggedIn`, but after all `useState`/`useEffect` calls (React hooks must not be called conditionally).
- **Don't put business logic in pages** — data transformation (mapping API response to chart format, computing totals) belongs in a helper function or the child component, not inline in `useEffect`.
- **Keep `useEffect` dependency arrays accurate** — if a fetch depends on `selectedCurrency`, list it. An empty `[]` that should have dependencies is a silent staleness bug.
- **`finally` block always sets `setLoading(false)`** — if you only set it in the happy path, the loading spinner stays forever on error.
- **`console.error` on failure, then fall back to empty/default state** — don't leave the page in a broken render state because one fetch failed.
- **One route per page file** — don't render different content on the same URL based on state; create separate routes instead.
