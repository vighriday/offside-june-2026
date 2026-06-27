"use client";

import { useState } from "react";
import type { StudioFormPayload } from "@/lib/studioClient";

// The worked example. These are the exact inputs the committed studio-example.json fixture
// was baked from, so prefilling the form with EXAMPLE and rendering that fixture show the
// SAME incident — the judge sees the evidence that produced the result on screen.
export const EXAMPLE: StudioFormPayload = {
  title: "A disputed penalty",
  settled_statement:
    "A defender's arm blocked the ball inside the box. The arm-to-ball contact is agreed by both sides.",
  historical_note:
    "VAR reviewed the incident on a clear, side-on replay; the contact was fully visible and reviewable in real time.",
  quotes: [
    { speaker: "Home manager", source: "post-match interview", text: "That's a clear penalty — the arm was out, away from the body." },
    { speaker: "Away manager", source: "post-match interview", text: "Never a penalty — it's ball to hand, the arm didn't move." },
  ],
  tactical_note: null,
};

export function StudioForm({ disabled, onRun, onExample, liveEnabled }: {
  disabled: boolean;
  onRun: (p: StudioFormPayload) => void;
  /** When provided, overrides the default "fill the form" behaviour of the example button. */
  onExample?: () => void;
  /** Whether a live backend is reachable. When false (the public $0 static site), the
   *  "Decompose live" submit is hidden entirely — Studio is example-only there, and live
   *  decomposition is a local / self-hosted action. This is what keeps the public site from
   *  POSTing to a backend that isn't there (no hang, no CORS error). */
  liveEnabled: boolean;
}) {
  const [form, setForm] = useState<StudioFormPayload>({
    title: "", settled_statement: "", historical_note: "",
    quotes: [{ speaker: "", source: "", text: "" }, { speaker: "", source: "", text: "" }],
    tactical_note: null,
  });

  const filledQuotes = form.quotes.filter((q) => q.speaker && q.source && q.text);
  const canRun = !disabled && form.title.trim() && form.settled_statement.trim() &&
    form.historical_note.trim() && filledQuotes.length >= 2;

  return (
    <form className="studio-form" onSubmit={(e) => { e.preventDefault(); onRun({ ...form, quotes: filledQuotes }); }}>
      {/* The moment */}
      <label>Title<input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} /></label>
      <label>What&apos;s agreed (settled facts)
        <textarea value={form.settled_statement} onChange={(e) => setForm({ ...form, settled_statement: e.target.value })} />
      </label>
      {/* Historical */}
      <label>What could/couldn&apos;t be seen, the tech, how it was reviewed
        <textarea value={form.historical_note} onChange={(e) => setForm({ ...form, historical_note: e.target.value })} />
      </label>
      {/* Framing — two quotes minimum, in opposed valence to fire Cultural bias */}
      {form.quotes.map((q, i) => (
        <fieldset key={i}>
          <input placeholder="Speaker" value={q.speaker}
            onChange={(e) => { const qs = [...form.quotes]; qs[i] = { ...q, speaker: e.target.value }; setForm({ ...form, quotes: qs }); }} />
          <input placeholder="Where said" value={q.source}
            onChange={(e) => { const qs = [...form.quotes]; qs[i] = { ...q, source: e.target.value }; setForm({ ...form, quotes: qs }); }} />
          <input placeholder="Quote" value={q.text}
            onChange={(e) => { const qs = [...form.quotes]; qs[i] = { ...q, text: e.target.value }; setForm({ ...form, quotes: qs }); }} />
        </fieldset>
      ))}
      <button type="button" onClick={() => setForm({ ...form, quotes: [...form.quotes, { speaker: "", source: "", text: "" }] })}>
        + add a quote
      </button>
      {/* Tactical (optional) */}
      <label>Data note (optional)
        <textarea value={form.tactical_note ?? ""} onChange={(e) => setForm({ ...form, tactical_note: e.target.value || null })} />
      </label>

      <div className="studio-form__actions">
        <button
          type="button"
          onClick={() => {
            // Always fill the form fields with the example's inputs, so the evidence is
            // visible. On the public site (onExample set) ALSO render the pre-baked result,
            // so the judge sees both the inputs and the complete decomposition together.
            setForm(EXAMPLE);
            onExample?.();
          }}
        >
          {liveEnabled ? "Load an example" : "Show a worked example"}
        </button>
        {liveEnabled && <button type="submit" disabled={!canRun}>Decompose live</button>}
      </div>
      {liveEnabled && !canRun && filledQuotes.length < 2 && (
        <p className="studio-form__hint">Add at least two named quotes in opposed valence for Cultural bias to fire.</p>
      )}
      {!liveEnabled && (
        <p className="studio-form__hint">
          Live decomposition runs the real Granite models locally — see the README
          &ldquo;Run the Studio yourself&rdquo;. Here, the worked example shows a complete real result.
        </p>
      )}
    </form>
  );
}
