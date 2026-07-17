-- Durable retry protection for PillowTalk chat turns.
-- Run after schema.sql and ai_emotional_memory.sql.

begin;

alter table public.chat_messages
  add column if not exists idempotency_key text,
  add column if not exists reply_to_message_id uuid;

create unique index if not exists chat_messages_user_idempotency_uidx
  on public.chat_messages (session_id, idempotency_key)
  where sender = 'user' and idempotency_key is not null;

create unique index if not exists chat_messages_ai_reply_uidx
  on public.chat_messages (reply_to_message_id)
  where sender = 'ai' and reply_to_message_id is not null;

alter table public.chat_messages
  drop constraint if exists chat_messages_reply_to_message_fkey;
alter table public.chat_messages
  add constraint chat_messages_reply_to_message_fkey
  foreign key (reply_to_message_id, session_id)
  references public.chat_messages (id, session_id)
  on delete cascade;

alter table public.chat_messages
  drop constraint if exists chat_messages_idempotency_sender_check;
alter table public.chat_messages
  add constraint chat_messages_idempotency_sender_check check (
    idempotency_key is null or (
      sender = 'user' and length(idempotency_key) between 8 and 128
    )
  );

alter table public.chat_messages
  drop constraint if exists chat_messages_reply_sender_check;
alter table public.chat_messages
  add constraint chat_messages_reply_sender_check check (
    reply_to_message_id is null or sender = 'ai'
  );

comment on column public.chat_messages.idempotency_key is
  'Opaque client retry key; unique within a session for user messages.';
comment on column public.chat_messages.reply_to_message_id is
  'User message answered by this assistant message.';

commit;
