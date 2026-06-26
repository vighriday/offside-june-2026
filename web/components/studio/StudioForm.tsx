"use client";

import { useState } from "react";
import type { StudioFormPayload } from "@/lib/studioClient";

const EXAMPLE: StudioFormPayload = {
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

export function StudioForm({ disabled, onRun }: {
  disabled: boolean;
  onRun: (p: StudioFormPayload) => void;
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
        <button type="button" onClick={() => setForm(EXAMPLE)}>Load an example</button>
        <button type="submit" disabled={!canRun}>Decompose live</button>
      </div>
      {!canRun && filledQuotes.length < 2 && (
        <p className="studio-form__hint">Add at least two named quotes in opposed valence for Cultural bias to fire.</p>
      )}
    </form>
  );
}
