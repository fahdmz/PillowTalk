# DrowzyDiary backend

FastAPI service for chat check-ins, recaps, and profile/sleep data. Auth is
**not** handled here — the Flutter app talks to Supabase Auth directly, and
every request to this API carries the Supabase-issued JWT in the
`Authorization: Bearer <token>` header, which `app/deps.py` verifies.

## Setup

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your Supabase project's URL, service role key, JWT secret
```

Run `sql/schema.sql` once in the Supabase SQL editor to create the tables
and RLS policies.

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

Docs at `http://localhost:8000/docs`.

## Endpoints

- `POST /chat/start` — begin a night or morning check-in, returns the greeting
- `POST /chat/message` — send a user message, get the next fixed-step reply
  (or the crisis reply if the rule-based screen triggers)
- `POST /chat/{session_id}/end` — close a check-in early (the UI's ✕ button)
- `GET /chat/{session_id}/messages` — full transcript of one session
- `GET /recaps` — list past check-ins (`?filter=all|night|morning&month=YYYY-MM`)
- `GET /recaps/{id}` — one recap's full transcript
- `DELETE /recaps/{id}` — delete a recap
- `GET /profile` / `PATCH /profile` — profile + settings
- `GET /profile/sleep/weekly` — this week's sleep hours by day
- `GET /profile/sleep-factors` — auto-detected, non-causal sleep influencers
