# Vicente Ramirez Notes

I was exploring Cursor in this test so i was using Agents and like the original README says i put all the chat transcript in transcript folder ([`transcript`](transcript))

## Depth beats breadth

- Developer Experience: I was trying to make the most easier to setup, in my mind i was in a scenario where a new member junior or mid senior enter to the team and he required to setup it in one day and start working on it in differents environment, sometimes some bugs that occurs in staging or production are hard to replicate locally based on the data in db so to make the dev exp better and easier i create some scripts for Unix (Linux/MacOs) and Windows to setup it entirely and just override the different environment variables. Also for someone to setup the database locally, then run migrate and seed maybe for some devs its hard to install a database in their laptops or they can have some issues, just requiring docker you can setup the postgres image and run everything locally without major issues. If i had another day then i will improve the logs so a dev can debug it easier also improving the CD so devs should not have issues with migrations when they forgot to run it in different environments and say it was working on my local !

- Performance: In performance side i just try some endpoints and just looking the logic and db i was able to see that we were missing some indexes for basic queries. Also implemented pagination to different endpoints like post to avoid load all post + comments + tags per request

- Production readiness: Implemented Continuous Integration when a event like push / pull request on main branch, so if the project is on github we will have a Github action running everytime when a previous event is triggered so our code can be more accurately running the tests and check the code quality along with the linter. Also improved env vars based on a .env file and delete the fixed values on settings.py. 
Create a dockerfile to container the app with multistage also with a docker compose file to setup if required.
If i had another day then i will implement OpenTelemetry, Github CD workflow along with AWS Elastic Containter Registry (ECS) to add extra level of security with the docker repo and image.


# AI NOTES

# Performance

Interview focus: make slow endpoints usable on a seeded database (~100k posts, ~500k comments) without reshaping the domain or adding auth.

## Phase 1: Post list endpoints

### Pagination

`GET /api/posts`, `/api/posts/search`, and `/api/posts/by-tag/{slug}` return `{ "items": [...], "count": N }` with `page` / `page_size` (default 20, max 100). This removed loading ~90k rows per request.

### Queryset optimization

[`blog/queries.py`](blog/queries.py) `published_posts_qs()`:

- `select_related("author")`, `prefetch_related("tags")`, `defer("body")`, `order_by("-created_at")`

### Database indexes ([`0002_post_performance_indexes`](blog/migrations/0002_post_performance_indexes.py))

- Partial index `blog_post_pub_created_desc_idx` on `created_at DESC WHERE is_published = true`
- `pg_trgm` extension + GIN trigram indexes on `Post.title` and `Post.body`

### Search

Replaced `icontains` with `TrigramSimilarity` (threshold `0.1` in [`blog/api.py`](blog/api.py)).

## Phase 2: Post detail and user endpoints

### Post detail (`GET /api/posts/{id}`)

- Fetch via `post_detail_qs()`: author, tags prefetched, `comment_count` annotated
- `view_count` incremented with `F("view_count") + 1` (single `UPDATE`, no read-modify-write `save()`)
- Comments paginated on the same endpoint:

| Param | Default | Max |
| ----- | ------- | --- |
| `comment_page` | `1` | — |
| `comment_page_size` | `20` | `50` |

Response includes `comment_count` (total) and `comments` (current page). Hot seeded posts can have thousands of comments; loading all was a major bottleneck.

### User endpoints (`GET /api/users/{id}`, `GET /api/users/find?email=`)

- `user_detail_qs()` annotates `post_count` and `comment_count` in one query (no per-request `.count()` calls)
- Index on `User.email` ([`0003_user_email_index`](blog/migrations/0003_user_email_index.py)) for find-by-email

## Verification

- Tests: bounded query counts for list and detail; comment pagination; user annotated counts
- Seeded DB: `GET /api/posts?page=1&page_size=20` and `GET /api/posts/{id}?comment_page=1&comment_page_size=20` should be sub-second

Example EXPLAIN for list (after seed):

```sql
EXPLAIN ANALYZE
SELECT id, title, author_id, view_count, created_at
FROM blog_post
WHERE is_published = true
ORDER BY created_at DESC
LIMIT 20;
```

---

# Developer experience

Canonical setup: [NEW_README.md](NEW_README.md) (linked from [README.md](README.md)). Tooling is **uv-only** for Python; `mise.toml` remains optional legacy from the assignment baseline.

### Scripts (Makefile + `setup.ps1` parity)

- `deps` / `sync` — `uv sync`
- `wait-db` — waits for Postgres via `docker compose exec … pg_isready`
- `setup` — deps → docker-up → wait-db → migrate → seed (**no auto-runserver**)
- `run` — docker-up → wait-db → `.env.local` → `runserver`
- `check` — `ruff check` + tests (with Postgres)
- `doctor` — versions, compose status, DB readiness hint
- Safer `env-init` — skips existing files unless `FORCE=1` / `-Force`

### Environment

- One committed template: `.env.example`; `env-init` copies it to `.env`, `.env.local`, `.env.staging`, `.env.production` (gitignored)
- `ENVIRONMENT` in [`core/settings.py`](core/settings.py): non-local defaults `DEBUG=False`; rejects example `SECRET_KEY` when `DEBUG=False`

### Deliberate DX non-goals

- Pre-commit hooks
- Full merge of README and NEW_README (assignment text stays in README)
- CI database seeding (migrations + unit tests only)

---

# Production readiness (foundation)

Shared with DX where it helps teammates and load balancers.

### CI

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) — Postgres 16 service, `uv sync`, migrate, `pytest`, `ruff check` (no `--fix`).

### Health

- `GET /health/live` — process up
- `GET /health/ready` — `connection.ensure_connection()`

### Container

- [`Dockerfile`](Dockerfile) — multi-stage `uv sync` with `prod` group, **gunicorn** CMD
- [`docker-compose.yml`](docker-compose.yml) — optional `web` service, `depends_on` postgres `service_healthy`, `DB_HOST=postgres`

### Settings

- `CONN_MAX_AGE` env-driven (default 60s when not `local`)
- Structured key=value logging to stdout when `ENVIRONMENT != local`

### Kubernetes (EKS prep)

Baseline manifests in [`k8s/`](k8s/) — Deployment, Service, ALB Ingress, `secret.example.yaml`. CD workflows per environment still to add.

### Deferred (next day)

- OpenTelemetry / Datadog on HTTP + DB spans
- GitHub CD workflows → ECR → EKS; Helm/Kustomize overlays per env
- PgBouncer / RDS Proxy (document when `CONN_MAX_AGE` is not enough)
- `collectstatic`, secure headers middleware tuning, autoscaling
- Cursor pagination, authentication

---

## Deliberate non-goals (overall)

- Cursor pagination (offset pagination is sufficient for this scope)
- Authentication
- Reshaping the domain model beyond perf needs

## Possible follow-ups (out of scope)

- Tune trigram search threshold; add dedicated search smoke test
- Cache or defer `view_count` writes further if read traffic dominates
