"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useStore } from "@/lib/store";
import { testRunsApi } from "@/lib/api";
import { StatusBadge } from "@/components/ui/status-badge";
import { toast } from "sonner";
import { Play, Plus, ExternalLink, BarChart2 } from "lucide-react";
import { formatDate } from "@/lib/utils";
import { useWebSocket } from "@/hooks/use-websocket";

export default function ExecutionPage() {
  const { activeProjectId } = useStore();
  const qc = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [watchRunId, setWatchRunId] = useState<string | null>(null);
  const [runProgress, setRunProgress] = useState<Record<string, { passed: number; failed: number; total: number }>>({});

  const [form, setForm] = useState({
    name: "",
    environment: "staging",
    app_url: "",
    app_username: "",
    app_password: "",
  });

  const { data: runs = [], isLoading } = useQuery({
    queryKey: ["test-runs", activeProjectId],
    queryFn: () => testRunsApi.list(activeProjectId!),
    enabled: !!activeProjectId,
    refetchInterval: 5000,
  });

  // Live progress for watched run
  useWebSocket(
    watchRunId ? `ws://localhost:8000/ws/run/${watchRunId}` : null,
    (data: { event: string; passed: number; failed: number; total: number; run_id: string }) => {
      if (data.event === "run_progress" || data.event === "run_complete") {
        setRunProgress((prev) => ({
          ...prev,
          [data.run_id]: { passed: data.passed, failed: data.failed, total: data.total },
        }));
        if (data.event === "run_complete") {
          qc.invalidateQueries({ queryKey: ["test-runs"] });
          toast.success("Test run completed");
        }
      }
    }
  );

  const createMutation = useMutation({
    mutationFn: () => testRunsApi.create({ ...form, project_id: activeProjectId }),
    onSuccess: (run) => {
      toast.success("Test run started — AI agents executing");
      setShowForm(false);
      setWatchRunId(run.id);
      qc.invalidateQueries({ queryKey: ["test-runs"] });
    },
    onError: () => toast.error("Failed to start test run"),
  });

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">Test Execution</h1>
          <p className="text-sm text-muted-foreground">Phase 5 — AI agents execute tests autonomously</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium"
        >
          <Plus className="w-4 h-4" /> New Run
        </button>
      </div>

      {/* New run form */}
      {showForm && (
        <div className="rounded-xl border border-primary/30 bg-card p-6 space-y-4">
          <h2 className="font-semibold text-sm">Configure Test Run</h2>
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label className="block text-xs text-muted-foreground mb-1">Run Name</label>
              <input
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="Sprint 3 Regression"
                className="w-full bg-secondary border border-border rounded-lg px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs text-muted-foreground mb-1">Environment</label>
              <select
                value={form.environment}
                onChange={(e) => setForm({ ...form, environment: e.target.value })}
                className="w-full bg-secondary border border-border rounded-lg px-3 py-2 text-sm"
              >
                <option value="staging">Staging</option>
                <option value="uat">UAT</option>
                <option value="production">Production</option>
                <option value="local">Local</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-muted-foreground mb-1">Application URL</label>
              <input
                value={form.app_url}
                onChange={(e) => setForm({ ...form, app_url: e.target.value })}
                placeholder="https://app.yourcompany.com"
                className="w-full bg-secondary border border-border rounded-lg px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs text-muted-foreground mb-1">Username (optional)</label>
              <input
                value={form.app_username}
                onChange={(e) => setForm({ ...form, app_username: e.target.value })}
                placeholder="test@example.com"
                className="w-full bg-secondary border border-border rounded-lg px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs text-muted-foreground mb-1">Password (optional)</label>
              <input
                type="password"
                value={form.app_password}
                onChange={(e) => setForm({ ...form, app_password: e.target.value })}
                placeholder="Encrypted at rest"
                className="w-full bg-secondary border border-border rounded-lg px-3 py-2 text-sm"
              />
            </div>
          </div>
          <p className="text-xs text-muted-foreground">
            * All approved test cases in this project will be executed. Credentials are encrypted.
          </p>
          <div className="flex justify-end gap-2">
            <button onClick={() => setShowForm(false)} className="px-4 py-2 text-sm rounded-lg hover:bg-secondary">Cancel</button>
            <button
              onClick={() => createMutation.mutate()}
              disabled={!form.name || !form.app_url || createMutation.isPending}
              className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium disabled:opacity-50"
            >
              <Play className="w-4 h-4" />
              {createMutation.isPending ? "Starting..." : "Start Execution"}
            </button>
          </div>
        </div>
      )}

      {/* Runs list */}
      {isLoading ? (
        <div className="flex items-center justify-center h-40 text-muted-foreground text-sm">Loading...</div>
      ) : runs.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border p-12 text-center">
          <Play className="w-10 h-10 mx-auto mb-3 text-muted-foreground/40" />
          <p className="text-muted-foreground">No test runs yet. Create one to start AI execution.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {runs.map((run: {
            id: string; run_id: string; name: string; environment: string;
            status: string; total_cases: number; passed: number; failed: number;
            blocked: number; skipped: number; created_at: string; report_path?: string;
          }) => {
            const live = runProgress[run.id];
            const passed = live?.passed ?? run.passed;
            const failed = live?.failed ?? run.failed;
            const total = run.total_cases;
            const pct = total > 0 ? Math.round(((passed + failed) / total) * 100) : 0;

            return (
              <div key={run.id} className="rounded-xl border border-border bg-card p-5">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs text-muted-foreground">{run.run_id}</span>
                      <h3 className="font-semibold text-sm">{run.name}</h3>
                      <span className="text-xs bg-secondary px-2 py-0.5 rounded-full text-muted-foreground">{run.environment}</span>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">{formatDate(run.created_at)}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <StatusBadge status={run.status} />
                    {run.report_path && (
                      <a href={`/reports/runs/${run.id}/bug_report.html`} target="_blank" className="p-1.5 rounded hover:bg-secondary text-muted-foreground">
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    )}
                    <button onClick={() => setWatchRunId(run.id === watchRunId ? null : run.id)}
                      className="p-1.5 rounded hover:bg-secondary text-muted-foreground">
                      <BarChart2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                {/* Progress bar */}
                {total > 0 && (
                  <div className="mt-3">
                    <div className="flex justify-between text-xs text-muted-foreground mb-1">
                      <span>{passed + failed} / {total} executed</span>
                      <span>{pct}%</span>
                    </div>
                    <div className="h-1.5 bg-secondary rounded-full overflow-hidden flex">
                      <div className="bg-green-500 transition-all" style={{ width: `${(passed / total) * 100}%` }} />
                      <div className="bg-red-500 transition-all" style={{ width: `${(failed / total) * 100}%` }} />
                    </div>
                    <div className="flex gap-4 mt-2 text-xs">
                      <span className="text-green-400">✓ {passed} passed</span>
                      <span className="text-red-400">✗ {failed} failed</span>
                      <span className="text-yellow-400">⊘ {run.blocked} blocked</span>
                      <span className="text-slate-400">– {run.skipped} skipped</span>
                    </div>
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
