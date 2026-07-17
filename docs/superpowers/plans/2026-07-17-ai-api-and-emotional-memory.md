# PillowTalk AI API and Emotional Memory Implementation Plan

> Implementation is intentionally deferred while the Flutter UI is changing. This plan is backend-first and preserves the current Indonesian-facing labels.

**Goal:** Replace the fixed chat flow with a safe Azure AI Foundry chatbot, keep a local Indonesian emotion classifier as the primary classifier, use the GPT-5-mini Foundry deployment only as classification fallback, persist useful emotional/sleep context, generate one recap per completed morning/night session, and power the dashboard from stored observations.

**Architecture:** FastAPI owns orchestration and privileged credentials. Each user message is screened for urgent safety language, classified locally, normalized, optionally reclassified by GPT-5-mini when confidence is low, persisted, and passed to GPT-5 with bounded recent and historical context. Supabase is the system of record and enforces user ownership with row-level security.

**Canonical internal values:**

- Emotions: `joy`, `sadness`, `anger`, `fear`, `surprise`, `love`, `neutral`
- Domains: `relationship`, `sleep`, `work`, `health`, `sleep_substances`
- Sleep substances: `caffeine`, `alcohol`, `nicotine`, `sleep_medication`, `other_stimulant`, `other_sedative`
- Extracted fields: `sleep_hours`, `wake_time`, `confidence`, `source`
- Indonesian display names remain frontend presentation mappings; database/API values remain stable English identifiers.

## Phase 1: Configuration and authentication

**Files:** modify `backend/app/config.py`, `backend/app/deps.py`, `backend/requirements.txt`, and `backend/README.md`; create `backend/tests/test_config.py` and `backend/tests/test_auth.py`.

1. Add failing tests for missing Foundry credentials, numeric settings, and valid development configuration.
2. Replace ad-hoc environment reads with typed Pydantic settings and redact all credentials from errors/logs.
3. Add the async OpenAI SDK, JWKS HTTP support, Transformers/PyTorch dependencies, and test tooling with compatible version ranges.
4. Replace hard-coded HS256 verification with cached Supabase JWKS verification and key-rotation handling. Keep the shared JWT secret only as an explicit legacy-development option.
5. Test valid, expired, wrong-audience, wrong-project, unknown-key, and rotated-key tokens.
6. Build the OpenAI-compatible base URL by appending `/openai/v1/` to the configured Foundry resource endpoint. Pass Foundry deployment names as `model`; do not add an API-version variable for this v1 route.

**Acceptance:** The service fails fast with useful messages, never exposes credentials, and accepts current Supabase asymmetric JWTs.

## Phase 2: Database migration and ownership

**Files:** create a Supabase CLI migration, update `backend/sql/schema.sql`, and create database-contract tests.

1. Add `message_analyses`: one row per analyzed user message with canonical emotions/domains/substances, extracted sleep values, confidence, source (`local`, `foundry_fallback`, or `rules`), risk level, model ID/revision, and timestamps.
2. Add `session_recaps`: unique `session_id`, Indonesian title/summary, emotional trend, sleep observations, and generation metadata.
3. Add minimal `safety_events`; do not duplicate full message text by default.
4. Link sleep-factor occurrences to `session_id` and `message_id`; distinguish user reports from inferred correlations.
5. Enforce one active session per user/check-in type with a partial unique index and make `/chat/start` resume it idempotently.
6. Index user/time, session/time, recap lookup, and weekly factor aggregation paths.
7. Enable row-level security everywhere. Users only read/delete their records; AI writes use the backend service role after JWT ownership validation.
8. Test the migration on a disposable Supabase branch, run database advisors, and document rollback before production.

**Acceptance:** Cross-user access fails, duplicate active sessions/recaps are prevented, and dashboard queries use indexed paths.

## Phase 3: Local-first classifier

**Files:** create `backend/app/schemas/analysis.py`, `backend/app/services/classifier.py`, `backend/app/services/analysis_normalizer.py`, classifier tests, and an Indonesian/English fixture dataset.

1. Define strict Pydantic output models for the canonical values. Unknown labels never reach storage.
2. Load the pretrained Indonesian model once at process startup and expose raw labels/probabilities behind a small interface.
3. Maintain an explicit, versioned mapping from pretrained labels to the seven app emotions. Missing or unmappable classes trigger fallback instead of fabricated confidence.
4. Add deterministic Indonesian/English extraction for time phrases, sleep duration, and sleep substances, retaining a `source` marker.
5. Evaluate slang, negation, sarcasm, neutral ambiguity, all emotions/domains/substances, and mixed Indonesian-English wording.
6. Tune the threshold from the evaluation confusion matrix; `0.65` in the template is only a starting trial.
7. Pin `EMOTION_MODEL_REVISION` to a commit hash before deployment.

**Acceptance:** Confident Indonesian messages stay local, code-switching is covered, and every result validates against the stable contract.

## Phase 4: Foundry fallback and chatbot clients

**Files:** create `backend/app/services/foundry_client.py`, `backend/app/services/fallback_classifier.py`, and unit tests with mocked network calls.

1. Create one application-scoped `AsyncOpenAI` client using the configured Foundry endpoint, API key, timeout, and bounded retries.
2. Use the GPT-5-mini deployment for strict structured fallback matching `AnalysisResult`. All JSON Schema properties are required; nullable values use explicit unions.
3. Invoke fallback only for low confidence, unmappable labels, or ambiguous extraction.
4. Send only the current message and minimal classifier instruction to fallback; never send emotional history for classification.
5. Use `store=False`, omit prompt/response bodies from normal logs, and record only latency, deployment, token usage, outcome, and correlation ID.
6. If Foundry is unavailable, retain a rules-only/neutral analysis and return a controlled chat response.
7. Do not add the Foundry Project SDK yet. `AZURE_AI_FOUNDRY_PROJECT_ENDPOINT` remains optional because PillowTalk stores state in Supabase and does not need Agent Service or Foundry project connections.

**Acceptance:** Confident local messages make zero fallback calls, malformed structured output is rejected, and failure behavior is deterministic.

## Phase 5: Safety gate

**Files:** refactor `backend/app/services/crisis.py`, create `backend/app/services/safety.py`, and add bilingual safety tests.

1. Run deterministic Indonesian/English high-risk phrase screening before any model call.
2. Separate intense emotion from imminent self-harm/violence; emotion confidence alone never creates a crisis event.
3. For high risk, bypass ordinary generation and return empathetic, direct Indonesian safety guidance that encourages immediate human help and displays configured resources.
4. Persist minimal audit metadata rather than a second transcript copy.
5. Test negation, quotations, jokes, historical references, current intent, plan/means, threats toward others, and false positives.
6. Require qualified local review of final crisis wording and resource availability before release.

**Acceptance:** Safety always runs first, high-risk responses do not depend only on a generative model, and normal sadness is not classified as crisis.

## Phase 6: Chat orchestration and bounded memory

**Files:** create `chat_orchestrator.py` and `context_builder.py`; update chat router/schema; add route and orchestration tests.

1. Make `/chat/start` idempotently create or resume a morning/night session.
2. For `/chat/message`: verify ownership, persist the user turn, screen safety, classify/extract, persist analysis/factors, build bounded context, call GPT-5, persist the assistant turn, and return safe UI metadata.
3. Context contains the latest current-session messages, three recent completed recap summaries, and 14-day aggregated emotional/sleep trends—not the full emotional database.
4. Mark user-reported facts versus inference and instruct GPT-5 not to diagnose or claim causation.
5. Use the Foundry Responses API with `store=False`; keep state in Supabase rather than Foundry response IDs.
6. Add per-user rate limiting, correlation IDs, timeout/cancellation, idempotency keys, and a calm Indonesian upstream-failure reply.

**Acceptance:** Tenant isolation holds, retries do not duplicate turns, and prompt context stays within configured bounds.

## Phase 7: Recaps

**Files:** create `recap_generator.py`; update recap router/schema; add recap tests.

1. Define completion as explicit user end, final flow turn, or an inactivity close policy. Generate only after completion.
2. Generate a structured Indonesian title/summary, dominant emotions/domains, sleep observations, and cautious non-causal conclusion. Benchmark GPT-5-mini versus GPT-5, then choose by quality/cost.
3. Upsert by `session_id` so retries cannot duplicate recaps.
4. Keep transcripts in messages. Recap list returns summaries; recap detail returns the owned transcript.
5. Make delete transactional/cascading and require the Flutter optimistic UI to roll back when deletion fails.

**Acceptance:** Each morning/night session has at most one recap and recap detail returns its exact owned transcript.

## Phase 8: Database-backed dashboard

**Files:** update `backend/app/services/factors.py`, profile router/schema, and add dashboard reconciliation tests.

1. Aggregate weekly sleep from normalized user-reported records.
2. Aggregate relationship, work, health, sleep, caffeine, alcohol, nicotine, sleep medicine, other stimulant, and other sedative occurrences.
3. Use observational wording, never causal claims.
4. Require minimum samples and return `insufficient_data` when a trend is not supportable.
5. Return canonical API values plus uncertainty/sample size; map Indonesian labels in Flutter.

**Acceptance:** Dashboard totals reconcile with source rows and honor the user's timezone/day boundaries.

## Phase 9: Flutter integration after UI freeze

1. Consume the final OpenAPI contract with typed DTOs.
2. Pass only `SUPABASE_URL`, public `SUPABASE_ANON_KEY`, and `API_BASE_URL` through `--dart-define`; never ship the Foundry or Supabase service-role key.
3. Add loading, retry, offline, idempotency, and delete rollback states.
4. Revise the old fixed-flow test workbook for fallback, safety, recap, authorization, and dashboard reconciliation.
5. Add Android release Internet permission before device/release testing.

## Execution order and release gates

1. Configuration/auth and database schema.
2. Classifier contract, local evaluation, and Foundry fallback.
3. Safety gate, then chatbot orchestration.
4. Recaps and dashboard read models.
5. Flutter integration after design freeze.

Release only after tests and OpenAPI review pass; row-level-security tests prove tenant isolation; bilingual classifier metrics/confusion matrix are approved; safety cases receive human review; load testing validates local-model memory and API latency; and no key, transcript, or sensitive prompt appears in git or ordinary logs.
