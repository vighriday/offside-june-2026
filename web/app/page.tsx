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
