-- PillowTalk AI emotional-memory schema.
-- Run backend/sql/schema.sql first, then paste this whole file into the
-- Supabase SQL Editor. It is additive, rerunnable, and deletes no user data.

begin;

do $$
begin
  if to_regclass('public.chat_sessions') is null
     or to_regclass('public.chat_messages') is null
     or to_regclass('public.sleep_factors') is null
     or to_regclass('public.sleep_factor_occurrences') is null then
    raise exception 'Run backend/sql/schema.sql before ai_emotional_memory.sql';
  end if;

  if exists (
    select 1 from public.chat_sessions
    where status = 'active'
    group by user_id, checkin_mode
    having count(*) > 1
  ) then
    raise exception 'Complete duplicate active chat sessions before running this query';
  end if;
end
$$;

create unique index if not exists chat_sessions_one_active_per_mode_idx
  on public.chat_sessions (user_id, checkin_mode)
  where status = 'active';
create index if not exists chat_sessions_user_completed_idx
  on public.chat_sessions (user_id, ended_at desc)
  where status = 'completed';
create unique index if not exists chat_messages_id_session_uidx
  on public.chat_messages (id, session_id);

create table if not exists public.message_analyses (
  id bigint generated always as identity primary key,
  message_id uuid not null unique,
  session_id uuid not null,
  emotion text not null,
  emotion_scores jsonb not null default '{}'::jsonb,
  domains text[] not null default '{}'::text[],
  sleep_substances text[] not null default '{}'::text[],
  sleep_hours numeric(4, 2),
  wake_time time,
  confidence numeric(4, 3) not null,
  source text not null,
  risk_level text not null default 'none',
  model_id text,
  model_revision text,
  created_at timestamptz not null default now(),
  constraint message_analyses_message_session_fkey
    foreign key (message_id, session_id)
    references public.chat_messages (id, session_id) on delete cascade,
  constraint message_analyses_emotion_check check (emotion in (
    'joy', 'sadness', 'anger', 'fear', 'surprise', 'love', 'neutral'
  )),
  constraint message_analyses_emotion_scores_check
    check (jsonb_typeof(emotion_scores) = 'object'),
  constraint message_analyses_domains_check check (domains <@ array[
    'relationship', 'sleep', 'work', 'health', 'sleep_substances'
  ]::text[]),
  constraint message_analyses_sleep_substances_check
    check (sleep_substances <@ array[
      'caffeine', 'alcohol', 'nicotine', 'sleep_medication',
      'other_stimulant', 'other_sedative'
    ]::text[]),
  constraint message_analyses_sleep_hours_check
    check (sleep_hours is null or sleep_hours between 0 and 24),
  constraint message_analyses_confidence_check
    check (confidence between 0 and 1),
  constraint message_analyses_source_check
    check (source in ('local', 'foundry_fallback', 'rules')),
  constraint message_analyses_risk_level_check
    check (risk_level in ('none', 'low', 'medium', 'high', 'critical'))
);
alter table public.message_analyses enable row level security;
create index if not exists message_analyses_session_created_idx
  on public.message_analyses (session_id, created_at desc);
create index if not exists message_analyses_emotion_created_idx
  on public.message_analyses (emotion, created_at desc);

create table if not exists public.session_recaps (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null unique
    references public.chat_sessions (id) on delete cascade,
  title text not null,
  summary text not null,
  conclusion text not null,
  dominant_emotion text,
  domains text[] not null default '{}'::text[],
  emotional_trend jsonb not null default '{}'::jsonb,
  sleep_observations jsonb not null default '[]'::jsonb,
  model_deployment text not null,
  prompt_version text not null,
  generated_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint session_recaps_dominant_emotion_check
    check (dominant_emotion is null or dominant_emotion in (
      'joy', 'sadness', 'anger', 'fear', 'surprise', 'love', 'neutral'
    )),
  constraint session_recaps_domains_check check (domains <@ array[
    'relationship', 'sleep', 'work', 'health', 'sleep_substances'
  ]::text[]),
  constraint session_recaps_emotional_trend_check
    check (jsonb_typeof(emotional_trend) = 'object'),
  constraint session_recaps_sleep_observations_check
    check (jsonb_typeof(sleep_observations) = 'array')
);
alter table public.session_recaps enable row level security;
create index if not exists session_recaps_generated_idx
  on public.session_recaps (generated_at desc);

-- Raw message text stays in chat_messages; safety_events stores metadata only.
create table if not exists public.safety_events (
  id bigint generated always as identity primary key,
  message_id uuid not null unique,
  session_id uuid not null,
  risk_level text not null,
  signal_codes text[] not null default '{}'::text[],
  source text not null default 'rules',
  action_taken text not null,
  created_at timestamptz not null default now(),
  constraint safety_events_message_session_fkey
    foreign key (message_id, session_id)
    references public.chat_messages (id, session_id) on delete cascade,
  constraint safety_events_risk_level_check
    check (risk_level in ('high', 'critical')),
  constraint safety_events_source_check
    check (source in ('rules', 'foundry_fallback'))
);
alter table public.safety_events enable row level security;
create index if not exists safety_events_session_created_idx
  on public.safety_events (session_id, created_at desc);

alter table public.sleep_factor_occurrences
  add column if not exists message_id uuid,
  add column if not exists evidence_kind text not null default 'system_inferred',
  add column if not exists source text not null default 'rules',
  add column if not exists confidence numeric(4, 3);

do $$
begin
  if not exists (
    select 1 from pg_constraint
    where conname = 'sleep_factor_occurrences_message_fkey'
      and conrelid = 'public.sleep_factor_occurrences'::regclass
  ) then
    alter table public.sleep_factor_occurrences
      add constraint sleep_factor_occurrences_message_fkey
      foreign key (message_id) references public.chat_messages (id)
      on delete set null;
  end if;
  if not exists (
    select 1 from pg_constraint
    where conname = 'sleep_factor_occurrences_evidence_kind_check'
      and conrelid = 'public.sleep_factor_occurrences'::regclass
  ) then
    alter table public.sleep_factor_occurrences
      add constraint sleep_factor_occurrences_evidence_kind_check
      check (evidence_kind in ('user_reported', 'system_inferred'));
  end if;
  if not exists (
    select 1 from pg_constraint
    where conname = 'sleep_factor_occurrences_source_check'
      and conrelid = 'public.sleep_factor_occurrences'::regclass
  ) then
    alter table public.sleep_factor_occurrences
      add constraint sleep_factor_occurrences_source_check
      check (source in ('local', 'foundry_fallback', 'rules'));
  end if;
  if not exists (
    select 1 from pg_constraint
    where conname = 'sleep_factor_occurrences_confidence_check'
      and conrelid = 'public.sleep_factor_occurrences'::regclass
  ) then
    alter table public.sleep_factor_occurrences
      add constraint sleep_factor_occurrences_confidence_check
      check (confidence is null or confidence between 0 and 1);
  end if;
end
$$;

create index if not exists sleep_factor_occurrences_message_idx
  on public.sleep_factor_occurrences (message_id, occurred_at desc)
  where message_id is not null;

-- New AI tables: authenticated users may read/delete owned rows. All writes
-- happen through the FastAPI server key.
revoke all on table public.message_analyses from anon, authenticated;
grant select, delete on table public.message_analyses to authenticated;
drop policy if exists message_analyses_select_own on public.message_analyses;
create policy message_analyses_select_own on public.message_analyses
  for select to authenticated using (exists (
    select 1 from public.chat_sessions session
    where session.id = message_analyses.session_id
      and session.user_id = (select auth.uid())
  ));
drop policy if exists message_analyses_delete_own on public.message_analyses;
create policy message_analyses_delete_own on public.message_analyses
  for delete to authenticated using (exists (
    select 1 from public.chat_sessions session
    where session.id = message_analyses.session_id
      and session.user_id = (select auth.uid())
  ));

revoke all on table public.session_recaps from anon, authenticated;
grant select, delete on table public.session_recaps to authenticated;
drop policy if exists session_recaps_select_own on public.session_recaps;
create policy session_recaps_select_own on public.session_recaps
  for select to authenticated using (exists (
    select 1 from public.chat_sessions session
    where session.id = session_recaps.session_id
      and session.user_id = (select auth.uid())
  ));
drop policy if exists session_recaps_delete_own on public.session_recaps;
create policy session_recaps_delete_own on public.session_recaps
  for delete to authenticated using (exists (
    select 1 from public.chat_sessions session
    where session.id = session_recaps.session_id
      and session.user_id = (select auth.uid())
  ));

revoke all on table public.safety_events from anon, authenticated;
grant select, delete on table public.safety_events to authenticated;
drop policy if exists safety_events_select_own on public.safety_events;
create policy safety_events_select_own on public.safety_events
  for select to authenticated using (exists (
    select 1 from public.chat_sessions session
    where session.id = safety_events.session_id
      and session.user_id = (select auth.uid())
  ));
drop policy if exists safety_events_delete_own on public.safety_events;
create policy safety_events_delete_own on public.safety_events
  for delete to authenticated using (exists (
    select 1 from public.chat_sessions session
    where session.id = safety_events.session_id
      and session.user_id = (select auth.uid())
  ));

-- Existing AI-derived dashboard tables are also backend-write-only.
revoke all on table public.sleep_factors from anon, authenticated;
grant select, delete on table public.sleep_factors to authenticated;
drop policy if exists "sleep_factors_all_own" on public.sleep_factors;
drop policy if exists sleep_factors_select_own on public.sleep_factors;
create policy sleep_factors_select_own on public.sleep_factors
  for select to authenticated using ((select auth.uid()) = user_id);
drop policy if exists sleep_factors_delete_own on public.sleep_factors;
create policy sleep_factors_delete_own on public.sleep_factors
  for delete to authenticated using ((select auth.uid()) = user_id);

revoke all on table public.sleep_factor_occurrences from anon, authenticated;
grant select, delete on table public.sleep_factor_occurrences to authenticated;
drop policy if exists "sleep_factor_occurrences_all_own"
  on public.sleep_factor_occurrences;
drop policy if exists sleep_factor_occurrences_select_own
  on public.sleep_factor_occurrences;
create policy sleep_factor_occurrences_select_own
  on public.sleep_factor_occurrences for select to authenticated using (exists (
    select 1 from public.sleep_factors factor
    where factor.id = sleep_factor_occurrences.factor_id
      and factor.user_id = (select auth.uid())
  ));
drop policy if exists sleep_factor_occurrences_delete_own
  on public.sleep_factor_occurrences;
create policy sleep_factor_occurrences_delete_own
  on public.sleep_factor_occurrences for delete to authenticated using (exists (
    select 1 from public.sleep_factors factor
    where factor.id = sleep_factor_occurrences.factor_id
      and factor.user_id = (select auth.uid())
  ));

comment on table public.message_analyses is
  'Normalized emotion, domain, sleep, and safety analysis per user message.';
comment on table public.session_recaps is
  'One Indonesian recap and cautious conclusion per completed chat session.';
comment on table public.safety_events is
  'Minimal safety metadata; raw message text is not duplicated.';

commit;
