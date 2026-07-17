import { test } from "node:test";
import assert from "node:assert/strict";

import {
  parseTtsRequest,
  resolveVoiceName,
  buildSynthesizeRequestBody,
  extractAudioContent,
  InvalidTtsRequestError,
  GoogleTtsResponseError,
  DEFAULT_VOICE_NAMES,
  WIND_DOWN_AUDIO_CONFIG,
  MAX_TEXT_LENGTH,
} from "./request.ts";

test("parseTtsRequest trims text and accepts a supported language", () => {
  const result = parseTtsRequest({ text: "  Selamat malam  ", languageCode: "id-ID" });
  assert.deepEqual(result, { text: "Selamat malam", languageCode: "id-ID" });
});

test("parseTtsRequest rejects a missing/non-string text field", () => {
  assert.throws(() => parseTtsRequest({ languageCode: "id-ID" }), InvalidTtsRequestError);
  assert.throws(() => parseTtsRequest({ text: 42, languageCode: "id-ID" }), InvalidTtsRequestError);
});

test("parseTtsRequest rejects empty (or whitespace-only) text", () => {
  assert.throws(() => parseTtsRequest({ text: "   ", languageCode: "en-US" }), InvalidTtsRequestError);
});

test("parseTtsRequest rejects text longer than the 2000 character limit", () => {
  const tooLong = "a".repeat(MAX_TEXT_LENGTH + 1);
  assert.throws(
    () => parseTtsRequest({ text: tooLong, languageCode: "en-US" }),
    InvalidTtsRequestError,
  );
});

test("parseTtsRequest rejects an unsupported language code", () => {
  assert.throws(
    () => parseTtsRequest({ text: "hello", languageCode: "fr-FR" }),
    InvalidTtsRequestError,
  );
});

test("resolveVoiceName defaults to the calm Indonesian wind-down voice", () => {
  assert.equal(resolveVoiceName("id-ID"), DEFAULT_VOICE_NAMES["id-ID"]);
  assert.equal(resolveVoiceName("id-ID", null), DEFAULT_VOICE_NAMES["id-ID"]);
  assert.equal(resolveVoiceName("id-ID", ""), DEFAULT_VOICE_NAMES["id-ID"]);
});

test("resolveVoiceName honors GOOGLE_TTS_VOICE_ID override for Indonesian only", () => {
  assert.equal(resolveVoiceName("id-ID", "id-ID-Wavenet-C"), "id-ID-Wavenet-C");
  // English is unaffected by the Indonesian voice override.
  assert.equal(resolveVoiceName("en-US", "id-ID-Wavenet-C"), DEFAULT_VOICE_NAMES["en-US"]);
});

test("buildSynthesizeRequestBody shapes a Google-compatible payload with the wind-down audio profile", () => {
  const body = buildSynthesizeRequestBody({ text: "Tarik napas perlahan.", languageCode: "id-ID" });
  assert.deepEqual(body, {
    input: { text: "Tarik napas perlahan." },
    voice: { languageCode: "id-ID", name: "id-ID-Wavenet-A" },
    audioConfig: WIND_DOWN_AUDIO_CONFIG,
  });
});

test("buildSynthesizeRequestBody applies a voice override when given one", () => {
  const body = buildSynthesizeRequestBody(
    { text: "hi", languageCode: "id-ID" },
    "id-ID-Wavenet-D",
  );
  assert.equal(body.voice.name, "id-ID-Wavenet-D");
});

test("extractAudioContent returns the base64 payload from a valid Google response", () => {
  assert.equal(extractAudioContent({ audioContent: "aGVsbG8=" }), "aGVsbG8=");
});

test("extractAudioContent rejects a response missing audioContent", () => {
  assert.throws(() => extractAudioContent({}), GoogleTtsResponseError);
  assert.throws(() => extractAudioContent({ audioContent: "" }), GoogleTtsResponseError);
  assert.throws(() => extractAudioContent(null), GoogleTtsResponseError);
});
