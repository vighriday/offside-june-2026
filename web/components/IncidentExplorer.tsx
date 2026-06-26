"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import type { IncidentBundle } from "@/types/contract";
import { SettledFact } from "./SettledFact";
import { SplitView } from "./SplitView";
import { LensPanels } from "./LensPanels";
import { ProvenanceFooter } from "./ProvenanceFooter";
import { DivergenceLineage } from "./DivergenceLineage";
import { RuleEvolution } from "./RuleEvolution";
import { FalsificationPanel } from "./FalsificationPanel";
import { HowItWorks } from "./HowItWorks";
import { Hero } from "./Hero";

export interface LoadedBundle {
  bundle: IncidentBundle;
  isSample: boolean;
}

interface IncidentExplorerProps {
  incidents: LoadedBundle[];
}

// Orchestrates the explorer: the Divergence Lineage chain selects an incident, THE SPLIT
// changes, and a callout names the axis that flipped — the proof the diagnostic is computed
// from evidence, not pre-written. Lampard additionally surfaces the Rule Evolution toggle.
export function IncidentExplorer({ incidents }: IncidentExplorerProps) {
  const [active, setActive] = useState(0);
  const current = incidents[active];
  const { bundle, isSample } = current;
  const bundles = incidents.map((i) => i.bundle);

  return (
    <main className="incident">
      {isSample && (
        <p className="incident__sample-banner">
          ⚽ Pre-bake sample fixture — the audited bundle replaces this once the bake runs.
        </p>
      )}

      <div className="incident__inner">
        <Hero />

        <HowItWorks />

        {bundles.length > 1 && (
          <DivergenceLineage
            incidents={bundles}
            activeId={bundle.incident_id}
            onSelect={setActive}
          />
        )}

        {/* Re-key on incident id so the inner staged reveals replay on switch. */}
        <div key={bundle.incident_id}>
          <SettledFact
            fact={bundle.settled_fact}
            title={bundle.title}
            incidentId={bundle.incident_id}
          />

          {active > 0 && (
            <GeneralizationCallout
              prev={bundles[active - 1]}
              current={bundle}
            />
          )}

          <SplitView bundle={bundle} />

          {bundle.probes && bundle.probes.length > 0 && (
            <FalsificationPanel probes={bundle.probes} />
          )}

          {bundle.rule_evolution && <RuleEvolution evo={bundle.rule_evolution} />}

          <LensPanels lenses={bundle.lenses} citations={bundle.citations} />
          <ProvenanceFooter
            provenance={bundle.provenance}
            citations={bundle.citations}
          />
        </div>
      </div>
    </main>
  );
}

const AXIS_LABEL: Record<string, string> = {
  RULE_AMBIGUITY: "Rule ambiguity",
  INDETERMINACY: "Indeterminacy",
  DECISION_TIME_DEFICIT: "Decision-time deficit",
  CULTURAL_PRIOR_BIAS: "Cultural prior bias",
};

// Names the axis whose state differs from the previously-viewed incident — making the
// "same engine, different diagnosis" proof explicit rather than something to spot.
function GeneralizationCallout({
  prev,
  current,
}: {
  prev: IncidentBundle;
  current: IncidentBundle;
}) {
  const prevStates = Object.fromEntries(prev.split.cells.map((c) => [c.axis, c.state]));
  const flipped = current.split.cells.filter((c) => prevStates[c.axis] !== c.state);
  if (!flipped.length) return null;

  return (
    <AnimatePresence>
      <motion.p
        className="generalization-callout"
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35 }}
      >
        <span className="generalization-callout__mark">Same engine, different diagnosis</span>
        {flipped.map((c) => (
          <span key={c.axis}>
            {" "}
            <strong>{AXIS_LABEL[c.axis]}</strong> shifted from{" "}
            {prevStates[c.axis].replace("_", " ").toLowerCase()} to{" "}
            {c.state.replace("_", " ").toLowerCase()} versus {prev.title}.
          </span>
        ))}{" "}
        The diagnostic is computed from the evidence, not pre-written.
      </motion.p>
    </AnimatePresence>
  );
}
