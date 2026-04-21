# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

FastAPI backend serving two React frontends (`../e-commerce_react`, customer; `../ecommerce_vendor`, vendor admin). PostgreSQL + optional Elasticsearch + Razorpay.

## Commands

```bash
pip install -r requirements.txt
python app.py                                # uvicorn on 0.0.0.0:8000 with reload
docker-compose up -d elasticsearch           # start ES (required for /search)
docker-compose --profile with-kibana up -d   # also start Kibana on 5601
```

No test runner is configured — `tests/` is empty. Ad-hoc debug utilities live at repo root: `debug_orders.py`, `fix_enum.py`, `fix_order_data.py`, `fresh_database_setup.py`, `check_enum.py`, `check_images.py`. Run them directly with `python <script>.py`.

## App entry and router wiring

`app.py` has ~110 lines of commented-out prior iterations. The **active** code starts at line 113 with `create_app()`.

Router prefixes are set in `app.include_router(...)` calls, **not** in the router modules. Current map:

| Prefix | Router file |
|---|---|
| `/api/v1` | `auth`, `categories`, `specifications`, `pricing`, `products`, `cart`, `addresses`, `orders`, `search` |
| `/api/v1/payment` | `payment` (Razorpay) |
| `/api/vendor` | `vender_auth`, `vendor_orders` |
| `/api/analytics` | `vendor_analytics` |

**Spelling:** `vender_auth` (not "vendor") — the file, router variable, and URL prefix use this spelling consistently. Do not "fix" unless you also update the vendor frontend's auth endpoints.

**CORS allow-list is hardcoded** in `app.py`: `elakkiyaboutique.com`, `www.elakkiyaboutique.com`, `localhost:5173`, `localhost:5174`. Add any new frontend origin here.

## Database

- SQLAlchemy 2.0 + `psycopg2-binary` on PostgreSQL.
- `Base.metadata.create_all(bind=engine)` runs on import — **no Alembic, no migrations.** Schema changes happen by editing models and either letting `create_all` add new tables (it will not alter existing ones) or running a fresh DB setup via `fresh_database_setup.py`.
- `src/models/__init__.py` must import every model so `Base.metadata` sees it. Add new models there or tables will not be created.
- Default DB name is `e-commerce_second` (note the dash and `_second` suffix).

## Configuration (`config/settings.py`)

Two large commented-out prior versions precede the active `class Settings` (around line 58). Settings come from env vars (loaded via `python-dotenv`) **with hardcoded defaults in source**, including the DB password. There is no `.env.example`. Relevant vars:

- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
- `API_V1_STR`, `PROJECT_NAME`, `BASE_URL`
- `ELASTICSEARCH_HOST`, `ELASTICSEARCH_PORT`, `ELASTICSEARCH_USERNAME`, `ELASTICSEARCH_PASSWORD`, `ELASTICSEARCH_USE_SSL`, `ELASTICSEARCH_VERIFY_CERTS` (these live in a commented-out Settings block — uncomment when using ES config)

## Elasticsearch (optional)

- Startup wraps `ElasticsearchService.initialize_index()` in try/except. The app boots without ES, but all `/api/v1/search*` endpoints will fail.
- **Auto-indexing** happens via SQLAlchemy event hooks (`after_insert`/`after_update`/`after_delete`) wired in `src/models/product.py`, not in `app.py`. When changing Product fields, update the ES document mapping in `src/documents/` and trigger `/api/v1/search/reindex`.
- `docker-compose.yml` only runs ES (+ optional Kibana); the FastAPI app is not containerized.

## Layout

- `config/` — `database.py`, `settings.py`, `elasticsearch.py`
- `src/api/v1/` — one router per file. Filename does not always match URL prefix (vendor routers live here but mount under `/api/vendor`).
- `src/models/` — SQLAlchemy models
- `src/schemas/` — Pydantic schemas
- `src/services/` — business logic (auth, cart, pricing, product, payment, file, vendor, search)
- `src/documents/`, `src/search/` — Elasticsearch document mappings + service
- `uploads/`, `media/` — served via static mounts at `/uploads` and `/media`

## Static files + uploads

Image uploads are served directly from the Python process via `StaticFiles`. The `uploads/` directory is created at startup if missing. In production behind a reverse proxy, `ProxyHeadersMiddleware` is configured with `trusted_hosts=["127.0.0.1"]` — update this list if the proxy sits elsewhere.

## Auth

Two separate flows:
- **Customer:** OTP-based (email/phone) via `src/api/v1/auth.py` + `src/models/otp.py`. Returns JWT + refresh token.
- **Vendor:** separate flow in `src/api/v1/vender_auth.py` with its own service `src/services/auth_vendor_service.py`.

Both issue PyJWT tokens; frontends refresh via interceptor queues.
