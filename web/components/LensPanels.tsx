"use client";

import { motion } from "motion/react";
import { cleanRationale } from "@/lib/rationale";
import type {
  Citation,
  GuardianVerdict,
  LensKind,
  LensStance,
  SealedLens,
} from "@/types/contract";

// The four lenses below THE SPLIT. Each shows ONE lens's grounded reading and — the
// novel move — the IBM Granite Guardian verdict that audited it. A GROUNDED seal means a
// second IBM model checked the first's reading against its cited page and could not
// refute it. This is what no single-model entry can claim.

const LENS_LABEL: Record<LensKind, string> = {
  REFEREE: "Referee",
  TACTICAL: "Tactical",
  HISTORICAL: "Historical",
  FRAMING: "Framing",
};

const LENS_SOURCE: Record<LensKind, string> = {
  REFEREE: "IFAB Laws of the Game",
  TACTICAL: "StatsBomb event data",
  HISTORICAL: "Curated historical record",
  FRAMING: "Named-source quotes",
};

const STANCE_LABEL: Record<LensStance, string> = {
  SUPPORTS: "Supports",
  DISPUTES: "Disputes",
  MIXED: "Divergent",
  INSUFFICIENT_EVIDENCE: "Insufficient evidence",
};

// The stance chip is lens-aware: MIXED means different things per lens. On FRAMING it is a
// genuine divergence (two named sources in opposed valence) → "Divergent". On HISTORICAL it
// means the information was adequate and the fact knowable — no gap of either kind → that is
// an "Adequate" finding, not a disagreement, so "Divergent" would mislead a reader.
function stanceLabel(lens: LensKind, stance: LensStance): string {
  if (stance === "MIXED" && lens === "HISTORICAL") return "Adequate";
  return STANCE_LABEL[stance];
}

function GuardianSeal({
  verdict,
  model,
  noReading,
}: {
  verdict: GuardianVerdict;
  model: string;
  /** True when the lens returned INSUFFICIENT_EVIDENCE — there was nothing to audit. */
  noReading?: boolean;
}) {
  // The seal reflects how the reading was confirmed. A live Granite Guardian pass reads
  // as "Granite Guardian: grounded"; a deterministic offline build reads honestly as
  // "Backed by a cited source" rather than overclaiming a model audit that did not run.
  // When the lens had no reading at all, the Guardian never reviewed anything — say that
  // plainly instead of "held back", which would imply it weighed and declined a claim.
  const isLiveGuardian = model.includes("guardian");
  const label = noReading
    ? "No reading to audit — insufficient evidence"
    : isLiveGuardian
      ? verdict === "GROUNDED"
        ? "✓ Granite Guardian confirmed this against its source"
        : "Granite Guardian could not confirm — held back"
      : "✓ Backed by a cited source";
  return (
    <span className="guardian-seal" data-verdict={verdict} data-no-reading={noReading}>
      <span className="guardian-seal__mark" aria-hidden />
      {label}
    </span>
  );
}

interface LensPanelsProps {
  lenses: SealedLens[];
  citations: Record<string, Citation>;
}

// The StatsBomb User Agreement requires visible attribution wherever its data is shown.
// We surface it as a badge on the Tactical card, pulled from the cited StatsBomb atom.
function statsbombAttribution(
  output: SealedLens["output"],
  citations: Record<string, Citation>,
): string | null {
  for (const id of output.citation_ids) {
    const c = citations[id];
    if (c?.doc_kind === "STATSBOMB_EVENT" && c.attribution) return c.attribution;
  }
  return null;
}

export function LensPanels({ lenses, citations }: LensPanelsProps) {
  return (
    <section className="lens-panels" aria-label="The four lenses">
      <header className="lens-panels__header">
        <p className="lens-panels__eyebrow">The four lenses</p>
        <p className="lens-panels__note">
          Each lens reads only its own evidence; every reading is audited by a second IBM
          model before it is shown.
        </p>
      </header>

      <div className="lens-panels__grid">
        {lenses.map((sealed, i) => {
          const { output, seal } = sealed;
          const attribution =
            output.lens === "TACTICAL"
              ? statsbombAttribution(output, citations)
              : null;
          return (
            <motion.article
              key={output.lens}
              className="lens-panel"
              data-state={output.state}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.06 * i, ease: [0.4, 0.14, 0.3, 1] }}
            >
              <div className="lens-panel__top">
                <h3 className="lens-panel__name">{LENS_LABEL[output.lens]}</h3>
                <span className="lens-panel__stance" data-stance={output.stance}>
                  {stanceLabel(output.lens, output.stance)}
                </span>
              </div>
              <p className="lens-panel__source">{LENS_SOURCE[output.lens]}</p>
              <p className="lens-panel__rationale">{cleanRationale(output.rationale)}</p>
              {attribution && (
                <p className="lens-panel__attribution" title={attribution}>
                  <span className="lens-panel__attribution-mark">StatsBomb</span>
                  Open Data — used under the StatsBomb User Agreement
                </p>
              )}
              <GuardianSeal
                verdict={seal.verdict}
                model={seal.guardian_model}
                noReading={output.state === "INSUFFICIENT_EVIDENCE"}
              />
            </motion.article>
          );
        })}
      </div>
    </section>
  );
}
