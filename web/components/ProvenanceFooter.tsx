import type { BakeProvenance, Citation } from "@/types/contract";

// The provenance footer makes the reproducibility claim concrete: which IBM models
// produced this bundle, and the exact corpus commit it was baked from. A reviewer can
// re-run the bake at that SHA and get a byte-identical fixture. Any StatsBomb-sourced
// citation also carries its required attribution here.

interface ProvenanceFooterProps {
  provenance: BakeProvenance;
  citations: Record<string, Citation>;
}

export function ProvenanceFooter({ provenance, citations }: ProvenanceFooterProps) {
  const statsbombAttribution = Object.values(citations).find(
    (c) => c.doc_kind === "STATSBOMB_EVENT" && c.attribution,
  )?.attribution;

  const shaShort =
    provenance.corpus_git_sha && provenance.corpus_git_sha.length >= 7
      ? provenance.corpus_git_sha.slice(0, 7)
      : provenance.corpus_git_sha;

  // Be honest about what produced THESE bytes. An offline/deterministic bake never ran
  // Granite or Guardian, so it must not advertise model ids it didn't execute — it names
  // the deterministic router and the still-real embedding index. A live bake names the
  // actual IBM models. The footer reads the same source of truth the seals do.
  const isDeterministic =
    provenance.guardian_model === "deterministic-router" ||
    provenance.granite_model === "deterministic-router";

  return (
    <footer className="provenance">
      <div className="provenance__row">
        <span className="provenance__label">Produced by</span>
        <span className="provenance__models">
          {isDeterministic ? (
            <>
              deterministic evidence router · {provenance.embed_model} (IBM Granite
              Embedding) · grounded against the committed IFAB / StatsBomb corpus
            </>
          ) : (
            <>
              {provenance.granite_model} · {provenance.embed_model} ·{" "}
              {provenance.guardian_model}
            </>
          )}
        </span>
      </div>
      {isDeterministic && (
        <p className="provenance__honesty">
          This fixture was routed deterministically from the committed corpus. The live
          four-model pipeline (Granite reads each lens, Granite Guardian audits each) runs
          via <code>analyze_live.py</code> and is shown in the demo.
        </p>
      )}
      {shaShort && (
        <div className="provenance__row">
          <span className="provenance__label">Corpus</span>
          <span className="provenance__sha">{shaShort}</span>
          <span className="provenance__note">
            deterministic bake — re-running at this commit reproduces this fixture
            byte-for-byte
          </span>
        </div>
      )}
      {statsbombAttribution && (
        <p className="provenance__attribution">{statsbombAttribution}</p>
      )}
    </footer>
  );
}
