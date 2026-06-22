<div align="center">

# OFFSIDE

### The Football Disagreement Engine

**VAR gives officials seven camera angles. Fans get a tweet.**

OFFSIDE doesn't tell you whether the referee was right — it shows you, with the
receipts, exactly *why* a billion people will never agree.

</div>

---

> **Status:** 🚧 In active development for the IBM June Challenge (*Soccer, AI & the World Cup*).
> This README grows alongside the build.

## The problem

Billions watch the same match and experience it completely differently. The same
four seconds — Maradona's hand, 1986 — is *"the greatest goal in history"* in Buenos
Aires and *"he cheated"* in London. Both certain. Both internally consistent.

Today's football AI tells you **what happened** and adjudicates **whether a call was
correct**. OFFSIDE answers the question nobody else does:

> **Why do informed, intelligent people look at the same incident and refuse to
> agree — and why does that disagreement persist?**

## The approach

OFFSIDE reconstructs a contested moment through four evidence-grounded lenses
(Referee, Tactical, Historical, Framing) and decomposes the disagreement into a
single artifact — **THE SPLIT** — that attributes *why it stays contested* across
four fixed dimensions:

- **Rule Ambiguity** — the Laws themselves are unclear
- **Indeterminacy** — the fact stays contested even with today's technology
- **Decision-Time Deficit** — knowable now, but not at the moment of the call
- **Cultural / Prior Bias** — agreement on facts, divergence on the acceptable outcome

Every cell of THE SPLIT is grounded: it click-traces to a specific, page-numbered
passage of the actual **IFAB Laws of the Game**, extracted with IBM Docling. The
reasoning model is **structurally forbidden from emitting a number** — no fabricated
percentages, ever. Where there is no evidence, OFFSIDE says so.

## Why it matters

This is the World Cup's emotional core made legible: not *who was right*, but *why
the world divides* — built as human-centered, explainable, trustworthy AI.

## Built with IBM

| Tool | Role |
|------|------|
| **IBM Granite** | Grounded synthesis of *why* disagreement persists — never verdicts, never numbers |
| **Docling** | Extracts the IFAB Laws into structured, page-cited evidence — the trust spine |
| **Langflow** | Visible orchestration of the four-lens → synthesis pipeline |
| **Context Forge** | Governed MCP gateway over the lens agents *(secondary)* |

*Detailed architecture, setup, and demo to follow as the build progresses.*

## License

Source code: [MIT](LICENSE). Data sources (StatsBomb Open Data, IFAB Laws of the
Game, IBM Granite) are governed by their own separate terms — see LICENSES.md.
