import { loadIncident } from "@/lib/fixtures";
import { IncidentExplorer, type LoadedBundle } from "@/components/IncidentExplorer";

// The incidents OFFSIDE ships, in demo order: the Hand of God hero first, then Lampard's
// ghost goal as the contrast that proves the diagnostic generalizes. Any incident whose
// fixture is not present is skipped, so the app renders whatever has been baked.
const INCIDENT_IDS = ["hand-of-god-1986", "lampard-ghost-goal-2010"];

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
