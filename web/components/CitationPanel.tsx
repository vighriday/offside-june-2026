"use client";

import { AnimatePresence, motion } from "motion/react";
import { cleanRationale } from "@/lib/rationale";
import type { Citation, SplitCell } from "@/types/contract";

interface CitationPanelProps {
  /** The selected cell, or null when nothing is selected. */
  cell: SplitCell | null;
  citations: Record<string, Citation>;
}

// The click-to-source panel: when a cell is selected, its cited passages resolve here,
// each showing the exact source, page, and verbatim extracted text. This is the spine of
// the trust claim — every reading points at a real passage a judge can verify.
export function CitationPanel({ cell, citations }: CitationPanelProps) {
  return (
    <AnimatePresence mode="wait">
      {cell && cell.citation_ids.length > 0 && (
        <motion.aside
          key={cell.axis}
          className="citation-panel"
          initial={{ opacity: 0, x: 16 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: 16 }}
          transition={{ duration: 0.28, ease: [0.4, 0.14, 0.3, 1] }}
        >
          <p className="citation-panel__eyebrow">Traced to source</p>
          <h3 className="citation-panel__rationale">{cleanRationale(cell.rationale)}</h3>

          <ol className="citation-panel__list">
            {cell.citation_ids.map((id) => {
              const c = citations[id];
              if (!c) return null;
              return (
                <li key={id} className="citation-panel__item">
                  <div className="citation-panel__source">
                    <span className="citation-panel__doc">{c.source_doc}</span>
                    {c.page !== null && (
                      <span className="citation-panel__page">p.&nbsp;{c.page}</span>
                    )}
                  </div>
                  <p className="citation-panel__text">“{c.extracted_text}”</p>
                  {c.attribution && (
                    <p className="citation-panel__attribution">{c.attribution}</p>
                  )}
                </li>
              );
            })}
          </ol>
        </motion.aside>
      )}
    </AnimatePresence>
  );
}
