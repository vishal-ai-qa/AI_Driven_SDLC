"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useStore } from "@/lib/store";
import { bugsApi } from "@/lib/api";
import { StatusBadge } from "@/components/ui/status-badge";
import { toast } from "sonner";
import { Bug, ChevronDown, ChevronRight, Lightbulb } from "lucide-react";
import { formatDate } from "@/lib/utils";

export default function BugsPage() {
  const { activeProjectId } = useStore();
  const qc = useQueryClient();
  const [expanded, setExpanded] = useState<string | null>(null);
  const [severityFilter, setSeverityFilter] = useState("all");

  const { data: bugs = [], isLoading } = useQuery({
    queryKey: ["bugs", activeProjectId, severityFilter],
    queryFn: () => bugsApi.list(
      activeProjectId
        ? { ...(severityFilter !== "all" && { severity: severityFilter }) }
        : {}
    ),
    enabled: !!activeProjectId,
    refetchInterval: 10000,
  });

  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) => bugsApi.updateStatus(id, status),
    onSuccess: () => {
      toast.success("Bug status updated");
      qc.invalidateQueries({ queryKey: ["bugs"] });
    },
  });

  const severities = ["all", "critical", "high", "medium", "low"];

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">Bug Reports</h1>
          <p className="text-sm text-muted-foreground">Phase 6 — AI-analyzed defects with root cause & fix suggestions</p>
        </div>
        <div className="flex gap-1">
          {severities.map((s) => (
            <button
              key={s}
              onClick={() => setSeverityFilter(s)}
              className={`px-3 py-1.5 text-xs rounded-lg transition-colors capitalize ${
                severityFilter === s ? "bg-primary text-primary-foreground" : "bg-secondary text-muted-foreground hover:text-foreground"
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-40 text-muted-foreground text-sm">Loading...</div>
      ) : bugs.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border p-12 text-center">
          <Bug className="w-10 h-10 mx-auto mb-3 text-muted-foreground/40" />
          <p className="text-muted-foreground">No bugs found. Run tests to discover issues.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {(bugs as Array<{
            id: string; bug_id: string; title: string; severity: string; priority: string;
            status: string; environment?: string; description: string; expected_result: string;
            actual_result: string; root_cause?: string; suggested_fix?: string;
            steps_to_reproduce: string[]; is_flaky: boolean; is_environment_issue: boolean;
            console_logs?: Array<{ type: string; text: string }>;
            screenshots?: string[]; created_at: string;
          }>).map((bug) => {
            const isOpen = expanded === bug.id;
            return (
              <div key={bug.id} className="rounded-xl border border-border bg-card overflow-hidden">
                {/* Bug header */}
                <div
                  className="flex items-center gap-3 p-4 cursor-pointer hover:bg-secondary/30 transition-colors"
                  onClick={() => setExpanded(isOpen ? null : bug.id)}
                >
                  {isOpen ? <ChevronDown className="w-4 h-4 text-muted-foreground flex-shrink-0" /> : <ChevronRight className="w-4 h-4 text-muted-foreground flex-shrink-0" />}
                  <StatusBadge status={bug.severity} size="sm" />
                  <span className="font-mono text-xs text-muted-foreground flex-shrink-0">{bug.bug_id}</span>
                  <span className="font-medium text-sm flex-1 truncate">{bug.title}</span>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    {bug.is_flaky && <span className="text-xs bg-yellow-900/30 text-yellow-400 px-2 py-0.5 rounded-full">Flaky</span>}
                    {bug.is_environment_issue && <span className="text-xs bg-blue-900/30 text-blue-400 px-2 py-0.5 rounded-full">Env issue</span>}
                    <StatusBadge status={bug.status} size="sm" />
                    <select
                      value={bug.status}
                      onChange={(e) => { e.stopPropagation(); statusMutation.mutate({ id: bug.id, status: e.target.value }); }}
                      onClick={(e) => e.stopPropagation()}
                      className="bg-secondary border border-border rounded px-2 py-1 text-xs"
                    >
                      {["open", "in_progress", "fixed", "wont_fix", "duplicate", "verified"].map((s) => (
                        <option key={s} value={s}>{s.replace("_", " ")}</option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Expanded detail */}
                {isOpen && (
                  <div className="border-t border-border p-4 space-y-4 text-sm">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-xs text-muted-foreground mb-1">Description</p>
                        <p>{bug.description}</p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground mb-1">Environment</p>
                        <p>{bug.environment || "—"}</p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground mb-1">Expected</p>
                        <p className="text-green-400">{bug.expected_result}</p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground mb-1">Actual</p>
                        <p className="text-red-400">{bug.actual_result}</p>
                      </div>
                    </div>

                    {bug.steps_to_reproduce?.length > 0 && (
                      <div>
                        <p className="text-xs text-muted-foreground mb-2">Steps to Reproduce</p>
                        <ol className="space-y-1">
                          {bug.steps_to_reproduce.map((step: string, i: number) => (
                            <li key={i} className="flex gap-2">
                              <span className="bg-secondary rounded px-1.5 text-xs flex-shrink-0">{i + 1}</span>
                              <span className="text-xs">{typeof step === "string" ? step : JSON.stringify(step)}</span>
                            </li>
                          ))}
                        </ol>
                      </div>
                    )}

                    {bug.root_cause && (
                      <div className="bg-secondary/50 rounded-lg p-3">
                        <p className="text-xs text-muted-foreground mb-1">Root Cause (AI Analysis)</p>
                        <p className="text-sm">{bug.root_cause}</p>
                      </div>
                    )}

                    {bug.suggested_fix && (
                      <div className="bg-green-950/30 border border-green-800/40 rounded-lg p-3">
                        <p className="text-xs text-green-400 mb-1 flex items-center gap-1">
                          <Lightbulb className="w-3 h-3" /> Suggested Fix (AI)
                        </p>
                        <p className="text-sm">{bug.suggested_fix}</p>
                      </div>
                    )}

                    {bug.console_logs?.length > 0 && (
                      <div>
                        <p className="text-xs text-muted-foreground mb-2">Console Errors</p>
                        <div className="bg-black/40 rounded p-2 space-y-1 max-h-40 overflow-y-auto">
                          {bug.console_logs.slice(0, 10).map((log, i) => (
                            <p key={i} className="text-xs font-mono text-red-400">{log.type}: {log.text}</p>
                          ))}
                        </div>
                      </div>
                    )}

                    {bug.screenshots?.length > 0 && (
                      <div>
                        <p className="text-xs text-muted-foreground mb-2">Screenshots</p>
                        <div className="flex gap-2 flex-wrap">
                          {bug.screenshots.map((ss, i) => (
                            <a key={i} href={ss} target="_blank">
                              <img src={ss} alt={`screenshot ${i + 1}`} className="h-24 rounded border border-border object-cover" />
                            </a>
                          ))}
                        </div>
                      </div>
                    )}

                    <p className="text-xs text-muted-foreground">{formatDate(bug.created_at)}</p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
