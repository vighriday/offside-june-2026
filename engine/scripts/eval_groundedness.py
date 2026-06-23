"""Generate the lens groundedness report from the baked fixtures.

  python scripts/eval_groundedness.py            # deterministic proxy (offline, default)
  python scripts/eval_groundedness.py --ragas     # RAGAS faithfulness (needs [eval] + a judge)

Writes data/eval/groundedness_report.{json,md}. The numbers are a build-time audit of how
grounded each lens reading is — they never touch THE SPLIT or the UI (the moat is intact).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from offside_engine.analyze.split_schema import IncidentBundle
from offside_engine.eval.groundedness import score_bundle, write_report

_REPO = Path(__file__).resolve().parents[2]
_FIXTURES = _REPO / "web" / "fixtures"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ragas", action="store_true", help="use RAGAS faithfulness if installed")
    args = ap.parse_args()

    rows = []
    seen: set[str] = set()
    for path in sorted(_FIXTURES.glob("*.json")):
        iid = path.name.replace(".sample.json", "").replace(".json", "")
        if iid in seen:
            continue
        seen.add(iid)
        bundle = IncidentBundle.model_validate_json(path.read_text(encoding="utf-8"))
        rows.extend(score_bundle(bundle, use_ragas=args.ragas))

    out = _REPO / "engine" / "data" / "eval"
    jp, mp = write_report(rows, out)
    grounded = sum(1 for r in rows if r.groundedness >= 0.999)
    print(f"scored {len(rows)} lens readings across {len(seen)} incidents")
    print(f"fully grounded: {grounded}/{len(rows)}")
    print(f"wrote {jp}\nwrote {mp}")


if __name__ == "__main__":
    main()
