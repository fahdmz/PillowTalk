-- DrowzyDiary — Supabase schema
-- Auth is entirely handled by Supabase Auth (auth.users). Everything below
-- is app data that hangs off auth.uid(). Run this in the Supabase SQL editor.

-- ─────────────────────────────────────────────────────────────────────────
-- profiles: one row per user, created on first login (upsert from backend)
-- ─────────────────────────────────────────────────────────────────────────
create table if not exists public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  full_name text,
  age int,
  language text not null default 'en' check (language in ('en', 'id')),
  bedtime_mode boolean not null default false,
  reminder_tone text not null default 'chimes',
  quiet_hours_start time not null default '22:00',
  quiet_hours_end time not null default '07:00',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.profiles enable row level security;

drop policy if exists "profiles_select_own" on public.profiles;
create policy "profiles_select_own" on public.profiles
  for select using (auth.uid() = id);
drop policy if exists "profiles_upsert_own" on public.profiles;
create policy "profiles_upsert_own" on public.profiles
  for insert with check (auth.uid() = id);
drop policy if exists "profiles_update_own" on public.profiles;
create policy "profiles_update_own" on public.profiles
  for update using (auth.uid() = id);

-- ─────────────────────────────────────────────────────────────────────────
-- chat_sessions: one row per check-in (nightly worry offload / morning diary)
-- step_index drives the fixed-step state machine server-side.
-- ─────────────────────────────────────────────────────────────────────────
create table if not exists public.chat_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  checkin_mode text not null check (checkin_mode in ('night', 'morning')),
  status text not null default 'active' check (status in ('active', 'completed')),
  step_index int not null default 0,
  is_crisis boolean not null default false,
  preview text,
  started_at timestamptz not null default now(),
  ended_at timestamptz
);

alter table public.chat_sessions enable row level security;

drop policy if exists "chat_sessions_all_own" on public.chat_sessions;
create policy "chat_sessions_all_own" on public.chat_sessions
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create index if not exists chat_sessions_user_started_idx
  on public.chat_sessions (user_id, started_at desc);

-- ─────────────────────────────────────────────────────────────────────────
-- chat_messages: full transcript per session
-- ─────────────────────────────────────────────────────────────────────────
create table if not exists public.chat_messages (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.chat_sessions (id) on delete cascade,
  sender text not null check (sender in ('ai', 'user')),
  text text,
  is_crisis boolean not null default false,
  crisis_prefix text,
  crisis_phone text,
  crisis_suffix text,
  created_at timestamptz not null default now()
);

alter table public.chat_messages enable row level security;

drop policy if exists "chat_messages_all_own" on public.chat_messages;
create policy "chat_messages_all_own" on public.chat_messages
  for all using (
    exists (
      select 1 from public.chat_sessions s
      where s.id = chat_messages.session_id and s.user_id = auth.uid()
    )
  ) with check (
    exists (
      select 1 from public.chat_sessions s
      where s.id = chat_messages.session_id and s.user_id = auth.uid()
    )
  );

create index if not exists chat_messages_session_idx
  on public.chat_messages (session_id, created_at);

-- ─────────────────────────────────────────────────────────────────────────
-- sleep_logs: Consensus-Sleep-Diary-lite fields, one row per morning check-in
-- ─────────────────────────────────────────────────────────────────────────
create table if not exists public.sleep_logs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  session_id uuid references public.chat_sessions (id) on delete set null,
  checkin_date date not null default current_date,
  bedtime time,
  sleep_latency_minutes int,
  wake_count int,
  wake_after_sleep_minutes int,
  wake_time time,
  quality_rating int check (quality_rating between 1 and 5),
  duration_minutes int,
  created_at timestamptz not null default now()
);

alter table public.sleep_logs enable row level security;

drop policy if exists "sleep_logs_all_own" on public.sleep_logs;
create policy "sleep_logs_all_own" on public.sleep_logs
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create index if not exists sleep_logs_user_date_idx
  on public.sleep_logs (user_id, checkin_date desc);

-- ─────────────────────────────────────────────────────────────────────────
-- sleep_factors: deterministic, non-causal "influencers" surfaced in Profile
-- ─────────────────────────────────────────────────────────────────────────
create table if not exists public.sleep_factors (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  name_key text not null,
  level text not null default 'low' check (level in ('low', 'medium', 'high')),
  updated_at timestamptz not null default now(),
  unique (user_id, name_key)
);

alter table public.sleep_factors enable row level security;

drop policy if exists "sleep_factors_all_own" on public.sleep_factors;
create policy "sleep_factors_all_own" on public.sleep_factors
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create table if not exists public.sleep_factor_occurrences (
  id uuid primary key default gen_random_uuid(),
  factor_id uuid not null references public.sleep_factors (id) on delete cascade,
  session_id uuid references public.chat_sessions (id) on delete set null,
  checkin_label_key text not null check (checkin_label_key in ('Nightly Check-in', 'Morning Check-in')),
  occurred_at timestamptz not null default now()
);

alter table public.sleep_factor_occurrences enable row level security;

drop policy if exists "sleep_factor_occurrences_all_own" on public.sleep_factor_occurrences;
create policy "sleep_factor_occurrences_all_own" on public.sleep_factor_occurrences
  for all using (
    exists (
      select 1 from public.sleep_factors f
      where f.id = sleep_factor_occurrences.factor_id and f.user_id = auth.uid()
    )
  ) with check (
    exists (
      select 1 from public.sleep_factors f
      where f.id = sleep_factor_occurrences.factor_id and f.user_id = auth.uid()
    )
  );

create index if not exists sleep_factor_occurrences_factor_idx
  on public.sleep_factor_occurrences (factor_id, occurred_at desc);
