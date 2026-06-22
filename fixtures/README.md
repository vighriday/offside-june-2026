# Fixtures

Frozen, audited `IncidentBundle` JSON — one file per incident, named by incident id
(e.g. `hand-of-god-1986.json`). Each is produced by the bake (`engine/bake.ipynb`),
which runs the IBM Granite stack at build time, and read verbatim by the web app at
runtime. No model or Python runs at web runtime.

A fixture is deterministic: re-running the bake on the same corpus yields byte-identical
bytes (sorted keys, temperature 0, fixed seed), so two bakes diff to nothing. Each
fixture carries its own provenance — the models used and the corpus git SHA it was baked
from — so any bundle can be traced back to the exact sources and reproduced.
