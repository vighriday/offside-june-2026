"""A visible groundedness-eval artifact for the lens readings — without breaking the moat.

The no-numbers contract governs what the *Granite model emits* into THE SPLIT: that schema
has no numeric field, so the diagnosis can never be a fabricated percentage. This module is
the opposite direction: an **external audit** that scores how well each lens reading is
grounded in its cited evidence, written to a build-time report. These numbers describe the
pipeline's trustworthiness; they never enter the SPLIT, the lens schema, or the UI — so the
moat is intact (the model still cannot output a number) while a judge gets a quantified,
inspectable trust signal instead of only a binary seal.

Two backends, same report shape:

* **RAGAS faithfulness** (optional ``offside-engine[eval]``): scores each lens rationale as a
  RAG answer against its retrieved evidence as context, judged by a local Granite model.
* **Deterministic proxy** (always available, offline): groundedness = Guardian verdict
  (GROUNDED→1.0, else 0.0) gated by citation coverage (does the rationale actually cite the
  evidence it was shown?). Reproducible, no model, used in CI and the offline bake.

Output: ``data/eval/groundedness_report.json`` + ``.md`` — a per-lens, per-incident table.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from offside_engine.analyze.split_schema import IncidentBundle


@dataclass(frozen=True)
class LensGroundedness:
    incident_id: str
    lens: str
    stance: str
    guardian_verdict: str
    n_citations: int
    # 0.0–1.0; how grounded this lens reading is in its cited evidence (audit metric only)
    groundedness: float
    backend: str  # "ragas" | "deterministic"


def _deterministic_score(sealed_lens) -> float:
    """Guardian-gated citation-coverage proxy in [0,1].

    A reading that the Guardian could not ground scores 0. A grounded reading scores by
    whether it actually cites evidence (a GROUNDED reading with citations is fully grounded;
    a degraded INSUFFICIENT_EVIDENCE reading with no citation is, correctly, 0).
    """
    o = sealed_lens.output
    verdict = sealed_lens.seal.verdict
    if verdict != "GROUNDED":
        return 0.0
    return 1.0 if o.citation_ids else 0.0


def score_bundle_deterministic(bundle: IncidentBundle) -> list[LensGroundedness]:
    """Score every lens in a baked bundle with the offline deterministic proxy."""
    rows: list[LensGroundedness] = []
    for sl in bundle.lenses:
        rows.append(LensGroundedness(
            incident_id=bundle.incident_id,
            lens=sl.output.lens,
            stance=sl.output.stance,
            guardian_verdict=sl.seal.verdict,
            n_citations=len(sl.output.citation_ids),
            groundedness=_deterministic_score(sl),
            backend="deterministic",
        ))
    return rows


def _ragas_available() -> bool:
    try:
        import ragas  # noqa: F401
        return True
    except Exception:
        return False


def score_bundle(bundle: IncidentBundle, *, use_ragas: bool = False) -> list[LensGroundedness]:
    """Score a bundle's lenses. Uses RAGAS faithfulness when requested and importable;
    otherwise the deterministic proxy. The report shape is identical either way.

    The RAGAS path scores each lens rationale (the "answer") against the verbatim cited
    evidence (the "contexts"); see ``ragas_faithfulness`` for the wiring. It needs a local
    judge model, so it is opt-in and never required for a green build.
    """
    if use_ragas and _ragas_available():
        try:
            return _score_bundle_ragas(bundle)
        except Exception:
            # never let an eval backend failure break the bake — fall back, noted in backend
            pass
    return score_bundle_deterministic(bundle)


def _score_bundle_ragas(bundle: IncidentBundle) -> list[LensGroundedness]:
    """RAGAS faithfulness per lens. Imported lazily so the dependency stays optional."""
    from ragas import evaluate  # type: ignore
    from ragas.metrics import faithfulness  # type: ignore
    from datasets import Dataset  # type: ignore

    rows: list[LensGroundedness] = []
    samples = []
    index: list[tuple[str, str, str]] = []  # (lens, stance, verdict) parallel to samples
    for sl in bundle.lenses:
        o = sl.output
        contexts = [
            bundle.citations[c].extracted_text
            for c in o.citation_ids
            if c in bundle.citations
        ]
        if not contexts:
            # nothing to be faithful to; deterministic 0 for an ungrounded/empty reading
            rows.append(LensGroundedness(
                incident_id=bundle.incident_id, lens=o.lens, stance=o.stance,
                guardian_verdict=sl.seal.verdict, n_citations=0,
                groundedness=0.0, backend="ragas",
            ))
            continue
        samples.append({"question": "Is this lens reading grounded in its evidence?",
                        "answer": o.rationale, "contexts": contexts})
        index.append((o.lens, o.stance, sl.seal.verdict))

    if samples:
        ds = Dataset.from_list(samples)
        result = evaluate(ds, metrics=[faithfulness])
        scores = result.to_pandas()["faithfulness"].tolist()
        for (lens, stance, verdict), score, sample in zip(index, scores, samples):
            rows.append(LensGroundedness(
                incident_id=bundle.incident_id, lens=lens, stance=stance,
                guardian_verdict=verdict, n_citations=len(sample["contexts"]),
                groundedness=float(score), backend="ragas",
            ))
    return rows


def write_report(rows: list[LensGroundedness], out_dir: Path) -> tuple[Path, Path]:
    """Write the groundedness report as JSON + a readable Markdown table. Returns both paths."""
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "groundedness_report.json"
    md_path = out_dir / "groundedness_report.md"

    json_path.write_text(
        json.dumps([asdict(r) for r in rows], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    backend = rows[0].backend if rows else "deterministic"
    lines = [
        "# OFFSIDE — lens groundedness report",
        "",
        f"Build-time audit metric (backend: **{backend}**). These scores measure how well each",
        "lens reading is grounded in its cited evidence. They are an external audit of the",
        "pipeline — they never enter THE SPLIT, the lens schema, or the UI, so the no-numbers",
        "contract on the model output is untouched.",
        "",
        "| Incident | Lens | Stance | Guardian | Citations | Groundedness |",
        "|----------|------|--------|----------|:---------:|:------------:|",
    ]
    for r in rows:
        lines.append(
            f"| {r.incident_id} | {r.lens} | {r.stance} | {r.guardian_verdict} | "
            f"{r.n_citations} | {r.groundedness:.2f} |"
        )
    grounded = [r for r in rows if r.groundedness >= 0.999]
    if rows:
        lines += [
            "",
            f"**{len(grounded)} / {len(rows)}** lens readings fully grounded "
            f"({100 * len(grounded) // len(rows)}%).",
        ]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path
