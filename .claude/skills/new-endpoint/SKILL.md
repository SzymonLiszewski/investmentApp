---
name: new-endpoint
description: Scaffold a new REST endpoint following the project's layered architecture — thin view → service/selector → serializer → URL registration → test. Use when adding any new API endpoint to the base, portfolio, or analytics app.
---

# Add a new REST endpoint

Follow every step in order. The architecture rule: views are thin HTTP handlers only — no business logic, no ORM queries. Business logic goes in services; read-only queries go in selectors; serializers handle validation. Dependencies point inward: views → services/selectors → models.

## 0. Gather requirements

Before writing code, establish (ask the user if not stated):

- **App** — which Django app owns this endpoint: `base` (assets, market data, auth), `portfolio` (transactions, composition, value history), or `analytics` (forecasts, ML).
- **Purpose** — one sentence: what does the endpoint do? (read vs write, what data, for whom)
- **HTTP method(s)** — GET / POST / PUT / DELETE.
- **URL path** — e.g. `portfolio/allocation/`, `analytics/sentiment/<str:ticker>/`. Follow existing URL patterns in the app's `urls.py`.
- **Authentication** — `IsAuthenticated` (user-specific data, portfolio operations) or `AllowAny` (public market data, asset search). Default to `IsAuthenticated` when in doubt.
- **View style** — use a **CBV** (`ListCreateAPIView`, etc.) only for standard CRUD with list + create on the same path. Use an **FBV** for everything else (filtering, computed results, custom logic, analytics). Default to FBV.

## 1. Service or selector

Create the business logic or query function before the view — the view imports it, not the other way around.

### Selector (read-only, no side effects)

Add to `backend/<app>/selectors/<name>.py` (create the file if needed):

```python
from typing import Optional
from django.db.models import QuerySet
from ..models import <Model>

def get_<thing>(user, **filters) -> QuerySet:
    return <Model>.objects.filter(owner=user, **filters).order_by('-date')

def get_<thing>_for_date(user, target_date) -> Optional[<Model>]:
    return (
        <Model>.objects
        .filter(owner=user, date__lte=target_date)
        .order_by('-date')
        .first()
    )
```

Export from `backend/<app>/selectors/__init__.py`:
```python
from .<name> import get_<thing>, get_<thing>_for_date
```

### Service (writes, calculations, side effects)

Add a function to `backend/<app>/services/<name>.py` (create the file if needed):

```python
from decimal import Decimal
from rest_framework import serializers
from ..models import <Model>

def do_<action>(user, validated_data: dict) -> <Model>:
    # Raise serializers.ValidationError({'field': 'message'}) for input errors.
    # Raise ValueError for unexpected state.
    # Return the created/updated model instance.
    ...
```

**DI pattern for external fetchers:** if the service needs a price fetcher or other external data source, accept it as an optional parameter defaulting to the factory:

```python
from base.services import get_default_stock_fetcher

def do_<action>(..., stock_fetcher=None):
    stock_fetcher = stock_fetcher or get_default_stock_fetcher()
    ...
```

Never import a concrete provider (e.g. `YFinanceFetcher`) directly in a service — only factory functions.

## 2. Serializer (if the endpoint accepts or returns structured data)

Add to `backend/<app>/serializers.py`. Skip this step for endpoints that return plain dicts or take no structured input.

```python
class <Name>Serializer(serializers.ModelSerializer):
    class Meta:
        model = <Model>
        fields = ['id', 'field_a', 'field_b', ...]
        extra_kwargs = {
            'field_a': {'required': False, 'allow_null': True},
        }

    def validate(self, data):
        # Cross-field validation only — single-field validation uses validate_<field>()
        if data.get('condition') and not data.get('other_field'):
            raise serializers.ValidationError({'other_field': 'Required when condition is set.'})
        return data
```

**Write-only input fields** (used during creation but not returned in the response):
```python
some_input = serializers.CharField(write_only=True, required=False)

def create(self, validated_data):
    validated_data.pop('some_input', None)  # remove before saving
    return super().create(validated_data)
```

**Decimal fields:**
```python
price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
```

## 3. View

### Option A — Function-Based View (default)

Create `backend/<app>/views/<name>.py` (or add to an existing views module):

```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated  # or AllowAny
from rest_framework.response import Response
from datetime import datetime, date

from ..<selectors_or_services> import get_<thing>, do_<action>

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def <endpointName>(request):
    # Parse query params
    param = request.query_params.get('param')
    if not param:
        return Response({'error': 'param is required'}, status=400)

    # Optional: parse date params
    date_str = request.query_params.get('date')
    if date_str:
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)
    else:
        target_date = date.today()

    result = get_<thing>(request.user, ...)  # pass request.user for authenticated endpoints
    return Response(result)
```

**POST body pattern:**
```python
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def <endpointName>(request):
    field_a = request.data.get('field_a')
    field_b = request.data.get('field_b')
    if not field_a:
        return Response({'error': 'field_a is required'}, status=400)

    result = do_<action>(request.user, {'field_a': field_a, 'field_b': field_b})
    return Response(result, status=201)
```

**With serializer (POST that creates a model):**
```python
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def <endpointName>(request):
    serializer = <Name>Serializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    instance = do_<action>(request.user, serializer.validated_data)
    return Response(<Name>Serializer(instance).data, status=201)
```

**URL path parameter:**
```python
@api_view(['GET'])
@permission_classes([AllowAny])
def <endpointName>(request, ticker: str):
    ...
```

### Option B — Class-Based View (list + create on same path only)

```python
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from ..<serializers> import <Name>Serializer
from ..<models> import <Model>

class <Name>View(generics.ListCreateAPIView):
    serializer_class = <Name>Serializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = <Model>.objects.filter(owner=self.request.user)
        # Apply query param filters:
        asset_type = self.request.query_params.get('asset_type')
        if asset_type:
            qs = qs.filter(asset_type=asset_type)
        return qs.order_by('-date')

    def perform_create(self, serializer):
        # Call service here for custom logic; save() sets owner
        instance = do_<action>(self.request.user, serializer.validated_data)
        # If the service saves: return instance (don't call serializer.save())
        # If the service just prepares data: serializer.save(owner=self.request.user)
```

### Export the view

In `backend/<app>/views/__init__.py`, add the import:
```python
from .<name> import <endpointName>  # FBV
# or
from .<name> import <Name>View       # CBV
```

If the app uses a single `views.py` (no `views/` directory), add the function/class directly there.

## 4. URL registration

Open `backend/<app>/urls.py` and add the new path **in logical order** (more specific paths before less specific ones, e.g. `bonds/series/fixed/` before `bonds/series/`):

```python
# FBV
path('<path>/', views.<endpointName>, name='<name>'),

# FBV with URL parameter
path('<path>/<str:ticker>/', views.<endpointName>, name='<name>'),

# CBV
path('<path>/', views.<Name>View.as_view(), name='<name>'),
```

The app's URL prefix is already set in `backend/backend/urls.py`:
- `base` → `api/`
- `portfolio` → `api/portfolio/`
- `analytics` → `api/analytics/`

So a path `'allocation/'` in `portfolio/urls.py` resolves to `/api/portfolio/allocation/`.

## 5. Frontend wiring (if the endpoint is consumed by the UI)

In `frontend/src/api/client.js`, add the API call function alongside the existing ones:

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

In the consuming component or page, import and call it:
```js
import { get<Thing> } from '../api/client';
```

## 6. Tests

Create `backend/<app>/tests/test_<name>.py`. Model on `backend/analytics/tests/test_predict_view.py` for FBVs and `backend/portfolio/tests/test_transaction_service.py` for service unit tests.

### Endpoint integration test

```python
from django.test import TestCase, override_settings
from django.contrib.auth.models import User

@override_settings(USE_MOCK_DATA_FETCHER=True)
class <Name>ViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.client.login(username='testuser', password='pass')
        # or for JWT: self.client.force_login(self.user)

    def test_returns_200_with_valid_params(self):
        response = self.client.get('/api/<path>/', {'param': 'value'})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn('expected_key', body)

    def test_returns_400_when_required_param_missing(self):
        response = self.client.get('/api/<path>/')
        self.assertEqual(response.status_code, 400)

    def test_requires_authentication(self):
        self.client.logout()
        response = self.client.get('/api/<path>/')
        self.assertEqual(response.status_code, 403)  # skip for AllowAny endpoints
```

### Service unit test

```python
from unittest.mock import Mock
from django.test import TestCase

class <Action>ServiceTests(TestCase):
    def test_<happy_path>(self):
        mock_fetcher = Mock()
        mock_fetcher.get_price.return_value = 150.0

        result = do_<action>(..., stock_fetcher=mock_fetcher)

        self.assertEqual(result.<field>, expected_value)
        mock_fetcher.get_price.assert_called_once_with(...)

    def test_raises_validation_error_when_<bad_input>(self):
        from rest_framework import serializers
        with self.assertRaises(serializers.ValidationError):
            do_<action>(bad_input)
```

## 7. Verify

```bash
# Backend — from backend/
DJANGO_SETTINGS_MODULE=backend.settings_test python manage.py test --no-input

# Frontend (if you added an API call) — from frontend/
npm run lint
npm run test
```

On Windows/PowerShell:
```powershell
$env:DJANGO_SETTINGS_MODULE = 'backend.settings_test'; python manage.py test --no-input
```

## Guardrails

- **No ORM in views** — views call services or selectors; never `Model.objects.*` directly in a view.
- **No business logic in selectors** — selectors return querysets or model instances only; no calculations, no writes.
- **Services raise `serializers.ValidationError`** for user-input errors (returns 400); raise `ValueError` for unexpected state (let it 500 or catch in the view).
- **Always pass `request.user`** to services and selectors for `IsAuthenticated` endpoints — never look up the user by ID from the request body.
- **Decimal precision** — never do `float(decimal) * float(other)`; convert: `Decimal(str(float_val))`. Output to response: `float(decimal_val)` is acceptable.
- **Date parsing** — always wrap `strptime` in `try/except ValueError` and return 400 on failure.
- **`@override_settings(USE_MOCK_DATA_FETCHER=True)`** on all test classes that trigger code paths touching external data fetchers — otherwise tests will attempt real network calls.
