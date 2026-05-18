"use client";

import { useQuery } from "@tanstack/react-query";
import { useStore } from "@/lib/store";
import { projectsApi, testRunsApi, bugsApi } from "@/lib/api";
import { StatusBadge } from "@/components/ui/status-badge";
import { StatCard } from "@/components/ui/stat-card";
import { AgentPipeline } from "@/components/agent-pipeline";
import {
  FileText, BookOpen, FlaskConical, Bug,
  Play, Zap, Activity, CheckCircle, AlertCircle, Loader2,
} from "lucide-react";
import Link from "next/link";
import { formatDate } from "@/lib/utils";

const AGENT_STATUS_ICON: Record<string, React.ReactNode> = {
  completed: <CheckCircle className="w-3.5 h-3.5 text-green-400 shrink-0" />,
  error: <AlertCircle className="w-3.5 h-3.5 text-red-400 shrink-0" />,
  running: <Loader2 className="w-3.5 h-3.5 text-blue-400 shrink-0 animate-spin" />,
};

export default function DashboardPage() {
  const { activeProjectId } = useStore();

  const { data: stats } = useQuery({
    queryKey: ["project-stats", activeProjectId],
    queryFn: () => projectsApi.stats(activeProjectId!),
    enabled: !!activeProjectId,
    refetchInterval: 10000,
  });

  const { data: runs = [] } = useQuery({
    queryKey: ["test-runs", activeProjectId],
    queryFn: () => testRunsApi.list(activeProjectId!),
    enabled: !!activeProjectId,
  });

  const { data: bugs = [] } = useQuery({
    queryKey: ["bugs", activeProjectId],
    queryFn: () => bugsApi.list(activeProjectId ? { project_id: activeProjectId } : {}),
    enabled: !!activeProjectId,
  });

  const { data: agentLogs = [] } = useQuery({
    queryKey: ["agent-logs", activeProjectId],
    queryFn: () => projectsApi.agentLogs(activeProjectId!, 10),
    enabled: !!activeProjectId,
    refetchInterval: 8000,
  });

  const latestRun = runs[0];
  const criticalBugs = bugs.filter((b: { severity: string }) => b.severity === "critical").length;

  return (
    <div className="space-y-8">
      {/* Project selector */}
      {!activeProjectId && (
        <div className="rounded-xl border border-border bg-card p-8 text-center">
          <Zap className="w-12 h-12 text-primary mx-auto mb-4" />
          <h2 className="text-xl font-bold mb-2">Welcome to QAgent</h2>
          <p className="text-muted-foreground mb-4">Select a project or create one to get started.</p>
          <Link href="/dashboard/requirements" className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium">
            Create Project
          </Link>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Requirements"
          value={stats?.requirements?.total ?? "—"}
          icon={<FileText className="w-4 h-4" />}
          sub={stats ? `${stats.requirements.approved} approved` : "Loading…"}
          href="/dashboard/requirements"
        />
        <StatCard
          label="User Stories"
          value={stats?.stories?.total ?? "—"}
          icon={<BookOpen className="w-4 h-4" />}
          sub={stats ? `${stats.stories.approved} approved` : "Loading…"}
          href="/dashboard/stories"
        />
        <StatCard
          label="Test Cases"
          value={stats?.test_cases?.total ?? "—"}
          icon={<FlaskConical className="w-4 h-4" />}
          sub={stats ? `${stats.test_cases.approved} approved` : "Loading…"}
          href="/dashboard/test-cases"
        />
        <StatCard
          label="Open Bugs"
          value={stats?.bugs?.open ?? bugs.length}
          icon={<Bug className="w-4 h-4" />}
          sub={`${criticalBugs} critical`}
          accent={criticalBugs > 0 ? "red" : undefined}
          href="/dashboard/bugs"
        />
      </div>

      {/* Phase pipeline */}
      <AgentPipeline projectId={activeProjectId} />

      {/* Latest run summary */}
      {latestRun && (
        <div className="rounded-xl border border-border bg-card p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold">Latest Test Run — {latestRun.run_id}</h2>
            <StatusBadge status={latestRun.status} />
          </div>
          <div className="grid grid-cols-4 gap-4">
            {[
              { label: "Passed", value: latestRun.passed, color: "text-green-400" },
              { label: "Failed", value: latestRun.failed, color: "text-red-400" },
              { label: "Blocked", value: latestRun.blocked, color: "text-yellow-400" },
              { label: "Skipped", value: latestRun.skipped, color: "text-slate-400" },
            ].map(({ label, value, color }) => (
              <div key={label} className="text-center">
                <p className={`text-2xl font-bold ${color}`}>{value}</p>
                <p className="text-xs text-muted-foreground">{label}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Bottom row: Agent activity + Recent bugs */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Agent activity feed */}
        {agentLogs.length > 0 && (
          <div className="rounded-xl border border-border bg-card p-6">
            <div className="flex items-center gap-2 mb-4">
              <Activity className="w-4 h-4 text-primary" />
              <h2 className="font-semibold">Agent Activity</h2>
            </div>
            <div className="space-y-2">
              {agentLogs.slice(0, 8).map((log: {
                id: string; agent: string; phase: string;
                status: string; output_summary: string; timestamp: string;
                tokens_used: number; error: string;
              }) => (
                <div key={log.id} className="flex items-start gap-2 py-1.5 border-b border-border/50 last:border-0">
                  {AGENT_STATUS_ICON[log.status] ?? <Activity className="w-3.5 h-3.5 text-muted-foreground shrink-0" />}
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium truncate">{log.agent?.replace(/_/g, " ")}</p>
                    <p className="text-xs text-muted-foreground truncate">
                      {log.error || log.output_summary || log.phase}
                    </p>
                  </div>
                  <div className="shrink-0 text-right">
                    <p className="text-xs text-muted-foreground">{formatDate(log.timestamp)}</p>
                    {log.tokens_used > 0 && (
                      <p className="text-xs text-muted-foreground">{(log.tokens_used / 1000).toFixed(1)}K tok</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
            <Link href="/dashboard/analytics" className="text-xs text-primary hover:underline mt-3 block">
              View ROI & cost →
            </Link>
          </div>
        )}

        {/* Recent bugs */}
        {bugs.length > 0 && (
          <div className="rounded-xl border border-border bg-card p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold">Recent Bugs</h2>
              <Link href="/dashboard/bugs" className="text-xs text-primary hover:underline">View all</Link>
            </div>
            <div className="space-y-2">
              {bugs.slice(0, 5).map((bug: { id: string; bug_id: string; title: string; severity: string; status: string; created_at: string }) => (
                <div key={bug.id} className="flex items-center gap-3 py-2 border-b border-border last:border-0">
                  <StatusBadge status={bug.severity} size="sm" />
                  <span className="text-xs text-muted-foreground w-16 flex-shrink-0">{bug.bug_id}</span>
                  <span className="text-sm flex-1 truncate">{bug.title}</span>
                  <StatusBadge status={bug.status} size="sm" />
                  <span className="text-xs text-muted-foreground">{formatDate(bug.created_at)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
