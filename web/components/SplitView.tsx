"use client";

import { useState } from "react";
import type { IncidentBundle, SplitAxis } from "@/types/contract";
import { SplitCell } from "./SplitCell";
import { CitationPanel } from "./CitationPanel";

interface SplitViewProps {
  bundle: IncidentBundle;
}

// THE SPLIT — the core artifact. Four equal cells, one per axis. A plain-language intro
// and a state legend sit ABOVE the grid so the diagnostic is readable before it's seen.
// Cells are visible by default (a CSS entrance animates them in but can never leave them
// stuck dim); selecting one traces its reading to source.
export function SplitView({ bundle }: SplitViewProps) {
  const [selectedAxis, setSelectedAxis] = useState<SplitAxis | null>(null);
  const selectedCell =
    bundle.split.cells.find((c) => c.axis === selectedAxis) ?? null;

  return (
    <section className="split-view" aria-label="THE SPLIT — disagreement diagnostic">
      <header className="split-view__header">
        <p className="split-view__eyebrow">THE SPLIT</p>
        <p className="split-view__prompt">Why this moment never resolved</p>
        <p className="split-view__intro">
          A disagreement can come from four places. OFFSIDE checks all four against the
          evidence and marks which ones are actually in play here. Click any box to see the
          source behind it.
        </p>
      </header>

      <div className="split-legend" aria-hidden>
        <span className="split-legend__item" data-k="present">
          <span className="split-legend__swatch" /> Present — a live reason it stays contested
        </span>
        <span className="split-legend__item" data-k="out">
          <span className="split-legend__swatch" /> Ruled out — checked and not the reason
        </span>
        <span className="split-legend__item" data-k="nd">
          <span className="split-legend__swatch" /> Not documented — no evidence either way
        </span>
      </div>

      <div className="split-view__body">
        <div className="split-view__grid" role="group" aria-label="The four dimensions">
          {bundle.split.cells.map((cell, i) => (
            <SplitCell
              key={cell.axis}
              cell={cell}
              index={i}
              selected={cell.axis === selectedAxis}
              onSelect={(axis) =>
                setSelectedAxis((cur) => (cur === axis ? null : axis))
              }
            />
          ))}
        </div>

        <CitationPanel cell={selectedCell} citations={bundle.citations} />
      </div>

      <p className="split-view__headline">{bundle.split.headline}</p>

      {!selectedCell && (
        <p className="split-view__hint">↑ Click any box to trace it to the real source page.</p>
      )}
    </section>
  );
}
