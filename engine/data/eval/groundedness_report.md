# OFFSIDE — lens groundedness report

Build-time audit metric (backend: **deterministic**). These scores measure how well each
lens reading is grounded in its cited evidence. They are an external audit of the
pipeline — they never enter THE SPLIT, the lens schema, or the UI, so the no-numbers
contract on the model output is untouched.

| Incident | Lens | Stance | Guardian | Citations | Groundedness |
|----------|------|--------|----------|:---------:|:------------:|
| offside-margin | REFEREE | SUPPORTS | GROUNDED | 2 | 1.00 |
| offside-margin | TACTICAL | INSUFFICIENT_EVIDENCE | UNGROUNDED | 0 | 0.00 |
| offside-margin | HISTORICAL | DISPUTES | GROUNDED | 3 | 1.00 |
| offside-margin | FRAMING | MIXED | GROUNDED | 2 | 1.00 |

**3 / 4** lens readings fully grounded (75%).
