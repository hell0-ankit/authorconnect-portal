authorconnect-portal/
├── backend/
│   ├── .env
│   ├── .env.example
│   ├── manage.py
│   ├── requirements.txt
│   ├── config/
│   │   ├── __init__.py
│   │   ├── asgi.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── apps/
│   │   ├── __init__.py
│   │   ├── accounts/
│   │   │   ├── __init__.py
│   │   │   ├── admin.py
│   │   │   ├── apps.py
│   │   │   ├── models.py
│   │   │   ├── serializers.py
│   │   │   ├── urls.py
│   │   │   └── views.py
│   │   ├── books/
│   │   │   ├── __init__.py
│   │   │   ├── admin.py
│   │   │   ├── apps.py
│   │   │   ├── models.py
│   │   │   ├── serializers.py
│   │   │   ├── urls.py
│   │   │   └── views.py
│   │   └── support/
│   │       ├── __init__.py
│   │       ├── admin.py
│   │       ├── apps.py
│   │       ├── models.py
│   │       ├── serializers.py
│   │       ├── urls.py
│   │       └── views.py
│   ├── services/
│   │   └── ai_service.py
│   ├── knowledge_base/
│   │   └── bookleaf_faq.md
│   └── fixtures/
│       └── sample_data.json
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── index.css
│       ├── components/
│       ├── pages/
│       │   ├── auth/
│       │   ├── author/
│       │   └── admin/
│       ├── services/
│       ├── hooks/
│       ├── context/
│       └── utils/
├── docs/
│   ├── architecture.md
│   └── api-documentation.md
├── README.md
└── .gitignore

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