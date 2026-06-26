"use client";

import { motion } from "motion/react";

// A one-screen, jargon-free explainer for a judge who has 30 seconds. It states plainly:
// what OFFSIDE is, the four IBM models and what each does, and — the honest part — what is
// real versus frozen. It sits right after the masthead so the rest of the page makes sense.
export function HowItWorks() {
  return (
    <section className="how" aria-label="How OFFSIDE works">
      <h2 className="how__title">In one screen</h2>

      <div className="how__steps">
        {STEPS.map((s, i) => (
          <motion.div
            key={s.k}
            className="how__step"
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-40px" }}
            transition={{ duration: 0.35, delay: 0.06 * i }}
          >
            <span className="how__num">{i + 1}</span>
            <div>
              <p className="how__step-title">{s.title}</p>
              <p className="how__step-body">{s.body}</p>
            </div>
          </motion.div>
        ))}
      </div>

      <div className="how__models">
        <p className="how__models-label">Three Granite models, plus Docling</p>
        <ul className="how__model-list">
          <li>
            <strong>Granite</strong> reads each piece of evidence and says what it means.
          </li>
          <li>
            <strong>Granite Guardian</strong> is a <em>second</em>{" "}model that checks the first —
            it throws out any reading the source page doesn&rsquo;t actually support.
          </li>
          <li>
            <strong>Granite Embedding</strong> finds the right page of the rulebook for each
            question.
          </li>
          <li>
            <strong>Docling</strong>, IBM&rsquo;s open-source document parser, reads the official
            Laws PDF so every answer can point at a real page and the exact spot on it.
          </li>
        </ul>
      </div>

      <p className="how__honest">
        <span className="how__honest-tag">Straight answer</span>
        The page you see is a frozen result, so it loads instantly with no model running.
        We built it that way on purpose — and to prove it&rsquo;s not a stored trick, open the
        <strong>millimetre offside</strong> case below: it <strong>attacks its own answer
        live</strong> with the real models and lets the second one overrule the first. The
        schema makes it structurally unable to invent a number.
      </p>
    </section>
  );
}

const STEPS = [
  {
    k: "pick",
    title: "Pick a disputed moment",
    body: "A famous one like the Hand of God, or a live VAR row from this season.",
  },
  {
    k: "split",
    title: "It splits the argument into four questions",
    body: "Is the rule unclear? Is the truth unknowable? Could the ref see it in time? Do the sides just want their own way?",
  },
  {
    k: "answer",
    title: "It answers each from the real Laws",
    body: "Where the Laws speak, the answer points at the exact page of the Laws of the Game — click it and you land on the spot.",
  },
  {
    k: "why",
    title: "You see WHY it never ends",
    body: "Not who was right — which of the four gaps each moment exposes. That is the whole product.",
  },
];
