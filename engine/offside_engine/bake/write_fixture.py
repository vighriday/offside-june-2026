"""Freeze an IncidentBundle to a deterministic JSON fixture the web reads.

The web app is a pure reader of these files — no model, no Python at runtime. This
writer serializes a bundle with **sorted keys and a stable indent**, so re-running the
bake on the same inputs produces a byte-identical file: a reviewer can diff two bakes
and see nothing changed. The filename is the incident id, so the web resolves a fixture
from a route slug with no manifest lookup.
"""

from __future__ import annotations

import json
from pathlib import Path

from offside_engine.analyze.split_schema import IncidentBundle


def bundle_to_json(bundle: IncidentBundle) -> str:
    """Serialize a bundle to deterministic JSON (sorted keys, trailing newline).

    Pydantic emits in field-definition order; ``sort_keys`` then imposes a canonical
    order independent of how the model happens to be defined, so the bytes depend only
    on the data. The trailing newline keeps the file POSIX-clean and diff-friendly.
    """
    payload = bundle.model_dump(mode="json")
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def write_fixture(bundle: IncidentBundle, fixtures_dir: Path) -> Path:
    """Write ``<incident_id>.json`` into ``fixtures_dir`` and return its path.

    The bundle is re-validated on the way in (constructing it already ran its
    validators; this is the contract that only a valid bundle is ever frozen).
    """
    IncidentBundle.model_validate(bundle.model_dump())  # belt-and-braces revalidation
    fixtures_dir.mkdir(parents=True, exist_ok=True)
    out = fixtures_dir / f"{bundle.incident_id}.json"
    out.write_text(bundle_to_json(bundle), encoding="utf-8")
    return out
