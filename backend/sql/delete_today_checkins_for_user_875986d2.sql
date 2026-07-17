-- Delete today's PillowTalk check-ins for this Supabase auth user:
-- 875986d2-c39d-4229-ba8a-4eff20179ee1
--
-- "Today" is calculated in Asia/Jakarta, matching the app user's local day.
-- Deleting chat_sessions cascades to chat_messages, message_analyses, and
-- session_recaps. sleep_factor_occurrences are deleted explicitly first
-- because their session_id foreign key uses ON DELETE SET NULL.

begin;

do $$
declare
  target_user_id uuid := '875986d2-c39d-4229-ba8a-4eff20179ee1';
begin
  if not exists (select 1 from auth.users where id = target_user_id) then
    raise exception 'No auth.users row found for %', target_user_id;
  end if;
end
$$;

create temporary table today_sessions_to_delete on commit drop as
select id
from public.chat_sessions
where user_id = '875986d2-c39d-4229-ba8a-4eff20179ee1'
  and started_at >= date_trunc('day', now() at time zone 'Asia/Jakarta') at time zone 'Asia/Jakarta'
  and started_at < (date_trunc('day', now() at time zone 'Asia/Jakarta') + interval '1 day') at time zone 'Asia/Jakarta';

delete from public.sleep_factor_occurrences occurrence
where occurrence.session_id in (
  select id from today_sessions_to_delete
);

delete from public.chat_sessions session
where session.id in (
  select id from today_sessions_to_delete
);

commit;

-- Optional check after running:
--
-- select count(*) as remaining_today_checkins
-- from public.chat_sessions
-- where user_id = '875986d2-c39d-4229-ba8a-4eff20179ee1'
--   and started_at >= date_trunc('day', now() at time zone 'Asia/Jakarta') at time zone 'Asia/Jakarta'
--   and started_at < (date_trunc('day', now() at time zone 'Asia/Jakarta') + interval '1 day') at time zone 'Asia/Jakarta';
