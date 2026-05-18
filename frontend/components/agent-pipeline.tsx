"use client";

import { cn } from "@/lib/utils";
import { CheckCircle2, Circle, Clock, Zap } from "lucide-react";

const PHASES = [
  { id: 1, label: "Requirements", sub: "Ingest & Parse" },
  { id: 2, label: "User Stories", sub: "Generate & Review" },
  { id: 3, label: "Test Cases", sub: "Generate & Review" },
  { id: 4, label: "Code Delivered", sub: "Checkpoint" },
  { id: 5, label: "AI Execution", sub: "Run Tests" },
  { id: 6, label: "Bug Analysis", sub: "Root Cause" },
  { id: 7, label: "Sign-off", sub: "Human Validation" },
  { id: 8, label: "Automation", sub: "Generate Scripts" },
];

interface Props {
  projectId?: string | null;
  currentPhase?: number;
}

export function AgentPipeline({ projectId, currentPhase = 1 }: Props) {
  return (
    <div className="rounded-xl border border-border bg-card p-6">
      <div className="flex items-center gap-2 mb-5">
        <Zap className="w-4 h-4 text-primary" />
        <h2 className="font-semibold text-sm">SDLC Pipeline</h2>
        {!projectId && <span className="text-xs text-muted-foreground ml-auto">Select a project to start</span>}
      </div>
      <div className="flex items-start gap-0 overflow-x-auto pb-2">
        {PHASES.map((phase, i) => {
          const done = phase.id < currentPhase;
          const active = phase.id === currentPhase;
          return (
            <div key={phase.id} className="flex items-start flex-shrink-0">
              <div className="flex flex-col items-center gap-1.5 w-24">
                <div className={cn(
                  "w-8 h-8 rounded-full flex items-center justify-center border-2 transition-colors",
                  done ? "bg-green-900/50 border-green-600" :
                  active ? "bg-primary/20 border-primary animate-pulse" :
                  "bg-secondary border-border"
                )}>
                  {done ? (
                    <CheckCircle2 className="w-4 h-4 text-green-400" />
                  ) : active ? (
                    <Zap className="w-3.5 h-3.5 text-primary" />
                  ) : (
                    <span className="text-xs text-muted-foreground">{phase.id}</span>
                  )}
                </div>
                <p className={cn("text-xs font-medium text-center", active ? "text-primary" : done ? "text-green-400" : "text-muted-foreground")}>
                  {phase.label}
                </p>
                <p className="text-[10px] text-muted-foreground text-center leading-tight">{phase.sub}</p>
              </div>
              {i < PHASES.length - 1 && (
                <div className={cn(
                  "h-0.5 w-4 mt-4 flex-shrink-0 transition-colors",
                  done ? "bg-green-600" : "bg-border"
                )} />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
