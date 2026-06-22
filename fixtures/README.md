# Fixtures

The baked incident fixtures live in [`../web/fixtures/`](../web/fixtures/), inside the
web deploy root, so the app reads them at build time and Vercel bundles them with no
cross-directory path. Each is a frozen, audited `IncidentBundle` named by incident id
(e.g. `hand-of-god-1986.json`), produced by the bake (`engine/bake.ipynb`) and read
verbatim by the web app — no model or Python runs at web runtime.

A fixture is deterministic: re-running the bake on the same corpus yields byte-identical
bytes (sorted keys, temperature 0, fixed seed). Each carries its own provenance — the
models used and the corpus git SHA — so any bundle traces back to its exact sources and
reproduces.

This directory is kept as the canonical pointer; the files themselves are under
`web/fixtures/`.
