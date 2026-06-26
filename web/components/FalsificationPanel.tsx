"use client";

import { motion } from "motion/react";
import type { Probe, CellState } from "@/types/contract";

// THE FALSIFICATION PANEL — the centerpiece. A frozen answer could be a lookup table; the
// only way to disprove that is to ATTACK the engine and watch what it does. Each probe was
// run through the SAME real Granite + Granite Guardian pipeline that produced the fixture,
// and the outcome here — the before/after state and the Guardian verdict — is a real
// captured result, locked by a CI integrity gate so it can never be hand-authored.

const STATE_WORD: Record<CellState, string> = {
  PRESENT: "unknowable",
  WEAK: "faintly unknowable",
  ABSENT: "ruled out",
  NOT_DOCUMENTED: "no evidence",
};

const KIND_COPY: Record<
  Probe["kind"],
  { badge: string; tone: "flip" | "noise" | "overrule" }
> = {
  FLIP: { badge: "Push it the right way", tone: "flip" },
  NOISE: { badge: "Push it with junk", tone: "noise" },
  OVERREACH: { badge: "Lie to it", tone: "overrule" },
};

interface FalsificationPanelProps {
  probes: Probe[];
}

export function FalsificationPanel({ probes }: FalsificationPanelProps) {
  if (!probes.length) return null;

  return (
    <section className="falsify" aria-label="Falsification probes">
      <header className="falsify__head">
        <h3 className="falsify__title">We tried to break our own answer</h3>
        <p className="falsify__lede">
          A frozen result could just be a stored answer. So we <strong>attacked</strong> it —
          feeding new evidence straight back through the same two IBM models, live, and watching
          what they did. Nothing below is written by hand; every verdict is a real Granite
          Guardian token, locked so it cannot be faked.
        </p>
      </header>

      <div className="falsify__grid">
        {probes.map((p, i) => {
          const moved = p.state_before !== p.state_after;
          const { badge, tone } = KIND_COPY[p.kind];
          return (
            <motion.article
              key={p.kind}
              className="falsify__card"
              data-tone={tone}
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{ duration: 0.4, delay: 0.08 * i }}
            >
              <span className="falsify__badge">{badge}</span>
              <p className="falsify__question">{p.plain_question}</p>

              <div className="falsify__what" aria-hidden>
                <span className="falsify__what-label">
                  {p.kind === "OVERREACH" ? "The over-claim" : "We fed it"}
                </span>
                <p className="falsify__injected">&ldquo;{p.injected_text}&rdquo;</p>
              </div>

              {/* FLIP/NOISE are about whether the engine's answer MOVES; OVERREACH is about
                  whether the auditor catches a claim, so it leads with the verdict instead. */}
              {p.kind !== "OVERREACH" && (
                <div className="falsify__move" data-moved={moved}>
                  <span className="falsify__state">{STATE_WORD[p.state_before]}</span>
                  <span className="falsify__arrow">{moved ? "→" : "="}</span>
                  <span className="falsify__state">{STATE_WORD[p.state_after]}</span>
                </div>
              )}

              <div
                className="falsify__verdict"
                data-verdict={p.guardian_verdict}
              >
                <span className="falsify__verdict-tag">
                  Granite Guardian: {p.guardian_verdict}
                </span>
                <span className="falsify__verdict-model">{p.guardian_model}</span>
              </div>

              <p className="falsify__outcome">{p.outcome}</p>
            </motion.article>
          );
        })}
      </div>

      <p className="falsify__foot">
        This is the part a copy can&rsquo;t fake: hand someone the attack and the engine still
        holds. The second IBM model is not decoration — you just watched it overrule the first.
      </p>
    </section>
  );
}
