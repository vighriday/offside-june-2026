"use client";

import { useState } from "react";
import { Hero } from "./Hero";
import { HowItWorks } from "./HowItWorks";
import { IncidentExplorer, type LoadedBundle } from "./IncidentExplorer";
import { StudioPanel } from "./studio/StudioPanel";

type Tab = "explore" | "studio" | "how";

const TABS: { id: Tab; label: string }[] = [
  { id: "explore", label: "Explore" },
  { id: "studio", label: "Studio" },
  { id: "how", label: "How it works" },
];

// The masthead + Buenos Aires/London hook are the identity — pinned above the tabs, always
// visible. Below them, exactly one surface shows at a time: see it work (Explore), do it
// yourself (Studio), understand it (How it works). This is the fix for the single-scroll
// complexity: one idea per surface instead of everything stacked.
export function TabShell({ incidents }: { incidents: LoadedBundle[] }) {
  const [tab, setTab] = useState<Tab>("explore");
  return (
    <main className="shell">
      <Hero />
      <nav className="shell__tabs" role="tablist" aria-label="OFFSIDE sections">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            role="tab"
            aria-selected={tab === t.id}
            className="shell__tab"
            data-active={tab === t.id}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>
      <div className="shell__panel" role="tabpanel">
        {tab === "explore" && <IncidentExplorer incidents={incidents} />}
        {tab === "studio" && <StudioPanel />}
        {tab === "how" && <HowItWorks />}
      </div>
    </main>
  );
}
