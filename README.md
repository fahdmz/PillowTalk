# DrowzyDiary

A private, voice-first sleep diary and wind-down companion: a bounded
evening worry offload and a morning sleep check-in, turned into a
correctable diary and cautious, non-causal weekly observations. Not a
medical diagnosis or treatment tool.

## Repository layout

- [`backend/`](backend/) — FastAPI service. Auth is handled entirely by
  Supabase Auth on the Flutter side; this API verifies the Supabase-issued
  JWT on every request and owns the check-in state machine, rule-based
  crisis detection, and non-causal sleep-factor detection. See
  [backend/README.md](backend/README.md).
- [`frontend/`](frontend/) — Flutter app: auth, a 3-tab home (Recap /
  Check-in / Profile), the night/morning-themed check-in chat, and a recap
  detail view. See [frontend/README.md](frontend/README.md).

`backend/` and `frontend/` are independent apps with their own dependencies
and tooling.

## Data model (Supabase/Postgres)

`sql/schema.sql` defines: `profiles`, `chat_sessions`, `chat_messages`,
`sleep_logs`, `sleep_factors`, `sleep_factor_occurrences` — all scoped to
`user_id` and backed by row-level security.

## Non-negotiable boundary

Check-ins are a fixed-step flow, not open-ended LLM conversation. Crisis
routing, consent, and step order stay rule-based and deterministic — see
`backend/app/services/crisis.py` and `backend/app/services/checkin_flow.py`.

## Setup

See [backend/README.md](backend/README.md) and
[frontend/README.md](frontend/README.md) for each app's setup steps. Both
need a shared Supabase project: run `backend/sql/schema.sql` once in the
Supabase SQL editor, then point the backend at its URL/service-role
key/JWT secret (`backend/.env`) and the frontend at its URL/anon key
(`--dart-define`, see frontend/README.md).
