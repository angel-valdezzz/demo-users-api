# Demo Users API

A small FastAPI service for realistic API testing: create a user, retrieve it, filter users, replace or patch fields, and delete it. Swagger and ReDoc are generated from the same schemas the API validates.

## Documentation

- [Swagger reference](https://angel-valdezzz.github.io/demo-users-api/)
- [Deployment and credentials](#render-free-deployment)
- Live Swagger: open `/docs` on your deployed API. ReDoc: `/redoc`.

The GitHub Pages reference is read-only and remains available while Render sleeps. Use the live Swagger page to execute requests with **Authorize**.

## Run locally

Install Poetry 2.5.1 or later, then:

```bash
poetry install
```

Generate independent credentials with `poetry run python -c "import secrets; print(secrets.token_urlsafe(32))"`. Configure `API_KEYS` as a JSON object of names and values. Each name owns a separate data space. Never commit real values.

PowerShell:

```powershell
$env:API_KEYS = '{"local":"REPLACE_WITH_YOUR_GENERATED_KEY"}'
poetry run uvicorn demo_api.main:create_app --factory --workers 1
```

Bash:

```bash
export API_KEYS='{"local":"REPLACE_WITH_YOUR_GENERATED_KEY"}'
poetry run uvicorn demo_api.main:create_app --factory --workers 1
```

Open `http://127.0.0.1:8000/docs`. Keys must have at least 32 characters. Add another named key for Actions or another authorized consumer. Removing a key revokes its access after restarting/redeploying. A name retains its data space during the process lifetime; changing the configuration restarts this temporary service.

## Business flow

| Method | Path | Result |
|---|---|---|
| POST | `/users` | Create; `201` and `Location` |
| GET | `/users/{user_id}` | Retrieve; `200` or `404` |
| GET | `/users?role=support&active=true&limit=20&offset=0` | Filter and paginate |
| PUT | `/users/{user_id}` | Replace editable fields |
| PATCH | `/users/{user_id}` | Update supplied fields |
| DELETE | `/users/{user_id}` | Delete; `204`, then GET returns `404` |
| GET | `/health` | Public availability check |

Send `X-API-Key` on users endpoints. POST and PUT require `name` and `email`; `role` defaults to `support`, and `active` to `true`. PATCH rejects explicit nulls. Unknown fields, invalid UUIDs, invalid emails and invalid pagination return `422`. A duplicate email returns `409`; missing or invalid credentials return `401`.

Example POST body:

```json
{"name":"Angel Demo","email":"angel@example.com","role":"sales","active":true}
```

IDs are **path parameters**. Filters and pagination are **query parameters**. Editable fields are the JSON **body**. All test data must be fictional. Each credential has one initial support user and a maximum of 1,000 users.

## Render free deployment

1. Connect this repository to Render and create a Blueprint from `render.yaml`.
2. Confirm **Free** for the service. No database or disk is required.
3. Enter `API_KEYS` securely in Render as a JSON object. Do not put it in `render.yaml`.
4. The service uses Poetry and one Uvicorn worker. Automatic deployment waits for passing GitHub checks on `main`.
5. Verify `/health`, `/docs` and an authenticated CRUD flow at the assigned HTTPS URL.

Free Render services sleep after 15 minutes without traffic. The first request wakes the service; startup can take roughly one minute. **All created data is temporary** and resets on suspension, restart, or deployment. Do not add workers: in-memory storage is process-local. Free Render Postgres expires after 30 days, so this demo does not depend on it.

For Robot consumers, configure `DEMO_BASE_URL` and `DEMO_API_KEY`. In Actions, the URL is a repository variable and the key a repository secret. Check `/health` before the suite with a total deadline of two minutes, then use normal request timeouts. Create unique users per execution and clean them up. Mask the header in reports, Robot output and console transcripts before publishing artifacts.

## Quality and CI

```bash
poetry run ruff check .
poetry run ruff format --check .
poetry run pytest -q
```

Tests cover CRUD, isolated credentials, uniqueness, defaults, invalid bodies, authentication and OpenAPI. GitHub Actions checks the code and exports a secret-free Swagger reference. Enable **Settings → Pages → Source: GitHub Actions** once to publish it.
