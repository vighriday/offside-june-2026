"use client";

import { motion } from "motion/react";

// The front door. A judge (or anyone) must understand WHAT this is and WHY it matters
// before they ever see the diagnostic grid. This opens on the gut-punch — same moment,
// opposite truths — then states the product in one plain line, then teaches how to read
// THE SPLIT. Everything below it now makes sense.
export function Hero() {
  return (
    <header className="hero">
      {/* The masthead — a proper wordmark with the offside-line motif slicing through it,
          so the front door reads as a product, not a label. */}
      <motion.div
        className="hero__masthead"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.4, 0.14, 0.3, 1] }}
      >
        <h1 className="hero__wordmark" aria-label="OFFSIDE">
          <span className="hero__wordmark-line" aria-hidden />
          OFFSIDE
        </h1>
        <span className="hero__tagline">The Football Disagreement Engine</span>
        <span className="hero__ibm">Built on IBM Granite · Docling · Guardian</span>
      </motion.div>

      <motion.div
        className="hero__clash"
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.15, ease: [0.4, 0.14, 0.3, 1] }}
      >
        <div className="hero__side hero__side--a">
          <span className="hero__side-tag">Buenos Aires</span>
          <span className="hero__side-quote">“The greatest goal in history.”</span>
        </div>
        <div className="hero__vs">
          <span className="hero__vs-frame">the same 4 seconds</span>
        </div>
        <div className="hero__side hero__side--b">
          <span className="hero__side-tag">London</span>
          <span className="hero__side-quote">“He cheated.”</span>
        </div>
      </motion.div>

      <p className="hero__line">
        Every football AI tells you <em>whether a call was right.</em>
        <br />
        OFFSIDE tells you <strong>why the argument never ends</strong> — and proves every
        reason against the actual Laws of the Game.
      </p>

      <p className="hero__sub">
        It decomposes a contested decision into the four structural reasons disagreement
        persists — is the <em>rule</em> unclear, is the <em>truth</em> unknowable, could the
        official <em>see</em> it, or do both sides just <em>want</em> their own outcome — and
        marks which are in play. The same engine reads the Hand of God and{" "}
        <strong>this season&rsquo;s VAR disputes</strong>: the rewritten handball Law, the
        millimetre offside line, the &ldquo;subjective&rdquo; calls that flip week to week. It
        cannot output a number, and a second IBM model audits the first.
      </p>

      <p className="hero__for">
        Built for the people who have to defend these decisions — referees&rsquo; bodies,
        rule-makers, and the broadcasters who explain them — not to re-litigate a goal, but to
        show <em>which structural gap</em> each controversy exposes.
      </p>
    </header>
  );
}
