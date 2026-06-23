import { loadIncident } from "@/lib/fixtures";
import { IncidentExplorer, type LoadedBundle } from "@/components/IncidentExplorer";

// The incidents OFFSIDE ships, in demo order. One iconic hook the room recognises in two
// seconds (the Hand of God), then a hard pivot into three CURRENT, unsettled disputes from
// the present Laws and season — the modern handball rewrite, the millimetre offside line,
// and the 'subjective' VAR call — which is where OFFSIDE earns the claim of a rule-maker's
// instrument rather than a quiz. The two remaining archive incidents close the set as the
// generalization contrast. Each incident lights up a different axis; across the set all
// four fire. Any incident whose fixture is not present is skipped.
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

  return <IncidentExplorer incidents={loaded} />;
}
