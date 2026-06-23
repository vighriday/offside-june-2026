"use client";

import Image from "next/image";
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
        <h1 className="hero__wordmark-wrap" aria-label="OFFSIDE">
          <Image
            className="hero__logo"
            src="/offside-logo.png"
            alt="OFFSIDE"
            width={560}
            height={373}
            priority
          />
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
        It breaks a contested call into the <strong>four reasons an argument lasts</strong>,
        and shows which ones apply:
      </p>

      <ol className="hero__reasons">
        <li><span>1</span> Is the rule unclear?</li>
        <li><span>2</span> Is the truth unknowable?</li>
        <li><span>3</span> Could the ref see it in time?</li>
        <li><span>4</span> Do the sides just want their own way?</li>
      </ol>

      <p className="hero__sub hero__sub--tight">
        Same engine on the 1986 Hand of God <em>and</em>{" "}
        <strong>this season&rsquo;s VAR disputes</strong>. Every answer is proved against a
        real page of the Laws of the Game — and a <strong>second IBM model checks the
        first</strong>. It never invents a number.
      </p>

      <p className="hero__for">
        A tool for the people who <em>defend</em> these calls — referees&rsquo; bodies,
        rule-makers, broadcasters — not to re-argue a goal, but to show which gap each one exposes.
      </p>
    </header>
  );
}
