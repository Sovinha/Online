# Copilot Instructions - Delivery Payment Calculator

## Project Overview
A **Flask-based payment calculation system** for motoboy (motorcycle courier) deliveries. It computes compensation based on distance (Google Maps API), base fees, and per-km rates, with adjustment capabilities and multi-location support.

**Key use case**: Restaurant delivery chains manage courier payments across multiple branches with configurable pricing models.

## Architecture & Data Flow

### Core Components
1. **[app.py](../app/app.py)** - Flask factory creates app with SQLite DB, login manager, and blueprints
2. **[models.py](../app/models.py)** - Three entities: `User`, `Historico` (payment batches), `HistoricoMotoboy` (individual courier records with hierarchy)
3. **[routes.py](../app/routes.py)** - Main endpoints for dashboard, calculations, history, exports
4. **[services/](../app/services/)** - Specialized modules for distance caching, calculations, PDF/TXT generation

### Data Flow: Payment Calculation
```
Excel Upload → read_excel → calcular_preview (distance lookup + calculation)
→ calcular_confirmar (persist to DB) → Dashboard/Export (PDF/TXT)
```

**Config-driven**: All pricing & location data loaded from [config.json](../config.json):
- Google Maps API key
- `valor_base` (base fee), `valor_km` (per-km rate), `valor_minimo` (minimum)
- `lojas` dict with addresses for distance calculations

## Critical Patterns & Workflows

### Distance Caching Strategy
[cache.py](../app/services/cache.py) implements persistence for Google Maps distance matrix calls via `cache_distancias.json`. **Before adding distance logic**: check cache first to avoid API quota exhaustion.

### File Path Resolution
[calculator.py](../app/services/calculator.py) uses `get_base_dir()` to support both development (Flask) and frozen executables (PyInstaller). When modifying file paths, respect this pattern.

### Multi-Motoboy Batch Processing
[Historico.motoboys](../app/models.py) uses `cascade="all, delete-orphan"` - deleting a batch auto-deletes linked courier records. Avoid orphaning records in custom queries.

### Database Indexes
[models.py](../app/models.py) indexes: `loja` (store filtering), `motoboy` (courier dashboards), `historico_id` (foreign key). When adding filters, prioritize indexed columns.

## Common Development Tasks

### Adding a New Route/Feature
1. Add route in [routes.py](../app/routes.py) with `@bp.route()` and `@login_required` decorator
2. Load config via `load_config()` if needed
3. Use `load_cache()`/`save_cache()` for distance caching
4. Return `render_template()` or `jsonify()` response

### Modifying Pricing Logic
Edit [calculator.py](../app/services/calculator.py) `calcular_pagamentos()`. Changes propagate to:
- Preview mode (`calcular_preview` endpoint)
- Historical data (recalculation requires re-running batches)

### Export Generation
- **PDF**: [pdf.py](../app/services/pdf.py) uses ReportLab, hardcoded Y-coordinate pagination
- **TXT**: [history.py](../app/services/history.py) simple text file
Both save to `exports/` directory (auto-created)

### User Authentication
[auth.py](../app/auth.py) implements basic username/password (plaintext - dev only). All protected routes use `@login_required`. User creation via separate [criar_usuario.py](../criar_usuario.py) script.

## Environment & Dependencies

**Run**: `python run.py` (Flask on 127.0.0.1:5000 with debug=True)
**Dependencies** ([requirements.txt](../requirements.txt)):
- Flask ecosystem (login, SQLAlchemy)
- `googlemaps` (distance matrix API)
- `pandas`, `openpyxl` (Excel import)
- `reportlab` (PDF generation)

**Database**: SQLite at `instance/app.db` (auto-created on app startup via `db.create_all()`)

## Design Decisions & Context

- **Dual export formats**: TXT for simple transfer, PDF for formal records
- **JSON config**: Avoids hardcoding pricing/locations; edit without redeploying
- **Pagination in PDF**: Y-coordinate tracking with page breaks (brittle but lightweight)
- **Cache JSON**: Reduces Google Maps API calls; manually persist after `calcular_pagamentos()`

## Testing Workflow
Manual testing via web UI:
1. Login with user created via `criar_usuario.py`
2. Upload Excel with delivery data
3. Verify preview calculations match config pricing
4. Confirm and export

No automated tests present - add pytest suite if regression prevention needed.
