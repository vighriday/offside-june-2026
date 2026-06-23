"use client";

import { motion } from "motion/react";

// The front door. A judge (or anyone) must understand WHAT this is and WHY it matters
// before they ever see the diagnostic grid. This opens on the gut-punch — same moment,
// opposite truths — then states the product in one plain line, then teaches how to read
// THE SPLIT. Everything below it now makes sense.
export function Hero() {
  return (
    <header className="hero">
      <p className="hero__brand">OFFSIDE — The Football Disagreement Engine</p>

      <motion.div
        className="hero__clash"
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.4, 0.14, 0.3, 1] }}
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

      <h1 className="hero__line">
        Every football AI tells you <em>whether a call was right.</em>
        <br />
        OFFSIDE tells you <strong>why a billion people will never agree</strong> —
        and backs every reason with the actual Laws of the Game.
      </h1>

      <p className="hero__sub">
        It doesn&rsquo;t officiate and it doesn&rsquo;t predict. It decomposes a contested
        moment into the four reasons disagreement persists — and proves each one against a
        real source page. It cannot output a number, and a second IBM model audits the first.
      </p>
    </header>
  );
}
