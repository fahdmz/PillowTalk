# DrowzyDiary mobile app

A Flutter implementation of the `DrowzyDiary.dc.html` design
(claude.ai/design project `188117e3-411b-440c-bad0-d0386dcf16bd`): an auth
screen, a 3-tab home (Recap / Check-in / Profile), a night/morning-themed
check-in chat, and a recap detail view with crisis-line handling — backed
by Supabase Auth and the FastAPI service in [`../backend`](../backend).

## Setup

```bash
flutter pub get
flutter run \
  --dart-define=SUPABASE_URL=https://your-project.supabase.co \
  --dart-define=SUPABASE_ANON_KEY=your-anon-key \
  --dart-define=API_BASE_URL=http://localhost:8000
```

`SUPABASE_URL`/`SUPABASE_ANON_KEY` are the same Supabase project the
backend points at (Settings > API in the Supabase dashboard — this is the
public anon key, not the backend's service-role key). `API_BASE_URL`
defaults to `http://localhost:8000` if omitted. See `lib/services/env.dart`.

## Layout

- `lib/theme/` - night/morning `Palette`s, Nunito text theme, and the
  bedtime-mode grayscale `ColorFilter`.
- `lib/models/` - plain data classes (chat message, recap entry/group,
  sleep factor).
- `lib/data/` - EN/ID copy (`strings.dart`), translation lookup tables,
  date/weekday formatting (`date_format.dart`), and the one remaining
  placeholder (`mock_data.dart` — the simulated STT transcript, since voice
  capture isn't wired to a real speech-to-text service yet).
- `lib/services/` - `AuthService` (the only place that touches Supabase
  Auth directly), `ApiClient` (adds the bearer token to every backend
  call), and `ChatService`/`RecapService`/`ProfileService` on top of it.
- `lib/state/app_state.dart` - single `ChangeNotifier` holding all app
  state and actions (screen/auth mode/active tab, chat messages, recap
  filter/selection, profile settings), talking to the network only through
  the services above.
- `lib/screens/` - `AuthScreen`, `HomeScreen` (+ `screens/tabs/` for Recap /
  Check-in / Profile), `ChatScreen`, `RecapDetailScreen`.
- `lib/widgets/` - shared pieces: crescent-moon/sun icons (custom painters),
  segmented toggle, filter pill, chat bubble, typing indicator, sleep bar
  chart, factor tile, bottom nav bar, breathing circle.

## Notes on fidelity

- Voice capture is still simulated with a timer and a fixed sample phrase
  (`mock_data.dart`) — real speech-to-text isn't wired up yet. Everything
  downstream of that (chat replies, crisis detection, sleep-factor
  detection) is real and comes from the backend.
- The crisis-line handling (SEJIWA, 119 ext. 8) is a real rule-based check
  on the backend (`app/services/crisis.py`), not LLM-decided.
- A few icons (mic, send, back, delete, nav icons) use standard Material
  icons as stand-ins for the design's hand-drawn SVGs; the moon and sun,
  which recur throughout and define the app's day/night identity, are
  recreated as custom painters for fidelity.
