<div align="center">

# OFFSIDE

### The Football Disagreement Engine

**VAR gives officials seven camera angles. Fans get a tweet.**

OFFSIDE doesn't tell you whether the referee was right — it shows you, with the
receipts, exactly *why* a billion people will never agree.

</div>

---

## The problem

Billions watch the same match and experience it completely differently. The same
four seconds — Maradona's hand, 1986 — is *"the greatest goal in history"* in Buenos
Aires and *"he cheated"* in London. Both certain. Both internally consistent.

Today's football AI tells you **what happened** and adjudicates **whether a call was
correct**. OFFSIDE answers the question nobody else does:

> **Why do informed, intelligent people look at the same incident and refuse to
> agree — and why does that disagreement persist?**

## THE SPLIT

OFFSIDE reconstructs a contested moment through four evidence-grounded lenses and
decomposes the disagreement into a single artifact — **THE SPLIT** — that attributes
*why it stays contested* across four fixed, mutually exclusive dimensions:

| Dimension | The question it answers |
|-----------|-------------------------|
| **Rule ambiguity** | Are the Laws themselves unclear or in conflict? |
| **Indeterminacy** | Does a fact stay contested even with all current technology? |
| **Decision-time deficit** | Knowable now, but not available at the moment of the call? |
| **Cultural prior bias** | Agreement on facts and rules, divergence on the acceptable outcome? |

For the Hand of God, THE SPLIT resolves to a precise diagnosis: it stays debated
**not** because the Law is unclear (rule ambiguity — *ruled out*) and **not** because
the act is unknowable (indeterminacy — *ruled out*; Maradona admitted it), but because
of **what the referee could see in the moment** (decision-time deficit) and **which
nation is watching** (cultural prior bias).

Each cell click-traces to a specific, page-numbered passage of the actual source — the
**IFAB Laws of the Game**, StatsBomb event data, curated historical record, or a named
quote. Where there is no evidence, OFFSIDE says so explicitly, in its own cell state.

## The moat: a model that cannot fabricate a number

The reasoning model is **structurally forbidden from emitting a number**. The schemas it
is constrained to — THE SPLIT, the lens readings — contain no numeric field anywhere in
their transitive shape. There is no `73%` to invent because there is no number-shaped
hole to fill. THE SPLIT communicates with *states* (present / weak / ruled out / not
documented), never with a bar that could be misread as a confidence. This invariant is
enforced by a test that walks the full JSON Schema and fails the build on any numeric
type — the guarantee is checked by CI, not by good intentions.

## How it works

OFFSIDE is a **factory**, not a live service. Everything expensive happens once, at build
time; the web app is a pure reader of the frozen result.

```text
  engine/ (Python, build-time)                         web/ (Next.js, Vercel)
  ─────────────────────────────                        ──────────────────────
  IFAB PDF ─Docling─▶ page-cited evidence ┐
  StatsBomb ─────────▶ license-safe aggregate ├─▶ per-lens index (LanceDB)
  curated YAML ──────▶ historical + framing ┘            │
                                                          ▼
                      ┌──────────── per lens ────────────┐
                      │  retrieve → Granite (cite-or-die) │
                      │  → Granite Guardian groundedness  │
                      └───────────────┬──────────────────┘
                                      ▼
                      Granite synthesis → THE SPLIT
                      → Guardian audits every cell
                      → assert documented thesis shape
                      → freeze byte-identical fixture ──────▶ fixtures/*.json ──▶ reads
```

No model and no Python run at web runtime. The fixture is deterministic: re-running the
bake on the same corpus produces a byte-identical file, and every fixture carries its own
provenance (the models used and the corpus git SHA) so any result can be reproduced.

## Built with IBM

Four IBM tools, each load-bearing — not decoration:

| Tool | Role |
|------|------|
| **IBM Granite** (`granite3.3:8b`) | Grounded synthesis of *why* disagreement persists — never a verdict, never a number |
| **Granite Embedding** (`granite-embedding:30m`) | Embeds the evidence so each lens retrieves only its own |
| **IBM Docling** | Extracts the IFAB Laws into structured, page-cited evidence — the click-to-source spine |
| **Granite Guardian** (`granite-guardian3:2b`) | A **second IBM model audits the first**: it checks every reading's groundedness against its cited page and demotes anything it cannot confirm |

The Granite Guardian gate is the move a single-model entry cannot make: a claim reaches a
fixture only if the first model asserted it **and** the second model could not refute it
against the source. The audit is recorded as a trust seal, frozen at temperature 0.

## Repository

```text
engine/     Python build-time factory (the bake). Run on Colab; 113 tests.
  bake.ipynb  the factory runner — pulls the Granite models and bakes a fixture
web/        Next.js 16 + IBM Carbon app. Reads the frozen fixtures; deploys to Vercel.
corpus/     curated evidence (framing quotes, historical record) as YAML
fixtures/   pointer to the baked bundles, which live in web/fixtures/
```

## Running it

**The bake** (produces a fixture) runs on Google Colab with a T4 GPU — see
[`engine/bake.ipynb`](engine/bake.ipynb). It installs Ollama, pulls the three Granite
models, and writes an audited bundle into `web/fixtures/`.

**The web app:**

```bash
cd web
npm install
npm run dev      # http://localhost:3000
```

Until the bake runs, the app serves a schema-valid sample fixture (flagged in the UI).
Deployment to Vercel is documented in [`web/DEPLOY.md`](web/DEPLOY.md).

## License

Source code: [MIT](LICENSE). Data sources (StatsBomb Open Data, the IFAB Laws of the
Game, IBM Granite) are governed by their own separate terms — see
[LICENSES.md](LICENSES.md).
