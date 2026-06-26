# OFFSIDE Live Studio — Design

**Date:** 2026-06-26
**Status:** Approved (design); pending spec review
**Author:** Hriday Vig

## Problem

Two real problems, one feature solves both.

1. **The product is hard to understand.** Everything stacks on one long scroll — pitch,
   explainer, the IBM models, the incident picker, THE SPLIT, the four lenses, the footer.
   A judge (and even the author) drowns. There is no single surface per idea.
2. **There is no way to prove the engine actually *computes*.** The deployed page is a
   frozen, pre-baked result (by design: `$0`, instant, reproducible). A skeptic could mistake
   it for a lookup table. The only live proof today is the falsification panel on one incident.

The user also asked: *how does a real **user** actually use this — a tool people return to?*
The answer fixes both problems: let a professional **supply the human evidence** for a
controversy and watch the engine **decompose it live, step by step**. Watching the four boxes
fill in one at a time both proves it computes *and* teaches THE SPLIT.

## Goal & non-goals

**Goal:** A new **Studio** surface where a user supplies the human evidence for a contested
decision, the engine retrieves the matching IFAB Law itself, runs the real Granite pipeline
(Granite reads each lens → Granite Guardian audits each → deterministic SPLIT routing), and
streams the result so the four SPLIT boxes fill in live. Plus a **tabs revamp** so the site
reads as three clear surfaces. The live pipeline runs on the author's machine for the demo and
is **self-hostable** by anyone with one command.

**Non-goals:**
- No free-text "type any incident, get magic" box. The engine grounds only against supplied +
  retrieved evidence; thin input honestly yields a thin SPLIT (`Not documented`), never fabrication.
- No always-on hosted GPU backend. The public Vercel site stays `$0` static. Live runs only on
  a machine that opts in (author's, or a judge's self-host).
- No user accounts, no saved private libraries, no cross-incident analytics (that is a later,
  larger product — explicitly out of scope here).
- No change to the no-numbers moat or cite-or-die guarantees. They apply unchanged to user
  incidents.

## Target user

A **professional who supplies evidence** — a broadcaster/analyst/referee-body user who has the
facts and the named quotes for a controversy and wants the structural decomposition (to put on
air, in a report, or to compare disputes). They bring the messy human evidence; the engine
brings the rulebook and the reasoning.

## Architecture overview

Two runtime modes, one codebase. The web app auto-detects which by polling backend health.

```
                         ┌───────────────────────────── Public Vercel (static, $0) ─────────┐
                         │  Explore tab   — frozen 6 incidents (unchanged)                    │
  Masthead + hook  ──►   │  Studio tab    — full form + "Load example" (pre-baked fixture)    │
  (always visible)       │                  submit DISABLED w/ self-host how-to banner        │
                         │  How-it-works  — the explainer, pulled out of Explore              │
                         └──────────────────────────────────────────────────────────────────┘
                                                  │  (health poll: backend reachable?)
                                                  ▼  yes →
                         ┌───────────── Local / self-hosted (author or judge) ───────────────┐
  Studio form  ─submit→  │  FastAPI  POST /decompose (SSE)   GET /health                      │
                         │     │ build incident from form (incident_from_form.py)             │
                         │     │ retrieve Law (existing IFAB index) + Granite reads 4 lenses  │
                         │     │ Granite Guardian audits each → deterministic SPLIT route     │
                         │     ▼ stream step events ───────────────────────────────────────► │
                         │  Ollama: granite3.3:8b · granite-embedding:30m · granite3-guardian │
                         └──────────────────────────────────────────────────────────────────┘
```

The engine logic is **unchanged**. The only new idea: the evidence source becomes the **user's
form** instead of a curated corpus folder. Same `lens_runner`, `lens_retrieve`,
`synthesize.derive_split`, `guardian`, `integrity`.

## UI: the tabs revamp

The masthead and the Buenos Aires/London hook stay pinned above the tabs (the identity).
Below them, three tabs:

| Tab | Purpose | Source |
|---|---|---|
| **Explore** | The current page: 6 curated incidents, Divergence Lineage, THE SPLIT, four lenses, falsification panel. The polished frozen showcase. | exists, lightly reorganized |
| **Studio** *(new)* | "Decompose your own controversy." Guided form → live streamed SPLIT. | new |
| **How it works** | The explainer (hero "in one screen", the IBM models, the honesty paragraph) pulled into its own tab so Explore is cleaner. | reorganized from existing copy |

Tabs give one idea per surface: **see it work · do it yourself · understand it.**

## The Studio form

A guided form, four blocks mapped to the four lenses, so filling it in teaches THE SPLIT.

| Block | User enters | Maps to lens → axis | Required |
|---|---|---|---|
| **The moment** | Title + 1–2 lines of settled facts ("what everyone agrees happened") | Settled-Fact box | yes |
| **Referee** | *nothing* — engine retrieves the matching IFAB Law via the existing embedded index | Referee → Rule ambiguity | auto |
| **Historical** | What could/couldn't be seen; tech available then; how/if it was reviewed | Historical → Indeterminacy *or* Decision-time | yes |
| **Framing** | ≥2 named quotes, each with a source label (who said it + where) | Framing → Cultural bias | yes (≥2, in opposed valence, to fire) |

**Two clarifications on the mapping (the engine derives, the form does not set states):**
- The user does **not** pick cell states. The Historical block feeds the Historical lens; Granite
  reads it and emits a stance (SUPPORTS = decision-time gap → Decision-time PRESENT; DISPUTES =
  truth unrecoverable even now → Indeterminacy PRESENT; MIXED = info adequate → both ruled out).
  The deterministic router assigns the axes from that stance, exactly as for curated incidents.
- Framing fires Cultural bias (PRESENT) only when the supplied quotes are in **opposed valence**
  (one condemns, one justifies — a MIXED stance). Two quotes that agree are one-sided → Cultural
  bias is ruled out. The UI states this so a user understands why two same-side quotes do not fire it.
| **Tactical** | Optional data note | Tactical | optional |

**Guard rails (integrity):**
- Minimums enforced client-side: no quotes → Framing cannot fire → UI states this plainly,
  never a fabricated result.
- Every quote requires a source label (name + where). No anonymous evidence — same receipt
  standard as the curated incidents.
- The engine still cite-or-dies: anything Granite cannot ground, Guardian demotes → cell shows
  `Not documented`. A thin incident returns a thin SPLIT. **This is the integrity feature.**

**Two on-ramps so it is never a blank page:**
1. **"Load an example"** pre-fills the form with a real case and renders a **pre-baked Studio
   fixture** — so even with no backend (public site), a judge sees a complete real Studio result
   end to end.
2. *(Stretch, not v1)* Free-form paste → Granite auto-sorts the blob into the four blocks for
   user review.

**Output** = the **exact same Explore renderer** (Settled Fact → THE SPLIT → four lenses →
Guardian seals → provenance). One renderer, two incident sources. The user recognizes it
immediately because they just saw it in Explore.

## Backend & the live pipeline

New thin service wrapping the existing engine. No engine-logic rewrite.

**`engine/serve/` — FastAPI**
- `POST /decompose` — takes the Studio form, builds an in-memory incident, runs the real
  pipeline, **streams** step events via SSE.
- `GET /health` — reports Ollama reachable + the three models pulled. Studio polls this to
  enable/disable submit and pick its mode.

**`engine/serve/incident_from_form.py`** — the one genuinely new piece: turns the form into the
same in-memory shape the corpus folders produce today (framing quotes + historical facts → atoms;
Referee retrieved from the existing IFAB index). This replaces "corpus folder" as the evidence source.

**`engine/serve/stream.py`** — emits step events around the existing pipeline calls.

**Streaming contract (SSE event types):**
```
retrieve  {lens, found:[{citation_id, page}]}     → "found Law 12 handball (p.110)"
lens      {lens, stance, rationale}               → "clear single clause…"
audit     {lens, verdict}                         → GROUNDED / UNGROUNDED
cell      {axis, state}                            → box fills in live
done      {bundle}                                 → full IncidentBundle (renders via SplitView)
error     {message}
```
The UI fills the four boxes one at a time as `cell` events arrive — the "watch it compute"
payoff that proves computation and teaches the SPLIT.

**Provenance:** a Studio result is stamped `live · user-supplied evidence · <models> ·
<timestamp>`, clearly distinct from the frozen-corpus seal. It never claims byte-reproducibility
(it is user input). **No faked verdicts — the sacred rule holds: every Guardian verdict is a real
captured Ollama token.**

## Public-site vs self-host behavior

**Public Vercel (no backend reachable):**
- Studio renders the full form + a banner: *"Live decomposition runs the real Granite models on
  your machine — not on this `$0` static host. One command starts it locally. Here's how ↓"*
- "Load an example" works fully (pre-baked Studio fixture). Health-poll fails → submit disabled
  with the how-to, never a broken spinner.

**Local / self-hosted (author or judge):**
- One command: `docker compose up` (or `make studio`) starts Ollama + pulls models + FastAPI +
  points web at `localhost:8000`. Health-poll succeeds → submit enabled → real live streaming.
- README "Run the Studio yourself" section: three copy-paste steps.

This keeps the `$0` static story 100% intact (cost exists only on a machine that opts in) and
makes self-hostability — which most entries cannot claim — a moat.

## Contract changes

- Extend `engine/offside_engine/export_types.py`:
  - a `StudioStreamEvent` union (`retrieve | lens | audit | cell | done | error`)
  - `provenance.mode: "frozen" | "live-user"` (existing frozen fixtures default to `"frozen"`)
- Regenerate `web/types/contract.ts`. CI contract-sync must stay green.

## Web components

- `web/app/` → tab shell (**Explore · Studio · How it works**); masthead + hook above tabs.
- `web/components/studio/StudioForm.tsx` — four-block guided form, validation, "Load example".
- `web/components/studio/LiveSplit.tsx` — consumes SSE, fills boxes live, then hands off to the
  **existing** `SplitView` / `LensPanels` (reused renderer).
- `web/lib/studioClient.ts` — health poll, SSE consumption, mode detection.
- One pre-baked **Studio example fixture** for the no-backend path.

## Build order (each a working checkpoint)

1. **Tabs revamp** (pure reorg, no backend) — ships value immediately, fixes "too complex".
2. **`incident_from_form` + `POST /decompose` non-streaming** — real SPLIT from a form, tested.
3. **SSE streaming + `LiveSplit`** box-fill.
4. **Health/mode detection + public-site banner + example fixture.**
5. **`docker compose` / `make studio` + README self-host section.**
6. **Tests + demo polish.**

## Testing & integrity

- `incident_from_form`: form → in-memory incident mapping is correct and complete.
- Empty/thin evidence → honest `Not documented`, **never fabrication** (the integrity test).
- Guardian still audits user incidents; a verdict is always a real captured token.
- No-numbers moat + cite-or-die hold on user incidents (reuse existing schema-walk test).
- `GET /health` reports model availability correctly (mocked Ollama).
- Contract-sync (export_types vs committed `contract.ts`) stays green.
- Web typecheck + `next build` stay green.

## Risks & mitigations

- **Backend unreachable mid-demo** → pre-baked example fixture always renders a complete real
  result; submit degrades to a clear how-to, never a broken state.
- **User supplies thin evidence and the SPLIT looks empty** → framed as the integrity feature
  ("the tool refuses to invent"), with inline guidance on what each block needs to fire.
- **Scope creep toward accounts/libraries** → explicitly out of scope; v1 is single-incident,
  stateless.
- **Inverting the architecture (model at runtime)** is contained to `engine/serve/`; the frozen
  Explore path and its `$0` provenance are untouched.

## Out of scope (future)

- Free-form paste → auto-sort (stretch within Studio, not v1).
- Saved private libraries, accounts, cross-incident pattern analytics.
- Always-on hosted backend for the public site.
