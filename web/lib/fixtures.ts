import { promises as fs } from "node:fs";
import path from "node:path";
import { CANONICAL_AXIS_ORDER, type IncidentBundle } from "@/types/contract";

// Fixtures live at the repo root `fixtures/` once baked; until the Colab bake runs, a
// schema-valid sample sits next to the web app. The loader prefers the real bake and
// falls back to the sample so the UI is buildable before the bake — clearly flagged.
const REPO_FIXTURES = path.join(process.cwd(), "..", "fixtures");
const SAMPLE_FIXTURES = path.join(process.cwd(), "fixtures");

async function readFirst(candidates: string[]): Promise<string | null> {
  for (const file of candidates) {
    try {
      return await fs.readFile(file, "utf-8");
    } catch {
      // try the next candidate
    }
  }
  return null;
}

/** Whether the loaded bundle came from a real bake or the pre-bake sample. */
export interface LoadedIncident {
  bundle: IncidentBundle;
  isSample: boolean;
}

/**
 * Load one incident bundle by id, preferring the baked fixture over the sample.
 *
 * The bundle is validated structurally at this boundary — the four axes must be present
 * in canonical order — so a malformed fixture fails the build loudly rather than render
 * a broken SPLIT. (The engine already guarantees this on write; this is defence in depth
 * for the sample and any hand-edited file.)
 */
export async function loadIncident(incidentId: string): Promise<LoadedIncident> {
  const baked = path.join(REPO_FIXTURES, `${incidentId}.json`);
  const sample = path.join(SAMPLE_FIXTURES, `${incidentId}.sample.json`);

  const realRaw = await readFirst([baked]);
  const raw = realRaw ?? (await readFirst([sample]));
  if (raw === null) {
    throw new Error(
      `No fixture for incident "${incidentId}" (looked for ${baked} and ${sample})`,
    );
  }

  const bundle = JSON.parse(raw) as IncidentBundle;
  assertWellFormed(bundle, incidentId);
  return { bundle, isSample: realRaw === null };
}

function assertWellFormed(bundle: IncidentBundle, incidentId: string): void {
  if (bundle.incident_id !== incidentId) {
    throw new Error(
      `Fixture incident_id "${bundle.incident_id}" does not match requested "${incidentId}"`,
    );
  }
  const axes = bundle.split.cells.map((c) => c.axis);
  const expected = CANONICAL_AXIS_ORDER;
  const ordered =
    axes.length === expected.length && axes.every((a, i) => a === expected[i]);
  if (!ordered) {
    throw new Error(
      `Fixture "${incidentId}" SPLIT cells are not the four axes in canonical order: ${axes.join(", ")}`,
    );
  }
  // every cited id must resolve in the citation map (click-to-source must never dangle)
  const cited = new Set<string>();
  bundle.settled_fact.citation_ids.forEach((id) => cited.add(id));
  bundle.lenses.forEach((l) => l.output.citation_ids.forEach((id) => cited.add(id)));
  bundle.split.cells.forEach((c) => c.citation_ids.forEach((id) => cited.add(id)));
  for (const id of cited) {
    if (!(id in bundle.citations)) {
      throw new Error(`Fixture "${incidentId}" cites id "${id}" with no citation`);
    }
  }
}
