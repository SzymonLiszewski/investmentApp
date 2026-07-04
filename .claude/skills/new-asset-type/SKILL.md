---
name: new-asset-type
description: Scaffold a new asset type (e.g. commodities, ETFs, real estate) across the full stack — model, serializers, calculator, asset manager, seed command, frontend form fields, and tests. Follow this when adding any new investment category that needs to live alongside stocks, bonds, and crypto.
---

# Add a new asset type

Follow every step in order. The architecture rule: the single `Asset` model holds all asset types; type-specific fields are nullable columns on that model. Business logic for value calculation lives in a dedicated `Calculator` subclass registered in `AssetManager`. Views and serializers enforce type-specific field requirements via `validate()`.

## 0. Gather requirements

Before writing code, establish (ask the user if not stated):

- **Internal name** — snake_case string used in code and the database (e.g. `commodities`, `real_estate`). This becomes the `AssetType.TextChoices` value.
- **Display name** — human-readable label (e.g. `'Commodities'`, `'Real Estate'`).
- **Native/settlement currency** — what currency the asset is denominated in (`'PLN'`, `'USD'`, `'EUR'`, or `'infer_from_symbol'` like stocks do).
- **Has symbol?** — does the asset have a ticker/symbol that can be looked up via yfinance or another fetcher, or is it always entered manually without a symbol?
- **Type-specific fields** — any extra fields beyond `symbol` and `name` that only this asset type needs (e.g. bonds have `maturity_date`, `interest_rate`, `bond_type`). For each field: name, Django field type, nullable/required.
- **Search mode** — can users search for this asset type in the frontend (symbol lookup), or is it always manually entered?

## 1. Asset model — `backend/base/models.py`

### 1a. Add to AssetType choices

In `Asset.AssetType(models.TextChoices)`, add:
```python
<INTERNAL_NAME> = '<internal_name>', '<Display Name>'
```

### 1b. Add type-specific fields

After the existing bond-specific fields block, add any new fields as nullable so they don't break existing rows:
```python
# <Display Name>-specific fields
<field_name> = models.<FieldType>(null=True, blank=True, ...)
```

### 1c. Update `clean()` if needed

If the new type requires a symbol (like stocks), add the same validation block that's already there for `AssetType.STOCKS`. If it does not require a symbol, no change needed (the existing check only fires for stocks).

## 2. Migration

```bash
# from backend/
python manage.py makemigrations
python manage.py migrate
```

Inspect the generated migration to confirm only additive changes (new fields or new choices values) — never destructive.

## 3. AssetSerializer — `backend/base/serializers.py`

### 3a. Declare type-specific fields

In `AssetSerializer.Meta.extra_kwargs`, add the new fields as optional:
```python
'<field_name>': {'required': False, 'allow_null': True},
```

If any fields are `DecimalField`, also add `allow_blank` only if it's a CharField. Match the pattern used for `interest_rate`, `wibor_margin`, etc.

### 3b. Update `validate()`

Add a block for the new type after the existing `if asset_type == 'bonds'` block:
```python
if asset_type == '<internal_name>':
    if <required_field> is None:  # only if a field is mandatory for this type
        raise serializers.ValidationError({'<field>': 'Required for <type>.'})
```

## 4. TransactionSerializer — `backend/portfolio/serializers.py`

### 4a. Declare write-only type-specific fields

After the bond-specific write-only fields block, add:
```python
# <Display Name>-specific fields (write-only, used during asset creation)
<field_name> = serializers.<FieldType>(write_only=True, required=False, allow_null=True, ...)
```

### 4b. Update `validate()`

Add a block for the new type in the `validate()` method, following the bond pattern:
```python
if asset_type == '<internal_name>':
    if <required_field> is None:
        raise serializers.ValidationError({'<field>': 'Required for <type>.'})
```

## 5. Calculator — `backend/portfolio/services/calculators.py`

Create a new subclass of `AssetCalculator`:

```python
class <Type>Calculator(AssetCalculator):
    def get_asset_type(self) -> str:
        return '<internal_name>'

    def get_current_value(self, asset_data: dict, target_currency: str) -> Decimal:
        # Implement value calculation here.
        # asset_data contains all Asset model fields as a dict.
        # Return Decimal value in target_currency.
        # If you need a price fetcher, accept it via __init__ (don't instantiate directly).
        ...
```

If the calculator needs a price fetcher (has a symbol), follow the `StockCalculator` pattern: accept the fetcher via `__init__`, never import a concrete provider here — the caller (`AssetManager`) injects it.

## 6. AssetManager — `backend/portfolio/services/asset_manager.py`

### 6a. Register the calculator

In `AssetManager.__init__()`, add to `self.calculators`:
```python
'<internal_name>': <Type>Calculator(<args if any>),
```

### 6b. Update `type_mapping`

In `_get_calculator_for_asset_type()`, add:
```python
'<internal_name>': '<internal_name>',
```

### 6c. Update `_get_native_currency()`

Add the native currency branch before the `else` / stocks branch:
```python
if asset.asset_type == '<internal_name>':
    return '<CURRENCY>'
```

For `'infer_from_symbol'`, no change needed — the existing stocks branch handles that.

## 7. Transaction service — `backend/portfolio/services/transaction_service.py`

In `get_or_create_asset()`, after the existing `if asset_type == 'bonds': ...` block, add:
```python
elif asset_type == '<internal_name>':
    asset_data.update({
        '<field_name>': kwargs.get('<field_name>'),
        # ... all type-specific fields
    })
```

Also ensure the function signature accepts the new kwargs (add them to the parameter list or use `**kwargs` if it already does).

## 8. Seed command — `backend/base/management/commands/seed_<internal_name>.py`

Model on `seed_crypto.py` (simple symbol+name) or `seed_polish_bonds.py` (type-specific fields). The command must:

- Extend `BaseCommand` with a clear `help` string.
- Build `asset_data` dicts for each record and pass through `AssetSerializer` — never write directly to the model.
- Use `get_or_create` logic via the serializer or a service function rather than raw `Asset.objects.create()`.
- Be idempotent: running it twice must not duplicate records.

```python
class Command(BaseCommand):
    help = 'Seed <internal_name> assets'

    def handle(self, *args, **options):
        assets = [...]  # list of dicts with at minimum 'name', 'asset_type'
        created = 0
        for item in assets:
            serializer = AssetSerializer(data={**item, 'asset_type': '<internal_name>'})
            if serializer.is_valid():
                obj, was_created = Asset.objects.get_or_create(
                    symbol=item.get('symbol'), name=item['name'],
                    defaults=serializer.validated_data
                )
                if was_created:
                    created += 1
        self.stdout.write(self.style.SUCCESS(f'Seeded {created} <type> assets.'))
```

## 9. API views (only if type-specific endpoints are needed)

Bonds have dedicated endpoints (`/api/bonds/series/`, `/api/bonds/economic-data/`) because they have complex lookup requirements. Only add new views if the asset type needs something the generic `/api/assets/search/` cannot provide.

If needed:
- Add view function(s) to a new `backend/base/views/<internal_name>.py`.
- Import and register in `backend/base/views/__init__.py` and `backend/base/urls.py`.
- Follow the function-based view pattern (`@api_view`, `@permission_classes`).

## 10. Frontend — `frontend/src/components/portfolio/AddStocks.jsx`

### 10a. Add to asset type dropdown

Locate the `<select>` or option list driven by `assetType` state. Add:
```jsx
<option value="<internal_name>"><Display Name></option>
```

### 10b. Add conditional form fields

After the existing bonds conditional block (`{assetType === 'bonds' && ...}`), add:
```jsx
{assetType === '<internal_name>' && (
  <div>
    {/* Type-specific fields here */}
    <label>...
    <input ...
  </div>
)}
```

### 10c. Update transaction payload

In the function that builds the POST body for `/api/portfolio/transactions/`, add type-specific fields when `assetType === '<internal_name>'`:
```js
...(assetType === '<internal_name>' && {
  <field_name>: <stateVar>,
  // ...
}),
```

### 10d. Reset state on type change

If you added new state variables, reset them in the `assetType` change handler (or on form reset) to avoid stale values carrying over when the user switches asset types.

## 11. Tests

### 11a. Calculator test

Create `backend/portfolio/tests/test_<internal_name>_calculator.py`:
- Happy path: `get_current_value()` returns a `Decimal` for valid asset data.
- Currency conversion: returns value in target currency when different from native.
- Edge cases: zero quantity, missing optional fields.

### 11b. Serializer validation test

Add to an existing serializer test file (or create `backend/base/tests/test_<internal_name>_serializer.py`):
- Valid data: serializer is valid and saves.
- Missing required type-specific field: serializer raises `ValidationError` with the correct field key.
- Wrong asset_type does not trigger the new validation block.

### 11c. AssetManager registration test

Assert that `AssetManager().get_calculator('<internal_name>')` returns an instance of `<Type>Calculator`.

## 12. Verify

```bash
# Backend — from backend/
DJANGO_SETTINGS_MODULE=backend.settings_test python manage.py test --no-input

# Frontend — from frontend/
npm run test
npm run lint
```

On Windows/PowerShell:
```powershell
$env:DJANGO_SETTINGS_MODULE = 'backend.settings_test'; python manage.py test --no-input
```

All tests must pass with zero lint warnings before the feature is considered done.

## Guardrails

- Never add an `AssetType` choice without also registering a `Calculator` — `AssetManager` will raise a `KeyError` at runtime for unknown types.
- All type-specific model fields must be `null=True, blank=True` — the Asset table is shared across all types.
- Don't import a concrete price fetcher inside the Calculator — inject it via `__init__` so tests can swap it.
- The `validate()` blocks in serializers must guard on `asset_type` first — never assume a field's presence.
