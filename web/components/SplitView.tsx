"use client";

import { useState } from "react";
import { motion } from "motion/react";
import type { IncidentBundle, SplitAxis } from "@/types/contract";
import { SplitCell } from "./SplitCell";
import { CitationPanel } from "./CitationPanel";

interface SplitViewProps {
  bundle: IncidentBundle;
}

// THE SPLIT — the core artifact. Four equal cells, one per axis, revealed in sequence
// after the settled fact; selecting a cell traces its reading to source. The headline
// resolves last, after the cells have settled, so the diagnostic reads before the verdict.
export function SplitView({ bundle }: SplitViewProps) {
  const [selectedAxis, setSelectedAxis] = useState<SplitAxis | null>(null);
  const selectedCell =
    bundle.split.cells.find((c) => c.axis === selectedAxis) ?? null;

  // The headline reveals after the last cell's entrance (4 cells × 0.15s stagger + buffer).
  const headlineDelay = 0.15 * bundle.split.cells.length + 0.45;

  return (
    <section className="split-view" aria-label="THE SPLIT — disagreement diagnostic">
      <header className="split-view__header">
        <p className="split-view__eyebrow">THE SPLIT — disagreement diagnostic</p>
        <p className="split-view__prompt">Why this moment never resolved</p>
      </header>

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

      <motion.p
        className="split-view__headline"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6, delay: headlineDelay, ease: "easeOut" }}
      >
        {bundle.split.headline}
      </motion.p>

      {!selectedCell && (
        <p className="split-view__hint">Select any dimension to trace it to source.</p>
      )}
    </section>
  );
}
