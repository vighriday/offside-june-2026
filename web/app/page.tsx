import { loadIncident } from "@/lib/fixtures";

// The root currently routes straight to the golden incident. Incident selection lands
// in M8; for the core artifact, the Hand of God is the front door.
export default async function Home() {
  const { bundle, isSample } = await loadIncident("hand-of-god-1986");
  return (
    <main style={{ padding: "2rem", maxWidth: "72rem", margin: "0 auto" }}>
      <p style={{ letterSpacing: "0.16em", textTransform: "uppercase", fontSize: "0.75rem", color: "var(--cds-text-secondary)" }}>
        OFFSIDE — The Football Disagreement Engine
      </p>
      <h1 style={{ fontWeight: 300, fontSize: "2.5rem", marginTop: "0.5rem" }}>{bundle.title}</h1>
      <p style={{ color: "var(--cds-text-secondary)", marginTop: "1rem", maxWidth: "44rem" }}>
        {bundle.settled_fact.statement}
      </p>
      {isSample && (
        <p style={{ marginTop: "1rem", fontSize: "0.75rem", color: "var(--split-weak)" }}>
          Showing the pre-bake sample fixture. The real bundle replaces this once the Colab bake runs.
        </p>
      )}
    </main>
  );
}
