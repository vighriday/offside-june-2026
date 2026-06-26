# OFFSIDE Live Studio Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Studio surface where a user supplies the human evidence for a contested decision and the real Granite pipeline decomposes it live (boxes fill in over SSE), plus a tabs revamp (Explore / Studio / How it works), with a local + self-hostable backend so the public Vercel site stays $0 static.

**Architecture:** A new FastAPI service (`engine/serve/`) wraps the existing, unchanged bake. A new `incident_from_form.py` turns a form payload into the same `(IncidentSpec, citations pool)` the corpus folders produce, then calls the existing `bake_incident`. The web app gains a tab shell; the Studio tab posts the form, consumes Server-Sent Events, and fills the four SPLIT boxes live, reusing the existing `SplitView`/`LensPanels` renderer for the final result.

**Tech Stack:** Python 3.12, FastAPI + `sse-starlette`, Ollama (granite3.3:8b, granite-embedding:30m, granite3-guardian:2b), pydantic v2, Next.js 16.2.9 + React, IBM Carbon, uv, pytest.

## Global Constraints

- Commits authored as **Hriday Vig <vighriday@gmail.com>** with **zero** AI/Claude trailers, hand-authored messages.
- **No-numbers moat:** Granite-facing schemas (`LensOutput`, `SplitCell`, `Split`) never gain a numeric field. The Studio adds no numeric field to any model a viewer reads as a magnitude.
- **Cite-or-die:** every grounded reading carries ≥1 citation; thin user evidence yields `Not documented`, never fabrication.
- **Never fake a Guardian verdict:** every verdict is a real captured Ollama token. The offline `deterministic-router` seal is never claimed for a Studio result.
- Engine bake logic is **reused unchanged**; the only genuinely new engine module is `incident_from_form.py` and the thin `serve/` wrappers.
- Python runs under `uv` (`cd engine && uv run …`); web under `npm` in `web/`.
- CI gates must stay green: ruff, pytest, contract-sync (`export_types` vs committed `contract.ts`), web typecheck, `next build`.
- `_local/`, `Images/` stay gitignored; API keys only in gitignored `.env`.

---

### Task 1: Tabs shell — lift masthead above Explore/Studio/How-it-works

**Files:**
- Create: `web/components/TabShell.tsx`
- Create: `web/components/tabs.module.css` (or extend the global stylesheet used by siblings — match the existing pattern in `web/components/`)
- Modify: `web/components/IncidentExplorer.tsx` (remove the in-body `<Hero/>` and `<HowItWorks/>`, keep only the Explore content)
- Modify: `web/app/page.tsx` (render `TabShell` wrapping the explorer)
- Test: `web/__tests__/tabshell.test.tsx` (if a web test runner exists; otherwise rely on typecheck + build as the gate — see Step 2)

**Interfaces:**
- Consumes: `IncidentExplorer` (existing, props `{ incidents: LoadedBundle[] }`), `Hero`, `HowItWorks` (existing components).
- Produces: `TabShell({ incidents }: { incidents: LoadedBundle[] })` — renders masthead + hook + a three-tab switcher. Tab state is client `useState<"explore" | "studio" | "how">`. Default `"explore"`.

- [ ] **Step 1: Confirm whether a web test runner is configured**

Run: `cd web && npm run -s 2>/dev/null; cat package.json | grep -A15 '"scripts"'`
Expected: see whether a `test` script exists. If none, this task is gated by `npm run typecheck` + `npm run build` (no unit test). Note the result and proceed accordingly — do not add a test runner just for this.

- [ ] **Step 2: Create `TabShell.tsx`**

```tsx
"use client";

import { useState } from "react";
import { Hero } from "./Hero";
import { HowItWorks } from "./HowItWorks";
import { IncidentExplorer, type LoadedBundle } from "./IncidentExplorer";
import { StudioPanel } from "./studio/StudioPanel";

type Tab = "explore" | "studio" | "how";

const TABS: { id: Tab; label: string }[] = [
  { id: "explore", label: "Explore" },
  { id: "studio", label: "Studio" },
  { id: "how", label: "How it works" },
];

// The masthead + Buenos Aires/London hook are the identity — pinned above the tabs, always
// visible. Below them, exactly one surface shows at a time: see it work (Explore), do it
// yourself (Studio), understand it (How it works). This is the fix for the single-scroll
// complexity: one idea per surface instead of everything stacked.
export function TabShell({ incidents }: { incidents: LoadedBundle[] }) {
  const [tab, setTab] = useState<Tab>("explore");
  return (
    <main className="shell">
      <Hero />
      <nav className="shell__tabs" role="tablist" aria-label="OFFSIDE sections">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            role="tab"
            aria-selected={tab === t.id}
            className="shell__tab"
            data-active={tab === t.id}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>
      <div className="shell__panel" role="tabpanel">
        {tab === "explore" && <IncidentExplorer incidents={incidents} />}
        {tab === "studio" && <StudioPanel />}
        {tab === "how" && <HowItWorks />}
      </div>
    </main>
  );
}
```

- [ ] **Step 3: Create a minimal `StudioPanel` placeholder so the shell compiles**

Create `web/components/studio/StudioPanel.tsx`:

```tsx
"use client";

// Placeholder — Task 6 replaces this with the real form + live result.
export function StudioPanel() {
  return (
    <section className="studio" aria-label="Studio">
      <p>Studio — decompose your own controversy. (coming up)</p>
    </section>
  );
}
```

- [ ] **Step 4: Remove `<Hero/>` and `<HowItWorks/>` from `IncidentExplorer`**

In `web/components/IncidentExplorer.tsx`, delete the `<Hero />` and `<HowItWorks />` lines from the returned JSX (they now live in `TabShell`). Remove their now-unused imports. Keep everything else (DivergenceLineage, SettledFact, SplitView, FalsificationPanel, RuleEvolution, LensPanels, ProvenanceFooter).

- [ ] **Step 5: Wire `TabShell` into `page.tsx`**

```tsx
import { loadIncident } from "@/lib/fixtures";
import { TabShell } from "@/components/TabShell";
import type { LoadedBundle } from "@/components/IncidentExplorer";

const INCIDENT_IDS = [
  "hand-of-god-1986",
  "handball-rewrite",
  "offside-margin",
  "pgmol-subjective",
  "suarez-handball-2010",
  "lampard-ghost-goal-2010",
];

export default async function Home() {
  const loaded: LoadedBundle[] = [];
  for (const id of INCIDENT_IDS) {
    try {
      loaded.push(await loadIncident(id));
    } catch {
      // fixture not baked yet — skip it rather than fail the page
    }
  }
  return <TabShell incidents={loaded} />;
}
```

- [ ] **Step 6: Add tab styling**

Add `.shell__tabs`, `.shell__tab` (with `[data-active="true"]`), `.shell__panel` to the stylesheet the other components use (find it by grepping where `.lens-panels` is defined: `cd web && grep -rl "lens-panels" app components styles 2>/dev/null`). Match IBM Carbon spacing/IBM Plex per the existing tokens. Underline-style active tab, no childish look.

- [ ] **Step 7: Typecheck + build**

Run: `cd web && npm run typecheck && npm run build`
Expected: PASS, 3 static pages generated, no type errors.

- [ ] **Step 8: Commit**

```bash
git add web/components/TabShell.tsx web/components/studio/StudioPanel.tsx web/components/IncidentExplorer.tsx web/app/page.tsx web/<stylesheet>
git commit -m "feat(web): three-tab shell (Explore / Studio / How it works) with pinned masthead"
```

---

### Task 2: `incident_from_form` — build a spec + citation pool from a form payload

**Files:**
- Create: `engine/offside_engine/serve/__init__.py` (empty)
- Create: `engine/offside_engine/serve/form_models.py`
- Create: `engine/offside_engine/serve/incident_from_form.py`
- Test: `engine/tests/test_incident_from_form.py`

**Interfaces:**
- Consumes (existing, verified signatures):
  - `from offside_engine.bake.incident import IncidentSpec` — dataclass with fields `incident_id, title, settled_status, settled_statement, settled_citation_ids, admission_note, lens_queries: dict[LensKind,str], allowed_citation_ids: frozenset[str], expected_thesis`.
  - `from offside_engine.analyze.split_schema import Citation` — fields `id, source_doc, doc_kind, page, bbox, extracted_text, attribution`.
  - `from offside_engine.ingest.curate import build_curated_citations` → `list[Citation]` (the IFAB law atoms; reuse so the Referee lens has Laws to retrieve).
- Produces:
  - `FormPayload` (pydantic) — the validated Studio form.
  - `build_studio_incident(payload: FormPayload) -> tuple[IncidentSpec, dict[str, Citation]]` — returns the spec (with `expected_thesis={}` — user incidents have no oracle) and the full citation pool (IFAB law atoms + the user's framing/historical atoms).

- [ ] **Step 1: Write the failing test**

```python
# engine/tests/test_incident_from_form.py
from offside_engine.serve.form_models import FormPayload, Quote
from offside_engine.serve.incident_from_form import build_studio_incident


def _payload() -> FormPayload:
    return FormPayload(
        title="A disputed penalty",
        settled_statement="A defender's arm blocked the ball in the box. The arm contact is agreed.",
        historical_note="VAR reviewed it on a clear replay; the contact was fully visible.",
        quotes=[
            Quote(speaker="Home manager", source="post-match", text="clear penalty, the arm was out"),
            Quote(speaker="Away manager", source="post-match", text="never a penalty, ball to hand"),
        ],
        tactical_note=None,
    )


def test_build_studio_incident_returns_spec_and_pool():
    spec, pool = build_studio_incident(_payload())
    # spec has no thesis oracle for a user incident
    assert spec.expected_thesis == {}
    assert spec.title == "A disputed penalty"
    # the four lens queries are present so every lens can retrieve
    assert set(spec.lens_queries) == {"REFEREE", "TACTICAL", "HISTORICAL", "FRAMING"}
    # the pool carries IFAB law atoms (for Referee retrieval) AND the user's atoms
    kinds = {c.doc_kind for c in pool.values()}
    assert "IFAB_LAW" in kinds
    assert "FRAMING_SOURCE" in kinds
    assert "HISTORICAL_REPORT" in kinds
    # every user atom id is in the allow-list, and the allow-list ⊆ pool ids
    assert spec.allowed_citation_ids <= set(pool)


def test_two_opposed_quotes_produce_two_framing_atoms():
    spec, pool = build_studio_incident(_payload())
    framing = [c for c in pool.values() if c.doc_kind == "FRAMING_SOURCE"]
    assert len(framing) == 2


def test_thin_evidence_still_builds_but_yields_no_framing():
    p = FormPayload(
        title="x", settled_statement="y", historical_note="z", quotes=[], tactical_note=None
    )
    spec, pool = build_studio_incident(p)
    framing = [c for c in pool.values() if c.doc_kind == "FRAMING_SOURCE"]
    assert framing == []  # no quotes → no framing atoms → Cultural bias cannot fire (honest)
```

- [ ] **Step 2: Run it to verify it fails**

Run: `cd engine && uv run pytest tests/test_incident_from_form.py -v`
Expected: FAIL with `ModuleNotFoundError: offside_engine.serve.form_models`.

- [ ] **Step 3: Write `form_models.py`**

```python
"""The validated Studio form — the user-supplied evidence for one contested decision."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Quote(BaseModel):
    """One named-source quote. Every quote needs a speaker and where it was said — no
    anonymous evidence, same receipt standard as the curated incidents."""
    model_config = ConfigDict(extra="forbid")
    speaker: str = Field(min_length=1)
    source: str = Field(min_length=1)  # where it was said, e.g. "post-match press conference"
    text: str = Field(min_length=1)


class FormPayload(BaseModel):
    """The Studio form. The user brings the human evidence; the engine brings the rulebook."""
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1)
    settled_statement: str = Field(min_length=1)  # what everyone agrees happened
    historical_note: str = Field(default="")       # what could/couldn't be seen, tech, review
    quotes: list[Quote] = Field(default_factory=list)
    tactical_note: str | None = None
```

- [ ] **Step 4: Write `incident_from_form.py`**

```python
"""Turn a Studio FormPayload into the SAME (IncidentSpec, citation pool) shape the corpus
folders produce — so the unchanged bake can decompose a user-supplied incident exactly as
it does a curated one. The user brings the human evidence (settled facts, historical note,
named quotes); the IFAB law atoms are reused from the curated corpus so the Referee lens
retrieves the matching Law itself. No thesis oracle is attached: a user incident has no
documented answer to check against, so the SPLIT is whatever the evidence routes to."""
from __future__ import annotations

import re

from offside_engine.analyze.split_schema import Citation
from offside_engine.bake.incident import IncidentSpec
from offside_engine.ingest.curate import build_curated_citations
from offside_engine.serve.form_models import FormPayload


def _slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s or "incident"


_LENS_QUERIES = {
    "REFEREE": "Which Law governs this act, and is it a clear single offence clause or are clauses in conflict?",
    "TACTICAL": "Is there event-data context for this incident?",
    "HISTORICAL": "Could the officials see or review the decisive fact at the moment of the call, and is the truth recoverable now?",
    "FRAMING": "How did named figures describe the same agreed fact afterwards?",
}


def build_studio_incident(payload: FormPayload) -> tuple[IncidentSpec, dict[str, Citation]]:
    incident_id = f"studio-{_slug(payload.title)}"
    pool: dict[str, Citation] = {}

    # IFAB law atoms — reused verbatim so the Referee lens can retrieve the real Law page.
    law_atoms = build_curated_citations()
    for c in law_atoms:
        pool[c.id] = c

    user_ids: set[str] = set()

    # Historical atom (one), if supplied.
    if payload.historical_note.strip():
        hid = f"{incident_id}-hist"
        pool[hid] = Citation(
            id=hid,
            source_doc="studio-user-input",
            doc_kind="HISTORICAL_REPORT",
            extracted_text=payload.historical_note.strip(),
        )
        user_ids.add(hid)

    # Framing atoms — one per quote. Two in opposed valence are what fire Cultural bias.
    for i, q in enumerate(payload.quotes):
        qid = f"{incident_id}-framing-{i}"
        pool[qid] = Citation(
            id=qid,
            source_doc="studio-user-input",
            doc_kind="FRAMING_SOURCE",
            extracted_text=f"{q.speaker} ({q.source}): {q.text}",
        )
        user_ids.add(qid)

    # Tactical atom (optional, one).
    if payload.tactical_note and payload.tactical_note.strip():
        tid = f"{incident_id}-tactical"
        pool[tid] = Citation(
            id=tid,
            source_doc="studio-user-input",
            doc_kind="STATSBOMB_EVENT",
            extracted_text=payload.tactical_note.strip(),
        )
        user_ids.add(tid)

    # The Referee lens may surface any IFAB law atom; the human lenses may surface only the
    # user's own atoms. So the allow-list is the user's atoms plus every law atom.
    allowed = frozenset(user_ids | {c.id for c in law_atoms})

    spec = IncidentSpec(
        incident_id=incident_id,
        title=payload.title,
        settled_status="ADJUDICATED_CONTESTED",
        settled_statement=payload.settled_statement,
        settled_citation_ids=(),  # the settled fact is the user's prose; no forced citation
        admission_note="",
        lens_queries=dict(_LENS_QUERIES),
        allowed_citation_ids=allowed,
        expected_thesis={},  # no oracle for a user incident
    )
    return spec, pool
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `cd engine && uv run pytest tests/test_incident_from_form.py -v`
Expected: 3 PASS.

- [ ] **Step 6: Ruff**

Run: `cd engine && uv run ruff check offside_engine/serve tests/test_incident_from_form.py`
Expected: All checks passed.

- [ ] **Step 7: Commit**

```bash
git add engine/offside_engine/serve/__init__.py engine/offside_engine/serve/form_models.py engine/offside_engine/serve/incident_from_form.py engine/tests/test_incident_from_form.py
git commit -m "feat(engine): build a bakeable incident + citation pool from a Studio form"
```

---

### Task 3: `decompose` (non-streaming) — bake a user incident end to end

**Files:**
- Create: `engine/offside_engine/serve/run.py`
- Test: `engine/tests/test_serve_run.py`

**Interfaces:**
- Consumes (existing, verified signatures):
  - `bake_incident(spec, *, retriever: LensRetriever, granite: GraniteClient, guardian: GuardianClient, citations: dict[str,Citation], embed_model=DEFAULT_EMBED_MODEL, corpus_git_sha=None, strict_thesis=False) -> IncidentBundle`
  - `build_index(citations: list[Citation], db_dir: Path) -> int`
  - `LensRetriever(db_dir: Path)`, `GraniteClient(cfg)`, `GuardianClient(host=..., model=...)`, `load_granite_config()`, `DEFAULT_GUARDIAN_MODEL`.
  - `build_studio_incident(payload) -> (IncidentSpec, dict[str,Citation])` (Task 2).
- Produces:
  - `decompose(payload: FormPayload) -> IncidentBundle` — the whole non-streaming bake, mirroring `analyze_live.py`'s non-graph path but sourced from the form. `strict_thesis=False`, no probes, no rule_evolution, provenance mode marked live-user (Task 5 adds the field; here just return the bundle).

- [ ] **Step 1: Write the failing test (mocked models — no Ollama in CI)**

```python
# engine/tests/test_serve_run.py
from unittest.mock import patch

from offside_engine.serve.form_models import FormPayload, Quote


def _payload() -> FormPayload:
    return FormPayload(
        title="A disputed penalty",
        settled_statement="A defender's arm blocked the ball; the contact is agreed.",
        historical_note="VAR reviewed a clear replay; the contact was fully visible.",
        quotes=[
            Quote(speaker="Home", source="post-match", text="clear penalty"),
            Quote(speaker="Away", source="post-match", text="never a penalty"),
        ],
        tactical_note=None,
    )


def test_decompose_calls_bake_with_form_sourced_spec_and_pool():
    # We don't run Ollama in CI; assert decompose wires the form-built spec+pool into the
    # real bake. The bake itself is exercised by its own tests against live models.
    from offside_engine.serve import run as run_mod

    captured = {}

    def fake_bake(spec, **kw):
        captured["spec"] = spec
        captured["citations"] = kw["citations"]
        # return a sentinel; decompose must pass it straight through
        return "BUNDLE_SENTINEL"

    with patch.object(run_mod, "bake_incident", side_effect=fake_bake), \
         patch.object(run_mod, "build_index", return_value=3), \
         patch.object(run_mod, "LensRetriever"), \
         patch.object(run_mod, "GraniteClient"), \
         patch.object(run_mod, "GuardianClient"), \
         patch.object(run_mod, "load_granite_config"):
        out = run_mod.decompose(_payload())

    assert out == "BUNDLE_SENTINEL"
    assert captured["spec"].title == "A disputed penalty"
    assert captured["spec"].expected_thesis == {}
    # pool carries IFAB + user atoms
    kinds = {c.doc_kind for c in captured["citations"].values()}
    assert {"IFAB_LAW", "FRAMING_SOURCE", "HISTORICAL_REPORT"} <= kinds
```

- [ ] **Step 2: Run it to verify it fails**

Run: `cd engine && uv run pytest tests/test_serve_run.py -v`
Expected: FAIL with `ModuleNotFoundError: offside_engine.serve.run`.

- [ ] **Step 3: Write `run.py`**

```python
"""Run the real bake on a user-supplied Studio incident and return the IncidentBundle.

This mirrors analyze_live.py's non-graph path exactly — index the pool, build the three
real clients, bake — but the evidence comes from the form (Task 2) instead of a corpus
folder. strict_thesis is False (a user incident has no oracle); no probes, no rule
evolution. The bake is unchanged: same cite-or-die, same Guardian gate, same no-numbers."""
from __future__ import annotations

import tempfile
from pathlib import Path

from offside_engine.analyze.granite_client import GraniteClient
from offside_engine.analyze.guardian import GuardianClient
from offside_engine.bake.bake import bake_incident
from offside_engine.config import DEFAULT_GUARDIAN_MODEL, load_granite_config
from offside_engine.index.build_lance import build_index
from offside_engine.retrieve.lens_retrieve import LensRetriever
from offside_engine.serve.form_models import FormPayload
from offside_engine.serve.incident_from_form import build_studio_incident


def decompose(payload: FormPayload):
    """Bake the user incident with the real Granite + Guardian models. Returns IncidentBundle."""
    spec, pool = build_studio_incident(payload)
    cfg = load_granite_config()
    with tempfile.TemporaryDirectory() as tmp:
        db_dir = Path(tmp) / "lance"
        build_index(list(pool.values()), db_dir)
        retriever = LensRetriever(db_dir)
        granite = GraniteClient(cfg)
        guardian = GuardianClient(host=cfg.host, model=DEFAULT_GUARDIAN_MODEL)
        return bake_incident(
            spec,
            retriever=retriever,
            granite=granite,
            guardian=guardian,
            citations=pool,
            corpus_git_sha=None,
            strict_thesis=False,
        )
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd engine && uv run pytest tests/test_serve_run.py -v`
Expected: PASS.

- [ ] **Step 5: Ruff + commit**

```bash
cd engine && uv run ruff check offside_engine/serve/run.py tests/test_serve_run.py
git add engine/offside_engine/serve/run.py engine/tests/test_serve_run.py
git commit -m "feat(engine): decompose a Studio form into a real baked IncidentBundle"
```

---

### Task 4: FastAPI app — `GET /health` + `POST /decompose` (SSE streaming)

**Files:**
- Create: `engine/offside_engine/serve/stream.py`
- Create: `engine/offside_engine/serve/app.py`
- Modify: `engine/pyproject.toml` (add a `serve` optional-dependency group: `fastapi`, `sse-starlette`, `uvicorn`)
- Test: `engine/tests/test_serve_app.py`

**Interfaces:**
- Consumes: `decompose(payload)` (Task 3), `FormPayload` (Task 2).
- Produces:
  - `app` (FastAPI instance).
  - `GET /health` → `{"ok": bool, "ollama": bool, "models": {granite, embed, guardian: bool}}`.
  - `POST /decompose` → `text/event-stream` of `StudioStreamEvent` JSON (Task 5 defines the event shape; here emit `retrieve|lens|audit|cell|done|error`). CORS allows the web origin.

- [ ] **Step 1: Add the serve dependency group**

In `engine/pyproject.toml`, under `[project.optional-dependencies]`, add:

```toml
serve = ["fastapi>=0.115", "sse-starlette>=2.1", "uvicorn>=0.30"]
```

Run: `cd engine && uv sync --extra serve` → expected: resolves and installs fastapi, sse-starlette, uvicorn.

- [ ] **Step 2: Write the failing test (health + decompose route shape, decompose mocked)**

```python
# engine/tests/test_serve_app.py
from unittest.mock import patch

from fastapi.testclient import TestClient

from offside_engine.serve.app import app

client = TestClient(app)


def test_health_reports_structure():
    with patch("offside_engine.serve.app._ollama_up", return_value=False):
        r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert set(body) >= {"ok", "ollama", "models"}


def test_decompose_streams_events_ending_in_done():
    fake_events = [
        {"type": "cell", "axis": "RULE_AMBIGUITY", "state": "ABSENT"},
        {"type": "done", "bundle": {"incident_id": "studio-x"}},
    ]

    def fake_stream(payload):
        yield from fake_events

    payload = {
        "title": "x", "settled_statement": "y", "historical_note": "z",
        "quotes": [
            {"speaker": "a", "source": "s", "text": "t"},
            {"speaker": "b", "source": "s", "text": "u"},
        ],
        "tactical_note": None,
    }
    with patch("offside_engine.serve.app.stream_decompose", side_effect=fake_stream):
        r = client.post("/decompose", json=payload)
    assert r.status_code == 200
    text = r.text
    assert '"type": "cell"' in text or '"type":"cell"' in text
    assert "done" in text
```

- [ ] **Step 3: Run it to verify it fails**

Run: `cd engine && uv run pytest tests/test_serve_app.py -v`
Expected: FAIL (`offside_engine.serve.app` missing).

- [ ] **Step 4: Write `stream.py`**

```python
"""Step events for the Studio live run. Wraps the non-streaming decompose and emits one
event per visible step so the UI can fill the four SPLIT boxes one at a time. Every event
is derived from the REAL baked bundle — nothing is synthesised."""
from __future__ import annotations

from collections.abc import Iterator

from offside_engine.serve.form_models import FormPayload
from offside_engine.serve.run import decompose


def stream_decompose(payload: FormPayload) -> Iterator[dict]:
    """Yield {type: retrieve|lens|audit|cell|done|error} dicts from the real bake.

    The current bake is synchronous and returns the whole bundle, so we run it, then replay
    its real, already-computed steps as events in pipeline order. The states are the real
    routed states — the 'live' feel is honest narration of a real computation, not fakery."""
    try:
        bundle = decompose(payload)
    except Exception as exc:  # noqa: BLE001 — surfaced to the client as an error event
        yield {"type": "error", "message": str(exc)}
        return

    for sl in bundle.lenses:
        o, seal = sl.output, sl.seal
        yield {"type": "lens", "lens": o.lens, "stance": o.stance,
               "rationale": o.rationale, "citation_ids": list(o.citation_ids)}
        yield {"type": "audit", "lens": o.lens, "verdict": seal.verdict,
               "guardian_model": seal.guardian_model}
    for cell in bundle.split.cells:
        yield {"type": "cell", "axis": cell.axis, "state": cell.state}
    yield {"type": "done", "bundle": bundle.model_dump(mode="json")}
```

> Note: `retrieve` events are folded into `lens` (the citation_ids the lens surfaced). If a future task makes the bake itself stream mid-computation, split them out then — YAGNI now.

- [ ] **Step 5: Write `app.py`**

```python
"""The Studio backend: GET /health and POST /decompose (SSE). Thin — all real work is in
the unchanged bake, reached via stream_decompose. Runs locally (author's machine) or via
self-host; the public Vercel site never reaches it (it falls back to the example fixture)."""
from __future__ import annotations

import json

import ollama
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from offside_engine.config import (
    DEFAULT_EMBED_MODEL,
    DEFAULT_GUARDIAN_MODEL,
    load_granite_config,
)
from offside_engine.serve.form_models import FormPayload
from offside_engine.serve.stream import stream_decompose

app = FastAPI(title="OFFSIDE Studio")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://offside-june-2026.vercel.app"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _ollama_up() -> bool:
    try:
        ollama.list()
        return True
    except Exception:  # noqa: BLE001
        return False


@app.get("/health")
def health() -> dict:
    up = _ollama_up()
    have = set()
    if up:
        try:
            have = {m["model"] for m in ollama.list().get("models", [])}
        except Exception:  # noqa: BLE001
            have = set()
    cfg = load_granite_config()
    models = {
        "granite": cfg.model in have,
        "embed": DEFAULT_EMBED_MODEL in have,
        "guardian": DEFAULT_GUARDIAN_MODEL in have,
    }
    return {"ok": up and all(models.values()), "ollama": up, "models": models}


@app.post("/decompose")
async def decompose_route(payload: FormPayload) -> EventSourceResponse:
    def gen():
        for event in stream_decompose(payload):
            yield {"data": json.dumps(event)}
    return EventSourceResponse(gen())
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `cd engine && uv run pytest tests/test_serve_app.py -v`
Expected: 2 PASS. (If `TestClient` SSE buffering trims output, assert on `r.status_code` + that the mocked generator was consumed instead.)

- [ ] **Step 7: Ruff + commit**

```bash
cd engine && uv run ruff check offside_engine/serve tests/test_serve_app.py
git add engine/offside_engine/serve/stream.py engine/offside_engine/serve/app.py engine/pyproject.toml engine/uv.lock engine/tests/test_serve_app.py
git commit -m "feat(engine): FastAPI Studio backend — /health + streaming /decompose"
```

---

### Task 5: Contract — `provenance.mode` + `StudioStreamEvent`, regenerate `contract.ts`

**Files:**
- Modify: `engine/offside_engine/analyze/split_schema.py` (add `mode` field to `BakeProvenance`)
- Modify: `engine/offside_engine/export_types.py` (export `mode` + a `StudioStreamEvent` union)
- Modify: `engine/offside_engine/serve/stream.py` (stamp `bundle.provenance.mode = "live-user"` on the done event's bundle)
- Modify: `web/types/contract.ts` (regenerated, committed)
- Test: `engine/tests/test_export_types.py` (extend), `engine/tests/test_serve_stream_mode.py` (new)

**Interfaces:**
- Produces: `BakeProvenance.mode: Literal["frozen", "live-user"] = "frozen"` (default keeps every existing frozen fixture valid with no change). `StudioStreamEvent` TS union with the six event variants.

- [ ] **Step 1: Write the failing tests**

```python
# engine/tests/test_serve_stream_mode.py
from offside_engine.analyze.split_schema import BakeProvenance


def test_provenance_defaults_to_frozen():
    p = BakeProvenance(granite_model="g", guardian_model="gu", embed_model="e")
    assert p.mode == "frozen"


def test_provenance_accepts_live_user():
    p = BakeProvenance(granite_model="g", guardian_model="gu", embed_model="e", mode="live-user")
    assert p.mode == "live-user"
```

Add to `engine/tests/test_export_types.py` (a new assertion in the existing contract-shape test, or a new test):

```python
def test_contract_exports_studio_stream_event_and_mode():
    from offside_engine.export_types import build_ts
    ts = build_ts()
    assert "StudioStreamEvent" in ts
    assert "live-user" in ts and "frozen" in ts
```

- [ ] **Step 2: Run to verify they fail**

Run: `cd engine && uv run pytest tests/test_serve_stream_mode.py tests/test_export_types.py -v`
Expected: FAIL (`mode` unknown field; `StudioStreamEvent` not in TS).

- [ ] **Step 3: Add `mode` to `BakeProvenance`**

In `split_schema.py`, in `BakeProvenance`, add (after `corpus_git_sha`):

```python
    mode: Literal["frozen", "live-user"] = "frozen"
    """Whether this bundle was frozen from the committed corpus (default) or produced live
    from user-supplied evidence in the Studio. A live-user result never claims byte
    reproducibility — only the same SPLIT/citations/verdicts for the same input."""
```

(Ensure `Literal` is imported — it already is.)

- [ ] **Step 4: Export the new types**

In `export_types.py`, add a hand-written TS block for `StudioStreamEvent` (the streaming events are not pydantic models on the wire, so emit them as a TS union literal). Append within the generated output:

```python
_STUDIO_EVENTS_TS = '''
export type StudioStreamEvent =
  | { type: "retrieve"; lens: LensKind; found: { citation_id: string; page: number | null }[] }
  | { type: "lens"; lens: LensKind; stance: LensStance; rationale: string; citation_ids: string[] }
  | { type: "audit"; lens: LensKind; verdict: GuardianVerdict; guardian_model: string }
  | { type: "cell"; axis: SplitAxis; state: CellState }
  | { type: "done"; bundle: IncidentBundle }
  | { type: "error"; message: string };
'''
```

and concatenate `_STUDIO_EVENTS_TS` into the string `build_ts()` returns (after the model interfaces, so the referenced types exist). Confirm `LensKind`, `LensStance`, `GuardianVerdict`, `SplitAxis`, `CellState`, `IncidentBundle` are all already exported above it.

- [ ] **Step 5: Stamp `live-user` in the stream**

In `stream.py`, before `model_dump`, set the mode:

```python
    bundle = bundle.model_copy(update={
        "provenance": bundle.provenance.model_copy(update={"mode": "live-user"})
    })
    yield {"type": "done", "bundle": bundle.model_dump(mode="json")}
```

- [ ] **Step 6: Regenerate the contract**

Run: `cd engine && uv run python -m offside_engine.export_types`
Expected: writes `web/types/contract.ts`. Then: `git diff --stat web/types/contract.ts` shows `mode` + `StudioStreamEvent` added.

- [ ] **Step 7: Run tests + contract-sync check**

Run: `cd engine && uv run pytest tests/test_serve_stream_mode.py tests/test_export_types.py -v`
Expected: PASS. The committed `contract.ts` now matches `build_ts()`.

- [ ] **Step 8: Commit**

```bash
git add engine/offside_engine/analyze/split_schema.py engine/offside_engine/export_types.py engine/offside_engine/serve/stream.py web/types/contract.ts engine/tests/test_serve_stream_mode.py engine/tests/test_export_types.py
git commit -m "feat(contract): provenance.mode (frozen|live-user) + StudioStreamEvent union"
```

---

### Task 6: Studio form + live result UI

**Files:**
- Create: `web/lib/studioClient.ts`
- Create: `web/components/studio/StudioForm.tsx`
- Create: `web/components/studio/LiveSplit.tsx`
- Rewrite: `web/components/studio/StudioPanel.tsx` (replace the Task 1 placeholder)
- Create: `web/fixtures/studio-example.json` (a real pre-baked Studio bundle — produced in Task 7; until then `StudioPanel` guards its absence)
- Test: gated by `npm run typecheck` + `npm run build` (+ unit test only if a runner exists, per Task 1 Step 1)

**Interfaces:**
- Consumes: `StudioStreamEvent`, `IncidentBundle` (from `@/types/contract`), existing `SplitView`, `LensPanels`, `SettledFact`, `ProvenanceFooter`.
- Produces:
  - `studioClient.ts`: `checkHealth(base: string): Promise<HealthResult>`, `decomposeStream(base, payload, onEvent): Promise<void>` (POST + read `text/event-stream` via `fetch` + `ReadableStream`), `STUDIO_BASE` (default `http://localhost:8000`, overridable by `process.env.NEXT_PUBLIC_STUDIO_BASE`).
  - `StudioForm`: the four-block form + validation + "Load example".
  - `LiveSplit`: consumes events, fills four boxes, then renders the full bundle via existing components.

- [ ] **Step 1: Write `studioClient.ts`**

```ts
import type { IncidentBundle, StudioStreamEvent } from "@/types/contract";

export interface HealthResult {
  ok: boolean;
  ollama: boolean;
  models: { granite: boolean; embed: boolean; guardian: boolean };
}

export interface StudioFormPayload {
  title: string;
  settled_statement: string;
  historical_note: string;
  quotes: { speaker: string; source: string; text: string }[];
  tactical_note: string | null;
}

export const STUDIO_BASE =
  process.env.NEXT_PUBLIC_STUDIO_BASE ?? "http://localhost:8000";

export async function checkHealth(base = STUDIO_BASE): Promise<HealthResult | null> {
  try {
    const r = await fetch(`${base}/health`, { cache: "no-store" });
    if (!r.ok) return null;
    return (await r.json()) as HealthResult;
  } catch {
    return null; // backend not reachable → public-site fallback
  }
}

// POST the form, read the SSE stream, call onEvent for each parsed event.
export async function decomposeStream(
  payload: StudioFormPayload,
  onEvent: (e: StudioStreamEvent) => void,
  base = STUDIO_BASE,
): Promise<void> {
  const r = await fetch(`${base}/decompose`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!r.ok || !r.body) throw new Error(`decompose failed: ${r.status}`);
  const reader = r.body.getReader();
  const dec = new TextDecoder();
  let buf = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    // SSE frames are separated by a blank line; each "data:" line carries one JSON event.
    const frames = buf.split("\n\n");
    buf = frames.pop() ?? "";
    for (const frame of frames) {
      const line = frame.split("\n").find((l) => l.startsWith("data:"));
      if (!line) continue;
      const json = line.slice(line.indexOf(":") + 1).trim();
      if (json) onEvent(JSON.parse(json) as StudioStreamEvent);
    }
  }
}

export type { IncidentBundle };
```

- [ ] **Step 2: Write `LiveSplit.tsx`** (fills four boxes as `cell` events arrive, renders the full result on `done`)

```tsx
"use client";

import { useState } from "react";
import type { CellState, IncidentBundle, SplitAxis, StudioStreamEvent } from "@/types/contract";
import { SplitView } from "../SplitView";
import { LensPanels } from "../LensPanels";
import { SettledFact } from "../SettledFact";
import { ProvenanceFooter } from "../ProvenanceFooter";

const AXES: SplitAxis[] = [
  "RULE_AMBIGUITY", "INDETERMINACY", "DECISION_TIME_DEFICIT", "CULTURAL_PRIOR_BIAS",
];
const AXIS_LABEL: Record<SplitAxis, string> = {
  RULE_AMBIGUITY: "Is the rule unclear?",
  INDETERMINACY: "Is the truth unknowable?",
  DECISION_TIME_DEFICIT: "Could the ref see it in time?",
  CULTURAL_PRIOR_BIAS: "Do the sides just want their own way?",
};

export function LiveSplit({ events, bundle }: {
  events: StudioStreamEvent[];
  bundle: IncidentBundle | null;
}) {
  const filled: Partial<Record<SplitAxis, CellState>> = {};
  for (const e of events) if (e.type === "cell") filled[e.axis] = e.state;

  if (bundle) {
    // Final result — reuse the exact Explore renderer so the user recognises it.
    return (
      <div>
        <SettledFact fact={bundle.settled_fact} title={bundle.title} incidentId={bundle.incident_id} />
        <SplitView bundle={bundle} />
        <LensPanels lenses={bundle.lenses} citations={bundle.citations} />
        <ProvenanceFooter provenance={bundle.provenance} citations={bundle.citations} />
      </div>
    );
  }

  // Live: the four boxes fill in one at a time as cell events arrive.
  return (
    <div className="live-split" aria-live="polite">
      {AXES.map((axis) => (
        <div key={axis} className="live-split__cell" data-state={filled[axis] ?? "pending"}>
          <p className="live-split__q">{AXIS_LABEL[axis]}</p>
          <p className="live-split__state">{filled[axis] ?? "…computing"}</p>
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 3: Write `StudioForm.tsx`** (four blocks, ≥2-quote validation, "Load example")

```tsx
"use client";

import { useState } from "react";
import type { StudioFormPayload } from "@/lib/studioClient";

const EXAMPLE: StudioFormPayload = {
  title: "A disputed penalty",
  settled_statement:
    "A defender's arm blocked the ball inside the box. The arm-to-ball contact is agreed by both sides.",
  historical_note:
    "VAR reviewed the incident on a clear, side-on replay; the contact was fully visible and reviewable in real time.",
  quotes: [
    { speaker: "Home manager", source: "post-match interview", text: "That's a clear penalty — the arm was out, away from the body." },
    { speaker: "Away manager", source: "post-match interview", text: "Never a penalty — it's ball to hand, the arm didn't move." },
  ],
  tactical_note: null,
};

export function StudioForm({ disabled, onRun }: {
  disabled: boolean;
  onRun: (p: StudioFormPayload) => void;
}) {
  const [form, setForm] = useState<StudioFormPayload>({
    title: "", settled_statement: "", historical_note: "",
    quotes: [{ speaker: "", source: "", text: "" }, { speaker: "", source: "", text: "" }],
    tactical_note: null,
  });

  const filledQuotes = form.quotes.filter((q) => q.speaker && q.source && q.text);
  const canRun = !disabled && form.title.trim() && form.settled_statement.trim() &&
    form.historical_note.trim() && filledQuotes.length >= 2;

  return (
    <form className="studio-form" onSubmit={(e) => { e.preventDefault(); onRun({ ...form, quotes: filledQuotes }); }}>
      {/* The moment */}
      <label>Title<input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} /></label>
      <label>What's agreed (settled facts)
        <textarea value={form.settled_statement} onChange={(e) => setForm({ ...form, settled_statement: e.target.value })} />
      </label>
      {/* Historical */}
      <label>What could/couldn't be seen, the tech, how it was reviewed
        <textarea value={form.historical_note} onChange={(e) => setForm({ ...form, historical_note: e.target.value })} />
      </label>
      {/* Framing — two quotes minimum, in opposed valence to fire Cultural bias */}
      {form.quotes.map((q, i) => (
        <fieldset key={i}>
          <input placeholder="Speaker" value={q.speaker}
            onChange={(e) => { const qs = [...form.quotes]; qs[i] = { ...q, speaker: e.target.value }; setForm({ ...form, quotes: qs }); }} />
          <input placeholder="Where said" value={q.source}
            onChange={(e) => { const qs = [...form.quotes]; qs[i] = { ...q, source: e.target.value }; setForm({ ...form, quotes: qs }); }} />
          <input placeholder="Quote" value={q.text}
            onChange={(e) => { const qs = [...form.quotes]; qs[i] = { ...q, text: e.target.value }; setForm({ ...form, quotes: qs }); }} />
        </fieldset>
      ))}
      <button type="button" onClick={() => setForm({ ...form, quotes: [...form.quotes, { speaker: "", source: "", text: "" }] })}>
        + add a quote
      </button>
      {/* Tactical (optional) */}
      <label>Data note (optional)
        <textarea value={form.tactical_note ?? ""} onChange={(e) => setForm({ ...form, tactical_note: e.target.value || null })} />
      </label>

      <div className="studio-form__actions">
        <button type="button" onClick={() => setForm(EXAMPLE)}>Load an example</button>
        <button type="submit" disabled={!canRun}>Decompose live</button>
      </div>
      {!canRun && filledQuotes.length < 2 && (
        <p className="studio-form__hint">Add at least two named quotes in opposed valence for Cultural bias to fire.</p>
      )}
    </form>
  );
}
```

- [ ] **Step 4: Rewrite `StudioPanel.tsx`** (health-driven mode, banner, run wiring, example fixture fallback)

```tsx
"use client";

import { useEffect, useState } from "react";
import type { IncidentBundle, StudioStreamEvent } from "@/types/contract";
import { checkHealth, decomposeStream, type StudioFormPayload } from "@/lib/studioClient";
import { StudioForm } from "./StudioForm";
import { LiveSplit } from "./LiveSplit";

export function StudioPanel() {
  const [healthy, setHealthy] = useState<boolean | null>(null);
  const [events, setEvents] = useState<StudioStreamEvent[]>([]);
  const [bundle, setBundle] = useState<IncidentBundle | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { checkHealth().then((h) => setHealthy(!!h?.ok)); }, []);

  async function run(payload: StudioFormPayload) {
    setEvents([]); setBundle(null); setError(null); setRunning(true);
    try {
      await decomposeStream(payload, (e) => {
        setEvents((prev) => [...prev, e]);
        if (e.type === "done") setBundle(e.bundle);
        if (e.type === "error") setError(e.message);
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setRunning(false);
    }
  }

  return (
    <section className="studio" aria-label="Studio">
      <header className="studio__head">
        <h2>Decompose your own controversy</h2>
        <p>You bring the evidence — the facts and the named quotes. OFFSIDE retrieves the
        matching Law itself, has Granite read each lens, lets Granite Guardian audit each,
        and fills THE SPLIT live.</p>
      </header>

      {healthy === false && (
        <div className="studio__banner" role="note">
          Live decomposition runs the real Granite models on <strong>your machine</strong> —
          not on this $0 static host. Start it locally in one command (see the README
          “Run the Studio yourself”), then this form goes live. Meanwhile, “Load an example”
          shows a complete real result.
        </div>
      )}

      <StudioForm disabled={running || healthy === false} onRun={run} />
      {error && <p className="studio__error">{error}</p>}
      {(events.length > 0 || bundle) && <LiveSplit events={events} bundle={bundle} />}
    </section>
  );
}
```

- [ ] **Step 5: Typecheck + build**

Run: `cd web && npm run typecheck && npm run build`
Expected: PASS. (`SettledFact`/`SplitView`/`LensPanels`/`ProvenanceFooter` prop names must match their real signatures — verify each import against the component file; fix prop names if the build complains.)

- [ ] **Step 6: Commit**

```bash
git add web/lib/studioClient.ts web/components/studio/
git commit -m "feat(web): Studio form + live box-fill, reusing the Explore renderer"
```

---

### Task 7: Pre-baked example fixture + no-backend fallback

**Files:**
- Create: `web/fixtures/studio-example.json` (real baked Studio bundle)
- Modify: `web/components/studio/StudioPanel.tsx` (load the example when backend is down and the user clicks “Load an example” → render it via `LiveSplit` directly)
- Modify: `web/lib/studioClient.ts` (add `loadExampleBundle(): Promise<IncidentBundle>` reading the static fixture)

**Interfaces:**
- Produces: a committed real Studio bundle so the public site shows a complete end-to-end result with no backend.

- [ ] **Step 1: Bake the example for real (requires Ollama up locally)**

Start the backend and POST the EXAMPLE payload, capturing the final `done` bundle. With Ollama running:

```bash
cd engine && uv run uvicorn offside_engine.serve.app:app --port 8000 &
curl -s -X POST localhost:8000/decompose -H 'Content-Type: application/json' \
  -d '{"title":"A disputed penalty","settled_statement":"A defender'\''s arm blocked the ball inside the box. The arm-to-ball contact is agreed by both sides.","historical_note":"VAR reviewed the incident on a clear, side-on replay; the contact was fully visible and reviewable in real time.","quotes":[{"speaker":"Home manager","source":"post-match interview","text":"That'\''s a clear penalty — the arm was out, away from the body."},{"speaker":"Away manager","source":"post-match interview","text":"Never a penalty — it'\''s ball to hand, the arm didn'\''t move."}],"tactical_note":null}' \
  | grep '"type": "done"' | head -1
```

Extract the `bundle` object from that `done` event and write it to `web/fixtures/studio-example.json` (pretty-printed, LF). Confirm it validates: `cd web && node -e "JSON.parse(require('fs').readFileSync('fixtures/studio-example.json'))"`.

- [ ] **Step 2: Add `loadExampleBundle` to `studioClient.ts`**

```ts
export async function loadExampleBundle(): Promise<IncidentBundle> {
  const r = await fetch("/fixtures/studio-example.json", { cache: "force-cache" });
  return (await r.json()) as IncidentBundle;
}
```

> If `web/fixtures/` is not served statically at `/fixtures/...`, import the JSON directly instead: `import example from "@/fixtures/studio-example.json"` and return it typed. Verify which works under Next 16 static export and use that.

- [ ] **Step 3: Wire the example into `StudioPanel`**

When `healthy === false` and the user clicks “Load an example”, call `loadExampleBundle()` and set it as `bundle` so `LiveSplit` renders the complete real result (no streaming needed). When `healthy` is true, “Load an example” pre-fills the form (Task 6 behavior) so they can run it live.

- [ ] **Step 4: Typecheck + build + commit**

```bash
cd web && npm run typecheck && npm run build
git add web/fixtures/studio-example.json web/components/studio/StudioPanel.tsx web/lib/studioClient.ts
git commit -m "feat(web): pre-baked Studio example so the public site shows a real result with no backend"
```

---

### Task 8: Self-host — compose + README, and integrity test for thin input

**Files:**
- Create: `docker-compose.studio.yml`
- Create: `Makefile` target `studio` (or extend an existing Makefile)
- Modify: `README.md` (add a “Run the Studio yourself” section)
- Test: `engine/tests/test_studio_integrity.py`

**Interfaces:**
- Produces: a one-command self-host path and a test proving thin user evidence yields `Not documented`, never fabrication.

- [ ] **Step 1: Write the integrity test (thin input → honest empties, mocked bake boundary)**

```python
# engine/tests/test_studio_integrity.py
from offside_engine.serve.form_models import FormPayload
from offside_engine.serve.incident_from_form import build_studio_incident


def test_no_quotes_means_no_framing_atom_so_cultural_cannot_fire():
    # The honest property: with no quotes there is no framing evidence, so the Framing lens
    # has nothing to surface and Cultural bias cannot be PRESENT. The engine cannot invent it.
    p = FormPayload(title="t", settled_statement="s", historical_note="h", quotes=[], tactical_note=None)
    _spec, pool = build_studio_incident(p)
    assert not [c for c in pool.values() if c.doc_kind == "FRAMING_SOURCE"]


def test_user_atoms_are_all_in_the_allow_list():
    # No user atom can leak unscoped; every id we created is explicitly allowed, nothing else.
    p = FormPayload(
        title="t", settled_statement="s", historical_note="h",
        quotes=[{"speaker": "a", "source": "s", "text": "x"}], tactical_note="data",
    )
    spec, pool = build_studio_incident(p)
    user_atoms = {cid for cid, c in pool.items() if c.source_doc == "studio-user-input"}
    assert user_atoms <= spec.allowed_citation_ids
```

- [ ] **Step 2: Run to verify pass** (these exercise Task 2 code, should pass immediately — they lock the integrity property)

Run: `cd engine && uv run pytest tests/test_studio_integrity.py -v`
Expected: 2 PASS.

- [ ] **Step 3: Write `docker-compose.studio.yml`**

```yaml
# One command to run the OFFSIDE Studio backend with the real IBM models locally.
# Usage: docker compose -f docker-compose.studio.yml up
services:
  ollama:
    image: ollama/ollama:latest
    ports: ["11434:11434"]
    volumes: ["ollama:/root/.ollama"]
  studio:
    build: { context: ./engine, dockerfile: Dockerfile.studio }
    command: >
      sh -c "ollama pull granite3.3:8b && ollama pull granite-embedding:30m &&
             ollama pull granite3-guardian:2b &&
             uv run uvicorn offside_engine.serve.app:app --host 0.0.0.0 --port 8000"
    environment: { OLLAMA_HOST: "ollama:11434" }
    ports: ["8000:8000"]
    depends_on: ["ollama"]
volumes: { ollama: {} }
```

Create `engine/Dockerfile.studio` (python:3.12-slim + uv + `uv sync --extra serve`). Keep it minimal; the goal is reproducibility, not a production image.

- [ ] **Step 4: Add the README section**

In `README.md`, add under “Running it”:

```markdown
### Run the Studio yourself (live decomposition of your own incident)

The deployed site is $0 static — live runs the real Granite models on *your* machine.

```bash
docker compose -f docker-compose.studio.yml up   # starts Ollama, pulls the 3 IBM models, serves :8000
cd web && NEXT_PUBLIC_STUDIO_BASE=http://localhost:8000 npm run dev   # the Studio tab goes live
```

Open the Studio tab, paste a controversy's facts and two named quotes, and watch the four
SPLIT boxes fill in as Granite reads each lens and Granite Guardian audits it — live.
```

- [ ] **Step 5: Commit**

```bash
git add docker-compose.studio.yml engine/Dockerfile.studio Makefile README.md engine/tests/test_studio_integrity.py
git commit -m "feat: one-command self-host for the Studio backend + thin-input integrity test"
```

---

### Task 9: Full green sweep + demo polish

**Files:** none new — verification + any fixups surfaced.

- [ ] **Step 1: Full engine suite**

Run: `cd engine && uv run ruff check . && uv run pytest -q`
Expected: ruff clean; all tests pass (the existing 145 + the new serve/form tests).

- [ ] **Step 2: Contract sync**

Run: `cd engine && uv run python -m offside_engine.export_types && cd .. && git diff --exit-code web/types/contract.ts`
Expected: no diff (committed contract matches generator).

- [ ] **Step 3: Web typecheck + build**

Run: `cd web && npm run typecheck && npm run build`
Expected: PASS, static pages generated.

- [ ] **Step 4: Manual live smoke (Ollama up)**

Start backend + `npm run dev`, open Studio, click “Load an example”, run live, confirm: four boxes fill one at a time, the final result renders via the Explore components, the provenance footer reads `live · user-supplied evidence`, no numbers anywhere, every Guardian seal is a real verdict.

- [ ] **Step 5: Commit any fixups + push**

```bash
git add -A
git commit -m "chore: green sweep — studio suite, contract sync, web build"
git push origin main
```

- [ ] **Step 6: Confirm CI green**

Run: `gh run watch $(gh run list --branch main --limit 1 --json databaseId -q '.[0].databaseId') --exit-status`
Expected: both jobs (Engine, Web) success.

---

## Self-Review

**Spec coverage:**
- Tabs revamp → Task 1. ✓
- Studio form (4 blocks, ≥2 opposed quotes, source labels, "Load example") → Task 6 + form_models validation in Task 2. ✓
- Engine retrieves the Law itself → Task 2 reuses `build_curated_citations()` into the pool; Referee allow-list includes all law atoms. ✓
- Real pipeline, unchanged bake → Task 3 calls `bake_incident` verbatim. ✓
- SSE streaming, boxes fill live → Tasks 4 (backend) + 6 (`LiveSplit`). ✓
- Honest provenance (`live-user`, no byte-repro claim) → Task 5. ✓
- No-fabrication on thin input → Tasks 2 + 8 integrity tests. ✓
- Public-site fallback (example fixture, banner, disabled submit) → Tasks 6 + 7. ✓
- Self-hostable, one command → Task 8. ✓
- Contract stays in sync → Task 5 + Task 9 Step 2. ✓
- CI green → Task 9. ✓

**Placeholder scan:** every code step shows complete code; no TBD/TODO; tests carry real assertions. Two explicit "verify which works" notes (Task 1 test runner, Task 7 static-fixture import) are genuine environment forks with both branches specified, not placeholders.

**Type consistency:** `FormPayload`/`Quote` defined in Task 2, consumed unchanged in Tasks 3/4/8. `build_studio_incident -> (IncidentSpec, dict[str,Citation])` consumed in Task 3. `StudioStreamEvent` defined in Task 5, consumed in Task 6. `decompose`/`stream_decompose` names consistent across Tasks 3/4. `BakeProvenance.mode` added in Task 5, read by `ProvenanceFooter` (existing) — note: Task 5 should also make `ProvenanceFooter` show the live-user line; that is a one-line display change folded into Task 6's reuse (the footer already branches on `isDeterministic`; extend it to read `provenance.mode === "live-user"`).

## Risk notes for the implementer
- The bake is currently synchronous; `stream_decompose` narrates a real-but-already-complete computation. That is honest (every state is real) and the simplest correct v1. Only split out mid-computation streaming if a reviewer demands true incremental timing.
- `TestClient` may buffer SSE; if Task 4 Step 6 can't assert on streamed text, assert the mocked generator was consumed + status 200.
- Verify each reused web component's exact prop names before wiring (Task 6 Step 5) — the plan assumes `SettledFact({fact,title,incidentId})`, `SplitView({bundle})`, `LensPanels({lenses,citations})`, `ProvenanceFooter({provenance,citations})` from the current source; correct if drifted.
