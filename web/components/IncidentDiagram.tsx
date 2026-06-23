"use client";

import Image from "next/image";

// A per-incident schematic — the spatial truth a football judge came to see, as restrained
// IBM-Carbon line art (dark, one blue accent, an amber contested element). These are the
// generated diagrams under web/public/incidents/. Each is verdict-free: it shows what is
// geometrically agreed, never who was "right", with one plain caption naming the point.

interface Diagram {
  src: string;
  caption: string;
}

const DIAGRAMS: Record<string, Diagram> = {
  "hand-of-god-1986": {
    src: "/incidents/hand-of-god.png",
    caption:
      "The ball met a hand above the head — not a header. Obvious now; invisible to the ref in 1986.",
  },
  "handball-rewrite": {
    src: "/incidents/handball-rewrite.png",
    caption:
      "One contact, three tests the Law makes the official choose between: was it deliberate, did the arm make the body unnaturally bigger, or did it go straight in off the hand? Different tests, different outcomes — which is why the call splits.",
  },
  "offside-margin": {
    src: "/incidents/offside-margin.png",
    caption:
      "The Law fixes the line exactly; at the margin it can't be measured that finely, so a deliberately thick band is used.",
  },
  "pgmol-subjective": {
    src: "/incidents/pgmol-subjective.png",
    caption:
      "The same contact in two matches, opposite calls — the threshold is a matter of degree, not a bright line.",
  },
  "suarez-handball-2010": {
    src: "/incidents/suarez.png",
    caption:
      "A deliberate hand on the goal line — seen in real time and correctly punished. Only the framing stays split.",
  },
  "lampard-ghost-goal-2010": {
    src: "/incidents/lampard.png",
    caption:
      "The whole ball crossed the line. The Law's test was met; the officials simply could not see it in 2010.",
  },
};

export function IncidentDiagram({ incidentId }: { incidentId: string }) {
  const d = DIAGRAMS[incidentId];
  if (!d) return null;
  return (
    <figure className="incident-diagram">
      <Image
        className="incident-diagram__img"
        src={d.src}
        alt={d.caption}
        width={384}
        height={216}
        sizes="(max-width: 48rem) 100vw, 48rem"
      />
      <figcaption className="incident-diagram__caption">{d.caption}</figcaption>
    </figure>
  );
}
