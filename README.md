# AuthorConnect Portal

For prerequisites and step-by-step local development instructions, see the
[Project Setup Guide](./SETUP.md).

## Support tickets

Authors create tickets at `POST /api/v1/support/` with their JWT access token.
Send the request as `multipart/form-data` when attaching a file. The optional
`book` value must be one of the authenticated author's book IDs; omit it for a
General / Account Level request. Attachments are limited to 5 MB and PDF, PNG,
JPEG, and UTF-8 text files, and are served only through the authenticated
ticket attachment endpoint.

The author dashboard displays books and earned, paid, and pending royalties.
Authors can read public admin replies and respond in the ticket thread. AI
tools are restricted to the admin support workflow.

Authors create tickets without invoking AI. Admins can request an AI-generated
reply draft from a ticket; the draft remains editable and is never sent
automatically. Configure `GEMINI_API_KEY` in `backend/.env` to enable Gemini
classification and the admin-only drafting workflow. `GEMINI_MODEL` is
optional and defaults to `gemini-3.6-flash`. AI suggestions remain separate
from admin-edited category and priority fields.

Apply the support schema with:

```sh
cd backend
python manage.py migrate
```

Example request:

```sh
curl -X POST http://127.0.0.1:8000/api/v1/support/ \
  -H "Authorization: Bearer <JWT_ACCESS_TOKEN>" \
  -F "book=12" \
  -F "subject=Question about my book" \
  -F "description=Please help me with this issue." \
  -F "attachment=@screenshot.png"
```

## Real-time ticket chat

The existing `TicketMessage` records remain the source of truth. The REST
message endpoint persists replies and broadcasts public messages through
Channels; an authenticated WebSocket client receives the same saved message.
Internal admin notes are not broadcast. Admin-only queue events announce new
tickets and ticket status/category/priority changes.

Configure `REDIS_URL` in `backend/.env` (defaults to
`redis://127.0.0.1:6379/0`). Start Redis locally with `redis-server` and verify
it with `redis-cli ping` (expected response: `PONG`). Docker is not required;
use any reachable Redis-compatible service if Redis is not installed locally.

Install the backend dependencies, migrate, and start the ASGI server:

```sh
cd backend
pip install -r requirements.txt
python manage.py migrate
daphne -b 127.0.0.1 -p 8000 config.asgi:application
```

In another terminal:

```sh
cd frontend
npm install
npm run dev
```

WebSockets use `/ws/tickets/<ticket_id>/` for conversations and
`/ws/tickets/queue/` for the admin queue. The client sends its current JWT
access token in the first WebSocket message rather than the URL. The server
validates it and ticket ownership before joining any group. The browser
reconnects with bounded backoff and refreshes the REST message history after a
connection is restored.

For automated backend tests, run:

```sh
cd backend
python manage.py test apps.support.tests apps.support.test_consumers
```

### Manual real-time check

1. Start PostgreSQL, Redis, the ASGI server, and the frontend.
2. Sign in as an author in one browser session and an admin in a private or
   separate browser session.
3. Open the same ticket in both sessions and confirm each reports a connected
   live chat.
4. Send a reply as the author; confirm it appears in the admin session without
   refreshing. Reply as the admin and confirm it appears for the author.
5. Create a ticket as the author and confirm it appears in the admin queue
   without refreshing. Change its status/category/priority as admin and
   confirm both ticket views update.
6. Temporarily stop Redis: REST replies remain persisted and return a delivery
   warning; an open WebSocket may still appear connected while Redis pub/sub is
   unavailable. Restart Redis, refresh or reconnect, and verify that the REST
   history restores any missed messages.

For production, run Django through an ASGI server such as Daphne behind a
reverse proxy configured for WebSocket `Upgrade`/`Connection` headers and
`wss://`. Set `VITE_API_BASE_URL` and, when needed,
`VITE_WS_BASE_URL=wss://<api-host>` at frontend build time. Keep Redis private
to the application network, require authentication/TLS where supported, and
set `REDIS_URL` only in the backend environment. Do not log WebSocket
authentication frames or tokens.

### Production deployment checklist

Use `config.settings.production` for both ASGI and WSGI deployments. Set a
unique, private `SECRET_KEY`, production PostgreSQL credentials, a private
Redis URL, and an explicit `ALLOWED_HOSTS` list. Set `CORS_ALLOWED_ORIGINS`
and `CSRF_TRUSTED_ORIGINS` to the exact HTTPS browser origins; do not use
wildcards. The Render hostname is used only when the corresponding host or
origin list is not configured.

Terminate TLS at a trusted reverse proxy and configure it to overwrite
`X-Forwarded-Proto` before forwarding requests. Keep
`SECURE_SSL_REDIRECT=true` and HSTS enabled only when the public service is
available over HTTPS. `SECURE_HSTS_INCLUDE_SUBDOMAINS` and
`SECURE_HSTS_PRELOAD` are opt-in because they affect every subdomain and can
be difficult to roll back.

Before deploying, run checks and database migrations as separate release
steps:

```sh
cd backend
python manage.py check --deploy --settings=config.settings.production
python manage.py migrate --noinput --settings=config.settings.production
```

Build frontend assets with the production API/WebSocket URLs. Use durable,
access-controlled storage for private ticket attachments and a backup/restore
plan for PostgreSQL, Redis as appropriate for the service, and uploaded files.
The included Docker Compose configuration is for local development; it binds
services to loopback and intentionally disables HTTPS redirection.

### Docker development

Docker Compose runs the existing Django ASGI application and Redis. PostgreSQL
remains external and uses the existing `DB_NAME`, `DB_USER`, `DB_PASSWORD`,
`DB_HOST`, and `DB_PORT` settings from `backend/.env`; no PostgreSQL container
or replacement database is created. The example file lists the required
environment variables. Copy it if needed and fill in the existing PostgreSQL
credentials and a Django `SECRET_KEY` before starting:

```powershell
Copy-Item backend\.env.example backend\.env
```

When PostgreSQL runs on the Windows host, Compose connects to it through
`host.docker.internal` while Django running locally continues to use the
`DB_HOST` in `backend/.env`. For a PostgreSQL server at another address, set
`DB_HOST_DOCKER` in the shell where Compose is run to that server's hostname.
Start PostgreSQL before running migrations.

From the project root, build and start Redis, check that it is ready, migrate
the existing PostgreSQL database, and then start the backend:

```powershell
docker compose build
docker compose up -d redis
docker compose exec redis redis-cli ping
docker compose run --rm backend python manage.py migrate
docker compose up -d backend
docker compose ps
```

The Redis check should print `PONG`. The backend waits for Redis's health check,
and uses `redis://redis:6379/0` inside Docker. Redis is also published only on
`127.0.0.1:6379`, so local Windows development using the default
`redis://127.0.0.1:6379/0` can use the same service.

Keep the frontend running locally so its existing Vite `/api` and `/ws` proxies
connect to the container on `127.0.0.1:8000`. Start it in another PowerShell
window with:

```powershell
cd frontend
npm run dev
```

To test chat, sign in as an author and a support admin in separate browser
sessions, open the same ticket, and confirm the live connection and messages
appear in both sessions. WebSocket connections continue to use the existing
JWT authentication and ticket routes.

Stop the containers without removing data using `docker compose stop`, and
resume them later with `docker compose start`. Alternatively,
`docker compose down` removes the containers but preserves the `redis_data`
volume; run `docker compose up -d` to recreate and start the services. Do not
use `docker compose down -v` if you want to keep that volume.

## Demo login credentials

These credentials are for local/demo use only. They are created by the seed
data command and work only after it has run successfully and the accounts exist
in the database. Do not use these passwords in production.

### Admin account

| Role | Username | Email | Password |
|---|---|---|---|
| Admin | `admin` | `admin@bookleaf.com` | `AdminPass123!` |

### Author accounts

All listed authors share the demo password `AuthorPass123!`.

| # | Author | Username | Email |
|---:|---|---|---|
| 1 | Priya Sharma | `priya_sharma` | priya.sharma@email.com |
| 2 | Rohit Kapoor | `rohit_kapoor` | rohit.kapoor@email.com |
| 3 | Ananya Reddy | `ananya_reddy` | ananya.reddy@email.com |
| 4 | Vikram Joshi | `vikram_joshi` | vikram.joshi@email.com |
| 5 | Meera Nair | `meera_nair` | meera.nair@email.com |
| 6 | Arjun Malhotra | `arjun_malhotra` | arjun.malhotra@email.com |
| 7 | Sneha Kulkarni | `sneha_kulkarni` | sneha.kulkarni@email.com |
| 8 | Farhan Sheikh | `farhan_sheikh` | farhan.sheikh@email.com |
| 9 | Kavita Deshmukh | `kavita_deshmukh` | kavita.deshmukh@email.com |
| 10 | Diya Chatterjee | `diya_chatterjee` | diya.chatterjee@email.com |