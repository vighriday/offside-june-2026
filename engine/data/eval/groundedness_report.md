# OFFSIDE — lens groundedness report

Build-time audit metric (backend: **deterministic**). These scores measure how well each
lens reading is grounded in its cited evidence. They are an external audit of the
pipeline — they never enter THE SPLIT, the lens schema, or the UI, so the no-numbers
contract on the model output is untouched.

| Incident | Lens | Stance | Guardian | Citations | Groundedness |
|----------|------|--------|----------|:---------:|:------------:|
| hand-of-god-1986 | REFEREE | SUPPORTS | GROUNDED | 1 | 1.00 |
| hand-of-god-1986 | TACTICAL | SUPPORTS | GROUNDED | 1 | 1.00 |
| hand-of-god-1986 | HISTORICAL | SUPPORTS | GROUNDED | 2 | 1.00 |
| hand-of-god-1986 | FRAMING | MIXED | GROUNDED | 2 | 1.00 |
| handball-rewrite | REFEREE | DISPUTES | GROUNDED | 2 | 1.00 |
| handball-rewrite | TACTICAL | INSUFFICIENT_EVIDENCE | GROUNDED | 0 | 0.00 |
| handball-rewrite | HISTORICAL | DISPUTES | GROUNDED | 2 | 1.00 |
| handball-rewrite | FRAMING | DISPUTES | GROUNDED | 2 | 1.00 |
| lampard-ghost-goal-2010 | REFEREE | SUPPORTS | GROUNDED | 1 | 1.00 |
| lampard-ghost-goal-2010 | TACTICAL | INSUFFICIENT_EVIDENCE | GROUNDED | 0 | 0.00 |
| lampard-ghost-goal-2010 | HISTORICAL | SUPPORTS | GROUNDED | 2 | 1.00 |
| lampard-ghost-goal-2010 | FRAMING | SUPPORTS | GROUNDED | 2 | 1.00 |
| offside-margin | REFEREE | SUPPORTS | GROUNDED | 1 | 1.00 |
| offside-margin | TACTICAL | INSUFFICIENT_EVIDENCE | GROUNDED | 0 | 0.00 |
| offside-margin | HISTORICAL | DISPUTES | GROUNDED | 2 | 1.00 |
| offside-margin | FRAMING | DISPUTES | GROUNDED | 2 | 1.00 |
| pgmol-subjective | REFEREE | DISPUTES | GROUNDED | 2 | 1.00 |
| pgmol-subjective | TACTICAL | INSUFFICIENT_EVIDENCE | GROUNDED | 0 | 0.00 |
| pgmol-subjective | HISTORICAL | DISPUTES | GROUNDED | 1 | 1.00 |
| pgmol-subjective | FRAMING | MIXED | GROUNDED | 2 | 1.00 |
| suarez-handball-2010 | REFEREE | SUPPORTS | GROUNDED | 1 | 1.00 |
| suarez-handball-2010 | HISTORICAL | DISPUTES | GROUNDED | 1 | 1.00 |
| suarez-handball-2010 | TACTICAL | INSUFFICIENT_EVIDENCE | GROUNDED | 0 | 0.00 |
| suarez-handball-2010 | FRAMING | MIXED | GROUNDED | 2 | 1.00 |

**19 / 24** lens readings fully grounded (79%).
