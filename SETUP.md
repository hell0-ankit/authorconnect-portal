# AuthorConnect Portal Setup Guide

This guide covers a local development setup on Windows using PowerShell. The
backend uses Django, PostgreSQL, Redis, and Daphne; the frontend uses React and
Vite.

## Prerequisites

- Git
- Python 3.12
- Node.js 22.12 or later
- PostgreSQL, with a database and user you can use for development
- Redis, either installed locally or started with Docker
- Docker Desktop only if you choose the Docker Redis option

## 1. Get the project

Open PowerShell in the project directory. If you have not cloned the project:

```powershell
git clone https://github.com/hell0-ankit/authorconnect-portal.git
Set-Location authorconnect-portal
```

If the repository is already open, just use its root directory.

## 2. Configure PostgreSQL

Create a PostgreSQL role and database for local development. For example, in
`psql` connected as a PostgreSQL administrator:

```sql
CREATE ROLE authorconnect_user WITH LOGIN PASSWORD 'replace-with-a-local-password';
CREATE DATABASE authorconnect OWNER authorconnect_user;
```

Use your own local password. If you already have a development database and
user, use those existing values instead.

## 3. Set up the backend

From the project root, create and activate a virtual environment, then install
the Python dependencies:

```powershell
Set-Location backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, allow scripts for the current terminal only
with `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, then
activate the environment again.

Copy the example environment file and generate a development Django secret
key:

```powershell
Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

Set the generated value as `SECRET_KEY` in `backend\.env`, then fill in your
PostgreSQL password and database details. The example uses these local values:

```dotenv
SECRET_KEY=<paste-the-generated-key-here>
DB_NAME=authorconnect
DB_USER=authorconnect_user
DB_PASSWORD=<your-local-postgresql-password>
DB_HOST=127.0.0.1
DB_PORT=5432
REDIS_URL=redis://127.0.0.1:6379/0
```

Keep `backend\.env` private and do not commit it. The development settings are
used by default when running `manage.py` locally. Set
`DJANGO_SETTINGS_MODULE=config.settings.development` in the current terminal
if you need to make the selection explicit:

```powershell
$env:DJANGO_SETTINGS_MODULE = "config.settings.development"
```

## 4. Start Redis and prepare the database

Start Redis locally using your Redis installation, or use the Compose Redis
service from the project root in another PowerShell terminal:

```powershell
docker compose up -d redis
docker compose exec redis redis-cli ping
```

The Redis check should return `PONG`. When Redis runs in Docker and Django runs
on Windows, the backend can connect through `127.0.0.1:6379` as configured
above.

Back in the backend terminal, apply database migrations:

```powershell
python manage.py migrate
```

Optional: load sample accounts and demo data:

```powershell
python manage.py seed_data
```

This command resets passwords for its sample accounts. Use it only with a
local/demo database, never with production data. See the demo credentials in
the [README](./README.md#demo-login-credentials).

## 5. Start the backend

Run Daphne from the `backend` directory:

```powershell
$env:DJANGO_SETTINGS_MODULE = "config.settings.development"
daphne -b 127.0.0.1 -p 8000 config.asgi:application
```

The API is available at `http://127.0.0.1:8000/api/v1/`. Keep this terminal
open while using the app.

## 6. Start the frontend

Open a second PowerShell terminal at the project root:

```powershell
Set-Location frontend
npm install
npm run dev
```

Open the local address printed by Vite, normally
`http://localhost:5173`. Vite proxies `/api` and `/ws` requests to the local
Daphne server, so no frontend environment file is needed for the default local
setup.

## 7. Check the setup

From the backend directory, with the virtual environment active and
PostgreSQL/Redis running:

```powershell
python manage.py check
python manage.py spectacular --file schema.yml
```

For the focused support service tests:

```powershell
python manage.py test apps.support.test_ai_service
```

## Troubleshooting

- **`SECRET_KEY is not set`:** Confirm `backend\.env` exists and contains a
  non-empty `SECRET_KEY`.
- **PostgreSQL connection error:** Confirm PostgreSQL is running and the
  database name, user, password, host, and port in `backend\.env` are correct.
- **Redis connection error or chat unavailable:** Confirm Redis is running and
  `REDIS_URL` points to the address reachable from the backend.
- **Frontend cannot reach the API:** Confirm Daphne is running on port `8000`
  and Vite is running on port `5173`.
- **WebSocket does not connect:** Confirm both servers are running and Redis
  responds to `redis-cli ping`.

## Docker and production

The repository's Docker Compose instructions are documented in the
[README](./README.md#docker-development). Compose is intended for local
development; it is not a production deployment configuration.

For a production deployment, use `config.settings.production`, set real secret
values and exact allowed hosts/origins in the hosting environment, configure
HTTPS at a trusted reverse proxy, and provide durable storage for private
ticket attachments. Follow the [production deployment checklist](./README.md#production-deployment-checklist).
