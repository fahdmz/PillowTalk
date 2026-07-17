// Pure request/response logic for the `google-tts` Edge Function — no Deno
// or network APIs here on purpose, so this module can be unit-tested with
// Node's built-in test runner (see request.test.ts) instead of needing the
// Deno/Supabase CLI toolchain. `index.ts` is the thin Deno HTTP wrapper that
// calls into this file.

export const SYNTHESIZE_URL = "https://texttospeech.googleapis.com/v1/text:synthesize";

export const MAX_TEXT_LENGTH = 2000;

export const SUPPORTED_LANGUAGE_CODES = ["id-ID", "en-US"] as const;
export type SupportedLanguageCode = (typeof SUPPORTED_LANGUAGE_CODES)[number];

// Product requirement: the Indonesian voice must read as a calm woman, not
// a lively/upbeat one — Wavenet-A is Google's female id-ID voice. The
// English default only needs to exist for the app's English mode; it isn't
// part of the "wind-down voice" requirement.
export const DEFAULT_VOICE_NAMES: Record<SupportedLanguageCode, string> = {
  "id-ID": "id-ID-Wavenet-A",
  "en-US": "en-US-Wavenet-F",
};

// Wind-down audio profile per product requirement 9: calm and restrained
// rather than lively, suitable for helping someone settle down before sleep.
export const WIND_DOWN_AUDIO_CONFIG = {
  audioEncoding: "MP3",
  speakingRate: 0.88,
  pitch: -1,
  volumeGainDb: -2,
} as const;

export class InvalidTtsRequestError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "InvalidTtsRequestError";
  }
}

export class GoogleTtsResponseError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "GoogleTtsResponseError";
  }
}

export interface TtsRequestBody {
  text: string;
  languageCode: SupportedLanguageCode;
}

function isSupportedLanguageCode(value: unknown): value is SupportedLanguageCode {
  return (
    typeof value === "string" &&
    (SUPPORTED_LANGUAGE_CODES as readonly string[]).includes(value)
  );
}

/** Validates and normalizes an incoming `{ text, languageCode }` payload. */
export function parseTtsRequest(body: unknown): TtsRequestBody {
  if (typeof body !== "object" || body === null) {
    throw new InvalidTtsRequestError("Request body must be a JSON object");
  }
  const { text, languageCode } = body as Record<string, unknown>;

  if (typeof text !== "string") {
    throw new InvalidTtsRequestError("`text` must be a string");
  }
  const trimmed = text.trim();
  if (trimmed.length === 0) {
    throw new InvalidTtsRequestError("`text` must not be empty");
  }
  if (trimmed.length > MAX_TEXT_LENGTH) {
    throw new InvalidTtsRequestError(
      `\`text\` must be at most ${MAX_TEXT_LENGTH} characters`
    );
  }
  if (!isSupportedLanguageCode(languageCode)) {
    throw new InvalidTtsRequestError(
      `\`languageCode\` must be one of: ${SUPPORTED_LANGUAGE_CODES.join(", ")}`
    );
  }

  return { text: trimmed, languageCode };
}

/**
 * Resolves which Google TTS voice to request. `voiceOverride` (the
 * `GOOGLE_TTS_VOICE_ID` secret) only applies to the Indonesian wind-down
 * voice, so it can be swapped in production without touching English or
 * shipping a new app build.
 */
export function resolveVoiceName(
  languageCode: SupportedLanguageCode,
  voiceOverride?: string | null,
): string {
  if (languageCode === "id-ID" && voiceOverride && voiceOverride.trim().length > 0) {
    return voiceOverride.trim();
  }
  return DEFAULT_VOICE_NAMES[languageCode];
}

/** Builds the request body for Google's `text:synthesize` REST endpoint. */
export function buildSynthesizeRequestBody(
  request: TtsRequestBody,
  voiceOverride?: string | null,
) {
  return {
    input: { text: request.text },
    voice: {
      languageCode: request.languageCode,
      name: resolveVoiceName(request.languageCode, voiceOverride),
    },
    audioConfig: WIND_DOWN_AUDIO_CONFIG,
  };
}

/**
 * Pulls `audioContent` out of Google's synthesize response, validating its
 * shape rather than trusting an upstream API response blindly.
 */
export function extractAudioContent(googleResponse: unknown): string {
  if (typeof googleResponse !== "object" || googleResponse === null) {
    throw new GoogleTtsResponseError("Google TTS response must be a JSON object");
  }
  const { audioContent } = googleResponse as Record<string, unknown>;
  if (typeof audioContent !== "string" || audioContent.length === 0) {
    throw new GoogleTtsResponseError("Google TTS response is missing `audioContent`");
  }
  return audioContent;
}
