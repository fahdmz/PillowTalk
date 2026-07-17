# Manual test conversations

Sample messages to type into the app (or POST to `/chat/message`) to exercise the
real pipeline end-to-end: `chat_sessions` / `chat_messages` / `message_analyses` /
`sleep_factors` / `sleep_factor_occurrences` / `safety_events` tables, the local +
Foundry-fallback classifier, and the recap generator.

## How to use

1. `POST /chat/start` with `{"checkin_mode": "night" | "morning", "language": "en" | "id"}`.
2. `POST /chat/message` with `{"session_id", "text", "language"}` for each line in a
   session, in order (the chatbot uses prior turns for continuity).
3. `POST /chat/{session_id}/end` when a session's lines are done — this marks the
   session completed and generates the recap (`GET` it back via the recaps router).
4. Two modules in the codebase are **not** wired into this flow and can be ignored
   when predicting behavior: `services/checkin_flow.py` (fixed-step scripts,
   superseded by the free-form Foundry chatbot) and `services/crisis.py` (superseded
   by `services/safety.py`, which is what `chat_orchestrator.py` actually calls).
5. Everything under "Extraction reference" below is regex, not the ML model — it's
   deterministic and a good way to sanity-check what a session *should* produce
   before you look at the DB row.

### Extraction reference (`analysis_normalizer.py`)

- **Substances** (keyword, non-negated): caffeine (coffee/kopi/kafein/energy drink),
  alcohol (alcohol/bir/wine), nicotine (rokok/vape/cigarette), sleep_medication
  (obat tidur/melatonin/zolpidem), other_stimulant, other_sedative.
- **Domains**: relationship, sleep (tidur/bangun/sleep/slept/woke/awake), work
  (kerja/deadline/meeting/rapat), health.
- **sleep_hours**: only matches `tidur/slept/sleep(ing) [selama/for] <N> jam/hours/hrs`.
- **wake_time**: only matches `bangun/woke up/wake up [jam/pukul/at] HH[:MM]`.
- Negation words (`tidak, nggak, gak, no, not, belum, tanpa...`) within 4 tokens
  before a keyword suppress the match — several lines below test this on purpose.

### Factor-level build-up (`dashboard.py: _factor_level`)

`sleep_factors` level is just occurrence count: 1 → `low`/"insufficient_data",
2 → `medium`, 3+ → `high`. To see all three, send the caffeine sessions below (N1,
N2, N4, M1 all mention coffee — 4 occurrences → high), the work sessions (N1, N3 —
2 occurrences → medium), and the alcohol session only once (N4 → low).

---

## Night check-ins — English

**Session N1** (`checkin_mode: night`, `language: en`)
> Tests: caffeine + work domain, sadness→neutral arc
1. "I had two coffees after 6pm because of a work deadline and now my head won't stop racing."
2. "Yeah, I'm dreading tomorrow's meeting. I keep scrolling on my phone instead of actually trying to sleep."
3. "Honestly I just feel tired and a bit defeated about it, but I'm going to try to lie down now."

**Session N2** (next night, `en`)
> Tests: caffeine again (factor count 2), joy emotion, no domain false-positive
1. "Good day today actually — I'm really happy, we closed out a project early."
2. "I did have a cappuccino around 8pm to celebrate though, so we'll see how that goes."
3. "Feeling pretty relaxed, just wanted to note the coffee before I forget."

**Session N3** (`en`)
> Tests: work domain (count 2 → medium), anger, health domain
1. "I'm honestly furious. My manager moved the deadline up again and I have a headache from the stress."
2. "I took some paracetamol for the headache. Otherwise no caffeine or anything tonight, just angry."
3. "Calmer now, just needed to vent before bed."

**Session N4** (`en`)
> Tests: alcohol (count 1 → low), nicotine, sleep_hours phrase, relationship domain
1. "Had a couple glasses of wine with my partner tonight, and I also smoked a cigarette outside which I'm not proud of."
2. "We slept for about 5 hours last night and I could feel it all day."
3. "A little anxious it'll happen again tonight too."

**Session N5** (`en`)
> Tests: sleep_medication + other_sedative substances, fear emotion
1. "I took melatonin again tonight because I'm scared I won't fall asleep like last week."
2. "My doctor also mentioned a sedative as an option but I haven't tried it."
3. "Just anxious about tomorrow in general, not anything specific."

---

## Night check-ins — Indonesian

**Session N6** (`id`)
> Tests: kopi/kafein keyword, negated alcohol (should NOT flag), irregular bedtime phrasing
1. "Aku minum kopi lagi jam 9 malam gara-gara masih ada kerjaan kantor yang belum selesai."
2. "Tapi aku tidak minum alkohol sama sekali malam ini, cuma kopi itu."
3. "Rasanya jengkel karena selalu begadang gara-gara kerjaan."

**Session N7** (`id`)
> Tests: rokok/vape, wake_time + sleep_hours extraction together
1. "Semalam aku merokok sebelum tidur, mungkin itu yang bikin susah tidur."
2. "Aku tidur selama 6 jam dan bangun jam 5.30, badan masih terasa lelah."
3. "Agak sedih karena pengen tidur lebih nyenyak."

---

## Morning check-ins

**Session M1** (`checkin_mode: morning`, `en`)
> Tests: sleep_hours + wake_time regex, caffeine (factor count → high), surprise emotion
1. "I went to bed around 11, but I'd had a coffee at 7pm so it took forever to fall asleep."
2. "I slept for about 6 hours total, woke up twice in the night."
3. "I woke up at 6:45 and honestly felt surprisingly okay, better than expected."

**Session M2** (`morning`, `id`)
> Tests: sleep_hours/wake_time in Indonesian, love emotion, no substances
1. "Aku tidur selama 7 jam, cukup nyenyak semalam."
2. "Tidak ada yang mengganggu, pasanganku menemaniku sampai tertidur, jadi rasanya tenang."
3. "Bangun jam 6 pagi, perasaanku senang dan penuh cinta hari ini."

**Session M3** (`morning`, `en`)
> Tests: negated caffeine/alcohol (should NOT flag either), neutral emotion
1. "No coffee, no alcohol yesterday, just a normal quiet evening."
2. "I slept for 8 hours and woke up at 7, feeling pretty neutral about the day ahead."
3. "Nothing else to report really."

---

## Negation / false-positive controls

Use these to confirm the extractor does **not** over-trigger:

- "I didn't have any coffee today, just water." *(caffeine should NOT appear)*
- "No wine for me tonight." *(alcohol should NOT appear)*
- "Aku tidak minum kopi atau alkohol malam ini." *(neither substance should appear)*
- "This deadline is killing me, I can't wait for it to be over." *(idiom — must NOT trip crisis/safety screening, and "killing me" isn't a domain/substance keyword either)*
- "I haven't touched a cigarette in months." *(nicotine should NOT appear)*

---

## Safety / crisis screening set

These exercise `services/safety.py`'s `SafetyScreen`, which runs before the
classifier on every message. **Send these from a throwaway/test account**, since a
triggered row lands in `safety_events` and flips `chat_sessions.is_crisis = true`.
This is QA for your own crisis-detection pipeline, not real disclosure — useful to
confirm sensitivity/specificity before it ships.

### Should interrupt — risk_level `high` (no immediacy/means, so no escalation to critical)
- "I want to kill myself." *(en)*
- "Aku ingin bunuh diri." *(id)*
- "I've been thinking I want to hurt myself." *(en)*

### Should interrupt — risk_level `critical` (immediacy or means present)
- "I want to end my life tonight." *(immediacy: "tonight")*
- "Aku ingin bunuh diri sekarang dengan pisau." *(immediacy "sekarang" + means "pisau")*
- "I'm going to kill him right now." *(violence pattern + immediacy → critical)*

### Should flag `low` but NOT interrupt (historical / third-person / already-safe)
- "Dulu aku pernah ingin bunuh diri, tapi sekarang aku sudah aman." *(historical + safe-now markers)*
- "My friend said she wanted to end her life last year, and it really scared me." *(third-person marker)*
- "I used to want to die back in college, but I'm in a much better place now." *(historical marker)*

### Should NOT trigger at all (`none`) — negation regression guard
- "I don't want to hurt myself, I just feel really overwhelmed lately." *(negated)*
- "Aku tidak ingin mengakhiri hidup, cuma capek banget." *(negated)*
- "I would never do anything to hurt myself." *(negated)*

### Expected DB effects to check
- `high`/`critical` rows: `chat_messages.is_crisis = true` on the AI reply, `chat_sessions.is_crisis = true`, a `safety_events` row with matching `risk_level` and `signal_codes` (e.g. `self_harm_intent`, `immediacy`, `means_access`, `violence_intent`), and **no** `message_analyses` domain/substance data for that turn (it's the fixed neutral safety analysis).
- `low` rows: normal chat continues (not interrupted), but `message_analyses.risk_level` for that turn should read `low`, with signal `contextual_or_historical`.
- `none` rows: behaves like any ordinary message — normal classifier/domain/substance extraction applies.
