# Backend/DevOps Engineer Interview

A small content service: users, posts, comments, tags. Django + Ninja + PostgreSQL.

> **Assignment context:** interview goals and API summary are in [README.md](README.md). This document is the canonical setup guide.

## Quick Start

### Prerequisites

- **Python 3.14+** — [Download](https://www.python.org/downloads/) (pin with `uv python pin 3.14` if needed)
- **uv** — [Install](https://docs.astral.sh/uv/getting-started/installation/)
- **Docker** — [Download](https://www.docker.com/products/docker-desktop) (local PostgreSQL and optional app container)

### First-time setup

**Linux/macOS:**

```bash
make env-init          # once — creates .env, .env.local, .env.staging, .env.production
uv sync                # or: make deps
make setup             # deps + Postgres + migrate + seed (does not start the server)
make run               # daily dev server
```

**Windows (PowerShell):**

```powershell
.\setup.ps1 env-init
uv sync                # or: .\setup.ps1 deps
.\setup.ps1 setup
.\setup.ps1 run
```

If `setup.ps1` cannot run, allow local scripts once:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then visit http://localhost:8000/api/docs for API documentation.

---

## Before you run tests

Tests use PostgreSQL (including `pg_trgm` from migrations). Start the database first:

**Linux/macOS:** `make docker-up` then `make test`, or use `make check` / `make test` (they start Postgres and wait for readiness).

**Windows:** `.\setup.ps1 docker-up` then `.\setup.ps1 test`, or `.\setup.ps1 check`.

`make check` mirrors CI: `ruff check` + `pytest`.

---

## Daily Development (local database)

**Linux/macOS:**

```bash
make run
```

**Windows:**

```powershell
.\setup.ps1 run
```

`run` starts Docker Postgres, waits until it is ready, copies `.env.local` → `.env`, and starts `runserver`.

---

## Docker: Postgres only vs full stack

| Command | What it does |
| ------- | ------------ |
| `make docker-up` / `.\setup.ps1 docker-up` | PostgreSQL only (host-native `make run`) |
| `make up` / `.\setup.ps1 up` | Postgres + **web** (gunicorn in Docker) |
| `make down` / `.\setup.ps1 down` | Stop all compose services |

The **web** image runs gunicorn (not `runserver`). Health checks: `GET /health/live`, `GET /health/ready` (ready verifies DB connectivity).

---

## Other environments (smoke testing only)

`make run-staging` / `make run-production` copy `.env.staging` or `.env.production` to `.env` and start `runserver` on `0.0.0.0`. Use this to **smoke-test against a remote database**, not as a deployment model. Edit those files with your credentials (they are created from `.env.example` by `env-init`).

---

## Environment files

| File | Committed? | Purpose |
| ---- | ---------- | ------- |
| `.env.example` | Yes | Single template for all environments |
| `.env`, `.env.local`, `.env.staging`, `.env.production` | No (gitignored) | Your local copies (same starting content) |

`make env-init` / `.\setup.ps1 env-init` copies `.env.example` into the four gitignored files **only if they do not exist**. To overwrite: `make env-init FORCE=1` or `.\setup.ps1 env-init -Force`.

### Variables to change (staging / production)

```
SECRET_KEY=<strong-random-secret>
DB_HOST=your-database-host
DB_USER=your-username
DB_PASSWORD=your-password
ALLOWED_HOSTS=your-domain.com
ENVIRONMENT=staging   # or production
DEBUG=False
```

When `ENVIRONMENT` is not `local` and `DEBUG=False`, Django refuses to start with the example `SECRET_KEY`.

---

## API Endpoints

| Method | Path | Description |
| ------ | ---- | ----------- |
| GET    | `/api/posts` | Published posts, newest first (paginated) |
| GET    | `/api/posts/search?q=` | Trigram search on title/body (paginated) |
| GET    | `/api/posts/by-tag/{slug}` | Posts by tag (paginated) |
| GET    | `/api/posts/{id}` | Post detail |
| POST   | `/api/posts` | Create post |
| POST   | `/api/posts/{id}/comments` | Add comment |
| GET    | `/api/users/{id}` | User profile |
| GET    | `/api/users/find?email=` | Find user by email |
| GET    | `/health/live` | Liveness (process up) |
| GET    | `/health/ready` | Readiness (DB reachable) |

### Pagination (list endpoints)

`GET /api/posts`, `/api/posts/search`, and `/api/posts/by-tag/{slug}` return:

```json
{
  "items": [ /* PostListOut objects */ ],
  "count": 90000
}
```

Query parameters:

| Param | Default | Max | Description |
| ----- | ------- | --- | ----------- |
| `page` | `1` | — | Page number (1-based) |
| `page_size` | `20` | `100` | Items per page |

Example: `GET /api/posts?page=1&page_size=20`

---

## Common Commands

**Linux/macOS:**

```bash
make help           # All commands
make deps           # uv sync
make migrate        # Run migrations
make seed           # Seed (skip if data exists)
make seed-force     # Re-seed
make check          # lint + test (like CI)
make doctor         # Toolchain / DB diagnostics
make test
make format
make lint
make docker-down
```

**Windows:** same names via `.\setup.ps1 <command>`.

---

## Manual Commands

```bash
uv sync
uv run python manage.py migrate
uv run python manage.py seed
uv run python manage.py runserver
uv run pytest -v
uv run ruff format .
uv run ruff check .
```

---

## Troubleshooting

**PostgreSQL not connecting:**

```bash
docker compose ps
docker compose logs postgres
make doctor    # or .\setup.ps1 doctor
```

**Module not found:**

```bash
uv sync --reinstall
```

**Port 5432 in use:**

Change `DB_PORT` in `.env.local`, or stop the conflicting service. `make doctor` helps surface compose status.

**`migrate` fails right after `docker-up`:**

Use `make wait-db` or rely on `make setup` / `make run` / `make test`, which wait for Postgres health.

---

## CI

GitHub Actions (`.github/workflows/ci.yml`) runs on push/PR to `main`/`master`: Postgres 16 service, `uv sync`, migrate, `pytest`, `ruff check`.

## Kubernetes (future CD on EKS)

Baseline manifests live in [`k8s/`](k8s/) (Deployment, Service, ALB Ingress, `secret.example.yaml`). See [`k8s/README.md`](k8s/README.md) for apply steps and planned GitHub CD → ECR → EKS flow.

---

## Next Steps

Performance work and deferred production items are documented in [NOTES.md](NOTES.md).
