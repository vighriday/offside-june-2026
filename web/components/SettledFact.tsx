"use client";

import { motion } from "motion/react";
import type { ResolutionStatus, SettledFact as SettledFactData } from "@/types/contract";
import { IncidentDiagram } from "./IncidentDiagram";

// The settled fact is stated FIRST, before any decomposition. OFFSIDE never opens with
// refusal — it names what is agreed, then explains why the residual stays contested.

const STATUS_LABEL: Record<ResolutionStatus, string> = {
  SETTLED_FACT: "Settled",
  ADJUDICATED_CONTESTED: "Adjudicated, still contested",
  UNRESOLVABLE: "Unresolvable",
};

interface SettledFactProps {
  fact: SettledFactData;
  title: string;
  incidentId: string;
}

export function SettledFact({ fact, title, incidentId }: SettledFactProps) {
  return (
    <motion.header
      className="settled-fact"
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.4, 0.14, 0.3, 1] }}
    >
      <h2 className="settled-fact__title">{title}</h2>

      <div className="settled-fact__status">
        <span className="settled-fact__status-dot" data-status={fact.status} />
        <span className="settled-fact__status-label">
          {STATUS_LABEL[fact.status]}
        </span>
      </div>

      <p className="settled-fact__statement">{fact.statement}</p>

      <IncidentDiagram incidentId={incidentId} />
    </motion.header>
  );
}
