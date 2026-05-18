"use client";

import { useStore } from "@/lib/store";
import { cn } from "@/lib/utils";
import { Cpu } from "lucide-react";

export function AgentStatusBar() {
  const { agentStatuses } = useStore();
  const running = agentStatuses.filter((s) => s.status === "running");

  if (running.length === 0) return null;

  return (
    <div className="flex items-center gap-2 text-xs">
      <Cpu className="w-3 h-3 text-primary animate-pulse" />
      <span className="text-muted-foreground">Agent:</span>
      {running.map((s) => (
        <span key={s.agent} className="flex items-center gap-1.5 bg-primary/10 text-primary px-2 py-0.5 rounded-full">
          <span className="flex gap-0.5">
            <span className="streaming-dot w-1 h-1 rounded-full bg-primary" />
            <span className="streaming-dot w-1 h-1 rounded-full bg-primary" />
            <span className="streaming-dot w-1 h-1 rounded-full bg-primary" />
          </span>
          {s.agent.replace("_agent", "").replace("_", " ")}
          {s.message && <span className="text-muted-foreground truncate max-w-40">— {s.message}</span>}
        </span>
      ))}
    </div>
  );
}
