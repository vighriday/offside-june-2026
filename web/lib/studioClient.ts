import type { IncidentBundle, StudioStreamEvent } from "@/types/contract";
import exampleFixture from "@/fixtures/studio-example.json";

export interface HealthResult {
  ok: boolean;
  ollama: boolean;
  models: { granite: boolean; embed: boolean; guardian: boolean };
}

export interface StudioFormPayload {
  title: string;
  settled_statement: string;
  historical_note: string;
  quotes: { speaker: string; source: string; text: string }[];
  tactical_note: string | null;
}

export const STUDIO_BASE =
  process.env.NEXT_PUBLIC_STUDIO_BASE ?? "http://localhost:8000";

export async function checkHealth(base = STUDIO_BASE): Promise<HealthResult | null> {
  // Fail FAST when no backend is reachable. On the public ($0 static) site there is no
  // backend, so this fetch would otherwise hang until the browser's default timeout —
  // leaving the UI stuck in its "unknown" state for tens of seconds and making the form
  // appear to do nothing. A short abort flips us into the no-backend fallback immediately:
  // the banner shows and "Load an example" renders the pre-baked fixture instantly.
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 2500);
  try {
    const r = await fetch(`${base}/health`, { cache: "no-store", signal: controller.signal });
    if (!r.ok) return null;
    return (await r.json()) as HealthResult;
  } catch {
    return null; // backend not reachable (or timed out) → public-site fallback
  } finally {
    clearTimeout(timeout);
  }
}

// POST the form, read the SSE stream, call onEvent for each parsed event.
export async function decomposeStream(
  payload: StudioFormPayload,
  onEvent: (e: StudioStreamEvent) => void,
  base = STUDIO_BASE,
): Promise<void> {
  const r = await fetch(`${base}/decompose`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!r.ok || !r.body) throw new Error(`decompose failed: ${r.status}`);
  const reader = r.body.getReader();
  const dec = new TextDecoder();
  let buf = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    // SSE frames are separated by a blank line; each "data:" line carries one JSON event.
    const frames = buf.split("\n\n");
    buf = frames.pop() ?? "";
    for (const frame of frames) {
      const line = frame.split("\n").find((l) => l.startsWith("data:"));
      if (!line) continue;
      const json = line.slice(line.indexOf(":") + 1).trim();
      if (json) onEvent(JSON.parse(json) as StudioStreamEvent);
    }
  }
}

// Returns the pre-baked Studio example fixture so the public static site can show a
// complete real result with no backend. Uses a static import (resolveJsonModule: true)
// because web/fixtures/ is not under public/ and is therefore not served at a public URL.
export async function loadExampleBundle(): Promise<IncidentBundle> {
  return exampleFixture as IncidentBundle;
}

export type { IncidentBundle };
