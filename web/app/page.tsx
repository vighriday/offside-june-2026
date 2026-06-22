import { loadIncident } from "@/lib/fixtures";
import { SettledFact } from "@/components/SettledFact";
import { SplitView } from "@/components/SplitView";
import { LensPanels } from "@/components/LensPanels";
import { ProvenanceFooter } from "@/components/ProvenanceFooter";

// The root routes straight to the golden incident; incident selection lands in M8. For
// the core artifact, the Hand of God is the front door.
export default async function Home() {
  const { bundle, isSample } = await loadIncident("hand-of-god-1986");

  return (
    <main className="incident">
      {isSample && (
        <p className="incident__sample-banner">
          Pre-bake sample fixture — the audited bundle replaces this once the bake runs.
        </p>
      )}

      <div className="incident__inner">
        <SettledFact fact={bundle.settled_fact} title={bundle.title} />
        <SplitView bundle={bundle} />
        <LensPanels lenses={bundle.lenses} />
        <ProvenanceFooter
          provenance={bundle.provenance}
          citations={bundle.citations}
        />
      </div>
    </main>
  );
}
