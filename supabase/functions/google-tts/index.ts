// Supabase Edge Function: synthesizes AI chat replies into speech via
// Google Cloud Text-to-Speech, so the Google service-account credential
// never has to live in the Flutter app. Authentication is enforced by the
// platform (`verify_jwt = true` in supabase/config.toml) before this code
// ever runs — a request without a valid Supabase user access token gets a
// 401 automatically. See https://supabase.com/docs/guides/functions/auth.
import { GoogleAuth } from "npm:google-auth-library@10.9.0";

import {
  SYNTHESIZE_URL,
  parseTtsRequest,
  buildSynthesizeRequestBody,
  extractAudioContent,
  InvalidTtsRequestError,
  GoogleTtsResponseError,
} from "./request.ts";

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

function jsonResponse(body: unknown, init: ResponseInit = {}) {
  return new Response(JSON.stringify(body), {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "Cache-Control": "private, no-store",
      ...CORS_HEADERS,
      ...init.headers,
    },
  });
}

// The service-account JSON and any voice override are read once per cold
// start, not per request — neither ever leaves this server-side function.
const credentialsJson = Deno.env.get("GOOGLE_TTS_CREDENTIALS");
const voiceOverride = Deno.env.get("GOOGLE_TTS_VOICE_ID");

let cachedAuth: GoogleAuth | null = null;

function getAuth(): GoogleAuth {
  if (cachedAuth) return cachedAuth;
  if (!credentialsJson) {
    throw new Error("GOOGLE_TTS_CREDENTIALS is not configured");
  }
  cachedAuth = new GoogleAuth({
    credentials: JSON.parse(credentialsJson),
    scopes: ["https://www.googleapis.com/auth/cloud-platform"],
  });
  return cachedAuth;
}

async function getAccessToken(): Promise<string> {
  const client = await getAuth().getClient();
  const token = await client.getAccessToken();
  if (!token.token) {
    throw new Error("Failed to obtain a Google access token");
  }
  return token.token;
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: CORS_HEADERS });
  }
  if (req.method !== "POST") {
    return jsonResponse({ error: "Method not allowed" }, { status: 405 });
  }

  let payload: unknown;
  try {
    payload = await req.json();
  } catch {
    return jsonResponse({ error: "Request body must be valid JSON" }, { status: 400 });
  }

  let ttsRequest;
  try {
    ttsRequest = parseTtsRequest(payload);
  } catch (error) {
    if (error instanceof InvalidTtsRequestError) {
      return jsonResponse({ error: error.message }, { status: 400 });
    }
    throw error;
  }

  try {
    const accessToken = await getAccessToken();
    const response = await fetch(SYNTHESIZE_URL, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(buildSynthesizeRequestBody(ttsRequest, voiceOverride)),
    });

    if (!response.ok) {
      const detail = await response.text();
      console.error("Google TTS request failed", response.status, detail);
      return jsonResponse({ error: "Speech synthesis failed upstream" }, { status: 502 });
    }

    const audioContent = extractAudioContent(await response.json());
    return jsonResponse({ audioContent });
  } catch (error) {
    if (error instanceof GoogleTtsResponseError) {
      console.error("Google TTS returned an unusable response", error.message);
      return jsonResponse({ error: "Speech synthesis failed upstream" }, { status: 502 });
    }
    console.error("Unexpected google-tts failure", error);
    return jsonResponse({ error: "Internal error" }, { status: 500 });
  }
});
