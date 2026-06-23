"use client";

// A hand-authored inline SVG schematic per incident — the spatial truth a football judge
// came to see, rendered as restrained IBM-Carbon line art (no photo, no video, no license,
// no model). It turns each incident from a paragraph into a thing you can point at, and it
// stays fully inside the static-reader architecture. Each diagram is verdict-free: it shows
// what is geometrically agreed, never who was "right".
//
// Visual language, shared across all six: thin strokes on the dark g100 surface, the
// split-present blue as the one accent, a dashed "pitch line" motif, and a single labelled
// focus point. Nothing decorative competes with THE SPLIT below it.

import type { JSX } from "react";

const STROKE = "var(--cds-border-strong-01, #8d8d8d)";
const FAINT = "var(--cds-border-subtle-01, #525252)";
const ACCENT = "var(--split-present, #4589ff)";
const WARN = "var(--split-weak, #f1c21b)";
const TEXT = "var(--cds-text-secondary, #c6c6c6)";

function Frame({ children, caption }: { children: React.ReactNode; caption: string }) {
  return (
    <figure className="incident-diagram">
      <svg
        viewBox="0 0 320 150"
        role="img"
        aria-label={caption}
        className="incident-diagram__svg"
      >
        {children}
      </svg>
      <figcaption className="incident-diagram__caption">{caption}</figcaption>
    </figure>
  );
}

const label = (
  x: number,
  y: number,
  t: string,
  fill: string = TEXT,
  anchor: "middle" | "start" | "end" = "middle",
) => (
  <text x={x} y={y} fontSize="8" fill={fill} textAnchor={anchor} fontFamily="inherit">
    {t}
  </text>
);

// ── Hand of God: the ball met a hand above the head, the goal frame behind ──
function HandOfGod() {
  return (
    <Frame caption="The contact was above the head — a hand, not a header. Seen now; unseen in 1986.">
      {/* goal frame */}
      <path d="M30 120 V40 H120 V120" fill="none" stroke={FAINT} strokeWidth="1.5" />
      <path d="M30 40 L24 34 M120 40 L126 34" stroke={FAINT} strokeWidth="1" />
      {/* net hint */}
      <path d="M40 50 V112 M55 50 V112 M70 50 V112 M85 50 V112 M100 50 V112 M30 60 H120 M30 75 H120 M30 90 H120 M30 105 H120"
        stroke={FAINT} strokeWidth="0.4" opacity="0.5" />
      {/* head + raised arm reaching to the ball */}
      <circle cx="180" cy="92" r="9" fill="none" stroke={STROKE} strokeWidth="1.5" />
      <path d="M183 84 Q196 64 206 56" fill="none" stroke={STROKE} strokeWidth="1.5" />
      {/* the ball, at the hand, above head height */}
      <circle cx="210" cy="52" r="7" fill="none" stroke={ACCENT} strokeWidth="2" />
      <circle cx="206" cy="56" r="2" fill={ACCENT} />
      {label(255, 50, "hand contact", ACCENT, "start")}
      <path d="M214 53 H250" stroke={ACCENT} strokeWidth="0.8" strokeDasharray="2 2" />
      {/* head-height reference line */}
      <path d="M150 83 H300" stroke={WARN} strokeWidth="0.8" strokeDasharray="3 3" opacity="0.7" />
      {label(296, 80, "head height", WARN, "end")}
    </Frame>
  );
}

// ── Lampard: the whole ball clearly behind the line; goal not given ──
function Lampard() {
  return (
    <Frame caption="The whole ball crossed the line. The Law's test was met; the officials could not see it in 2010.">
      <path d="M40 120 V35 H150 V120" fill="none" stroke={FAINT} strokeWidth="1.5" />
      <path d="M40 35 H150" stroke={STROKE} strokeWidth="2" />
      {/* the goal line, on the ground */}
      <path d="M70 120 V40" stroke={STROKE} strokeWidth="2.5" />
      {label(70, 134, "goal line")}
      {/* ball clearly behind the line (inside the goal) */}
      <circle cx="100" cy="100" r="8" fill="none" stroke={ACCENT} strokeWidth="2" />
      <path d="M100 92 V108 M92 100 H108" stroke={ACCENT} strokeWidth="0.6" />
      {/* gap arrow showing the ball is fully over */}
      <path d="M70 100 H92" stroke={ACCENT} strokeWidth="0.8" strokeDasharray="2 2" />
      {label(108, 102, "whole ball over", ACCENT, "start")}
      {/* bounce arc from crossbar */}
      <path d="M150 38 Q130 70 100 92" fill="none" stroke={FAINT} strokeWidth="1" strokeDasharray="3 2" />
      {label(186, 60, "down off the bar", TEXT, "start")}
    </Frame>
  );
}

// ── Offside margin: the precise line, and the thick tolerance band over it ──
function OffsideMargin() {
  return (
    <Frame caption="The Law fixes the line exactly; at the margin it can't be measured that finely, so a deliberately thick band is used.">
      <path d="M20 120 H300" stroke={FAINT} strokeWidth="1" />
      {/* the precise offside line the Law implies */}
      <path d="M160 26 V120" stroke={ACCENT} strokeWidth="2" />
      {label(160, 18, "the line the Law draws", ACCENT)}
      {/* the tolerance band actually applied */}
      <rect x="150" y="30" width="20" height="86" fill={WARN} opacity="0.16" />
      <path d="M150 30 V116 M170 30 V116" stroke={WARN} strokeWidth="1" strokeDasharray="3 2" opacity="0.8" />
      {label(196, 110, "the thick band used", WARN, "start")}
      <path d="M188 108 H172" stroke={WARN} strokeWidth="0.7" />
      {/* attacker foot point inside the band — undecidable */}
      <circle cx="166" cy="78" r="3.5" fill={STROKE} />
      {label(166, 60, "attacker", TEXT)}
      {/* defender */}
      <circle cx="158" cy="95" r="3.5" fill="none" stroke={STROKE} strokeWidth="1.3" />
    </Frame>
  );
}

// ── Handball rewrite: one contact, three competing tests the Law offers ──
function HandballRewrite() {
  return (
    <Frame caption="One contact, three tests the Law asks the official to choose between — which is why the call is disputed.">
      {/* arm + ball contact, centre */}
      <path d="M150 120 Q150 80 176 66" fill="none" stroke={STROKE} strokeWidth="1.5" />
      <circle cx="186" cy="62" r="7" fill="none" stroke={ACCENT} strokeWidth="2" />
      <circle cx="182" cy="66" r="2" fill={ACCENT} />
      {/* three branching tests */}
      <path d="M190 60 L250 30" stroke={FAINT} strokeWidth="0.8" />
      <path d="M192 64 L250 64" stroke={FAINT} strokeWidth="0.8" />
      <path d="M190 68 L250 98" stroke={FAINT} strokeWidth="0.8" />
      {label(254, 32, "deliberate?", TEXT, "start")}
      {label(254, 67, "unnaturally bigger?", TEXT, "start")}
      {label(254, 100, "accidental → goal?", TEXT, "start")}
      {label(120, 70, "one contact", ACCENT, "end")}
      <path d="M122 67 H178" stroke={ACCENT} strokeWidth="0.7" strokeDasharray="2 2" />
    </Frame>
  );
}

// ── Suárez: ball on the line, hand blocking — seen and correctly punished ──
function Suarez() {
  return (
    <Frame caption="A deliberate hand on the goal line — seen in real time and correctly punished. Only the framing stays split.">
      <path d="M40 120 V35 H150 V120" fill="none" stroke={FAINT} strokeWidth="1.5" />
      <path d="M40 35 H150" stroke={STROKE} strokeWidth="2" />
      <path d="M95 120 V40" stroke={STROKE} strokeWidth="2.5" />
      {label(95, 134, "goal line")}
      {/* ball on the line */}
      <circle cx="95" cy="70" r="8" fill="none" stroke={ACCENT} strokeWidth="2" />
      {/* a hand blocking it */}
      <path d="M95 55 Q108 50 116 56" fill="none" stroke={STROKE} strokeWidth="1.6" />
      <path d="M95 55 L95 48 M101 53 L102 46 M108 52 L110 46" stroke={STROKE} strokeWidth="1.2" />
      {label(150, 60, "deliberate handball", ACCENT, "start")}
      <path d="M148 58 H104" stroke={ACCENT} strokeWidth="0.7" strokeDasharray="2 2" />
      {/* red card mark */}
      <rect x="44" y="44" width="9" height="13" rx="1" fill={WARN} opacity="0.85" />
      {label(70, 54, "red + penalty", TEXT, "start")}
    </Frame>
  );
}

// ── PGMOL subjective: same contact, opposite verdicts across matches ──
function PgmolSubjective() {
  return (
    <Frame caption="The same contact, two matches, opposite calls — the threshold is a matter of degree, not a bright line.">
      {/* match A */}
      <circle cx="70" cy="62" r="7" fill="none" stroke={STROKE} strokeWidth="1.5" />
      <path d="M70 69 Q70 86 60 96" fill="none" stroke={STROKE} strokeWidth="1.3" />
      <path d="M78 58 Q88 54 95 60" fill="none" stroke={FAINT} strokeWidth="1.3" />
      {label(70, 38, "Match A")}
      {/* verdict A: penalty given */}
      <path d="M58 110 l6 6 l12 -14" fill="none" stroke={ACCENT} strokeWidth="2.2" />
      {label(67, 130, "penalty", ACCENT)}
      {/* divider */}
      <path d="M160 30 V124" stroke={FAINT} strokeWidth="0.6" strokeDasharray="3 3" />
      {/* match B — identical */}
      <circle cx="250" cy="62" r="7" fill="none" stroke={STROKE} strokeWidth="1.5" />
      <path d="M250 69 Q250 86 240 96" fill="none" stroke={STROKE} strokeWidth="1.3" />
      <path d="M258 58 Q268 54 275 60" fill="none" stroke={FAINT} strokeWidth="1.3" />
      {label(250, 38, "Match B (same contact)")}
      {/* verdict B: waved away */}
      <path d="M242 104 l14 14 M256 104 l-14 14" stroke={WARN} strokeWidth="2.2" />
      {label(249, 130, "play on", WARN)}
    </Frame>
  );
}

const DIAGRAMS: Record<string, () => JSX.Element> = {
  "hand-of-god-1986": HandOfGod,
  "lampard-ghost-goal-2010": Lampard,
  "offside-margin": OffsideMargin,
  "handball-rewrite": HandballRewrite,
  "suarez-handball-2010": Suarez,
  "pgmol-subjective": PgmolSubjective,
};

export function IncidentDiagram({ incidentId }: { incidentId: string }) {
  const D = DIAGRAMS[incidentId];
  if (!D) return null;
  return <D />;
}
