"use client";

import { useQuery, useMutation } from "@tanstack/react-query";
import { useStore } from "@/lib/store";
import { projectsApi } from "@/lib/api";
import { toast } from "sonner";
import {
  BarChart3, DollarSign, Clock, Shield, TrendingUp,
  AlertTriangle, CheckCircle, Download, Zap,
} from "lucide-react";

interface RoiData {
  project_id: string;
  generated_at: string;
  cost: {
    total_tokens: number;
    total_cost_usd: number;
    by_phase: Record<string, { tokens: number; cost_usd: number }>;
  };
  coverage: {
    requirements_total: number;
    requirements_covered: number;
    coverage_pct: number;
  };
  time_saved: {
    hours_requirement_analysis: number;
    hours_test_case_writing: number;
    hours_test_execution: number;
    hours_bug_report_writing: number;
    total_hours_saved: number;
    estimated_cost_saved_usd: number;
  };
  quality: {
    bugs_caught: number;
    defect_escape_averted_usd: number;
    test_cases_generated: number;
    test_runs: number;
  };
  roi_multiplier: number;
}

interface GapData {
  gaps: Array<{
    story_ref: string;
    gap_type: string;
    severity: string;
    description: string;
    recommendation: string;
    confidence_score: number;
  }>;
  summary: {
    total_gaps: number;
    critical: number;
    high: number;
    medium: number;
    low: number;
    coverage_risk: string;
  } | null;
  last_run: string | null;
}

const SEVERITY_COLORS: Record<string, string> = {
  critical: "text-red-400 bg-red-900/20 border-red-800",
  high: "text-orange-400 bg-orange-900/20 border-orange-800",
  medium: "text-yellow-400 bg-yellow-900/20 border-yellow-800",
  low: "text-blue-400 bg-blue-900/20 border-blue-800",
};

const GAP_TYPE_LABELS: Record<string, string> = {
  missing_edge_case: "Missing Edge Case",
  ambiguous_ac: "Ambiguous AC",
  missing_security: "Security Gap",
  missing_error_handling: "No Error Handling",
  missing_boundary: "Missing Boundary",
  missing_performance: "Performance Gap",
  duplicate: "Duplicate Story",
};

export default function AnalyticsPage() {
  const { activeProjectId } = useStore();

  const { data: roi, isLoading: roiLoading } = useQuery<RoiData>({
    queryKey: ["roi", activeProjectId],
    queryFn: () => projectsApi.roi(activeProjectId!),
    enabled: !!activeProjectId,
    refetchInterval: 30000,
  });

  const { data: gaps, isLoading: gapsLoading, refetch: refetchGaps } = useQuery<GapData>({
    queryKey: ["gaps", activeProjectId],
    queryFn: () => projectsApi.gaps(activeProjectId!),
    enabled: !!activeProjectId,
  });

  const detectGapsMutation = useMutation({
    mutationFn: () => projectsApi.detectGaps(activeProjectId!),
    onSuccess: () => {
      toast.success("Gap analysis started — results will appear in ~30 seconds");
      setTimeout(() => refetchGaps(), 30000);
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail || "Gap analysis failed"),
  });

  const exportData = (format: "json" | "csv") => {
    window.open(
      `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/projects/${activeProjectId}/export?format=${format}`,
      "_blank"
    );
  };

  if (!activeProjectId) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
        <BarChart3 className="w-12 h-12 mb-4 opacity-20" />
        <p>Select a project to view analytics</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Analytics & ROI</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Business value delivered by QAgent for this project
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => exportData("csv")}
            className="flex items-center gap-2 px-3 py-2 text-sm border rounded-lg hover:bg-muted transition-colors"
          >
            <Download className="w-4 h-4" />
            CSV
          </button>
          <button
            onClick={() => exportData("json")}
            className="flex items-center gap-2 px-3 py-2 text-sm border rounded-lg hover:bg-muted transition-colors"
          >
            <Download className="w-4 h-4" />
            JSON
          </button>
          <button
            onClick={() => detectGapsMutation.mutate()}
            disabled={detectGapsMutation.isPending}
            className="flex items-center gap-2 px-4 py-2 text-sm bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
          >
            <Zap className="w-4 h-4" />
            {detectGapsMutation.isPending ? "Analyzing…" : "Run Gap Analysis"}
          </button>
        </div>
      </div>

      {roiLoading ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-32 rounded-xl bg-muted animate-pulse" />
          ))}
        </div>
      ) : roi ? (
        <>
          {/* ROI multiplier hero */}
          <div className="rounded-xl border bg-gradient-to-br from-primary/10 to-primary/5 p-8 flex items-center gap-8">
            <div className="text-center">
              <p className="text-5xl font-black text-primary">{roi.roi_multiplier}×</p>
              <p className="text-sm text-muted-foreground mt-1">ROI Multiplier</p>
            </div>
            <div className="h-16 w-px bg-border" />
            <div className="flex-1 grid grid-cols-3 gap-6">
              <div>
                <p className="text-2xl font-bold">{roi.time_saved.total_hours_saved}h</p>
                <p className="text-sm text-muted-foreground">Time Saved</p>
              </div>
              <div>
                <p className="text-2xl font-bold">
                  ${roi.time_saved.estimated_cost_saved_usd.toLocaleString()}
                </p>
                <p className="text-sm text-muted-foreground">Est. Cost Saved</p>
              </div>
              <div>
                <p className="text-2xl font-bold">${roi.cost.total_cost_usd.toFixed(2)}</p>
                <p className="text-sm text-muted-foreground">AI Cost Spent</p>
              </div>
            </div>
          </div>

          {/* Coverage + Quality */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="border rounded-xl p-5">
              <div className="flex items-center gap-2 mb-3">
                <Shield className="w-4 h-4 text-green-400" />
                <p className="text-sm font-medium">Test Coverage</p>
              </div>
              <p className="text-3xl font-bold">{roi.coverage.coverage_pct}%</p>
              <div className="mt-2 h-2 rounded-full bg-muted overflow-hidden">
                <div
                  className="h-full rounded-full bg-green-500 transition-all"
                  style={{ width: `${roi.coverage.coverage_pct}%` }}
                />
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                {roi.coverage.requirements_covered}/{roi.coverage.requirements_total} requirements
              </p>
            </div>

            <div className="border rounded-xl p-5">
              <div className="flex items-center gap-2 mb-3">
                <AlertTriangle className="w-4 h-4 text-red-400" />
                <p className="text-sm font-medium">Bugs Caught</p>
              </div>
              <p className="text-3xl font-bold">{roi.quality.bugs_caught}</p>
              <p className="text-sm text-green-400 mt-1">
                ${roi.quality.defect_escape_averted_usd.toLocaleString()} averted
              </p>
              <p className="text-xs text-muted-foreground mt-1">@$10K per escaped defect</p>
            </div>

            <div className="border rounded-xl p-5">
              <div className="flex items-center gap-2 mb-3">
                <CheckCircle className="w-4 h-4 text-blue-400" />
                <p className="text-sm font-medium">Test Cases</p>
              </div>
              <p className="text-3xl font-bold">{roi.quality.test_cases_generated}</p>
              <p className="text-xs text-muted-foreground mt-1">
                across {roi.quality.test_runs} runs
              </p>
            </div>

            <div className="border rounded-xl p-5">
              <div className="flex items-center gap-2 mb-3">
                <TrendingUp className="w-4 h-4 text-yellow-400" />
                <p className="text-sm font-medium">Token Usage</p>
              </div>
              <p className="text-3xl font-bold">{(roi.cost.total_tokens / 1000).toFixed(0)}K</p>
              <p className="text-xs text-muted-foreground mt-1">${roi.cost.total_cost_usd} total</p>
            </div>
          </div>

          {/* Time breakdown */}
          <div className="border rounded-xl p-6">
            <h2 className="font-semibold mb-4 flex items-center gap-2">
              <Clock className="w-4 h-4" />
              Time Saved Breakdown
            </h2>
            <div className="space-y-3">
              {[
                { label: "Requirement Analysis", hours: roi.time_saved.hours_requirement_analysis },
                { label: "Test Case Writing", hours: roi.time_saved.hours_test_case_writing },
                { label: "Test Execution", hours: roi.time_saved.hours_test_execution },
                { label: "Bug Report Writing", hours: roi.time_saved.hours_bug_report_writing },
              ].map((item) => {
                const pct = roi.time_saved.total_hours_saved > 0
                  ? Math.round((item.hours / roi.time_saved.total_hours_saved) * 100)
                  : 0;
                return (
                  <div key={item.label}>
                    <div className="flex justify-between text-sm mb-1">
                      <span>{item.label}</span>
                      <span className="text-muted-foreground">{item.hours}h</span>
                    </div>
                    <div className="h-2 rounded-full bg-muted overflow-hidden">
                      <div
                        className="h-full rounded-full bg-primary/70 transition-all"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Cost by phase */}
          <div className="border rounded-xl p-6">
            <h2 className="font-semibold mb-4 flex items-center gap-2">
              <DollarSign className="w-4 h-4" />
              AI Cost by Phase
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {Object.entries(roi.cost.by_phase).map(([phase, data]) => (
                <div key={phase} className="border rounded-lg p-3">
                  <p className="text-xs text-muted-foreground truncate">{phase.replace(/_/g, " ")}</p>
                  <p className="text-lg font-bold mt-1">${data.cost_usd}</p>
                  <p className="text-xs text-muted-foreground">{(data.tokens / 1000).toFixed(1)}K tokens</p>
                </div>
              ))}
            </div>
          </div>
        </>
      ) : null}

      {/* Gap Analysis Results */}
      <div className="border rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-yellow-400" />
            Gap Analysis
            {gaps?.last_run && (
              <span className="text-xs text-muted-foreground font-normal">
                Last run: {new Date(gaps.last_run).toLocaleDateString()}
              </span>
            )}
          </h2>
          {gaps?.summary && (
            <div className="flex gap-3 text-xs">
              {gaps.summary.critical > 0 && (
                <span className="text-red-400">{gaps.summary.critical} critical</span>
              )}
              {gaps.summary.high > 0 && (
                <span className="text-orange-400">{gaps.summary.high} high</span>
              )}
              <span className="text-muted-foreground">{gaps.summary.total_gaps} total gaps</span>
            </div>
          )}
        </div>

        {gapsLoading ? (
          <div className="h-24 bg-muted animate-pulse rounded-lg" />
        ) : !gaps?.gaps?.length ? (
          <div className="text-center py-8 text-muted-foreground">
            <AlertTriangle className="w-8 h-8 mx-auto mb-2 opacity-20" />
            <p>No gap analysis run yet.</p>
            <p className="text-xs mt-1">Click "Run Gap Analysis" to scan your stories for missing coverage.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {gaps.gaps.map((gap, i) => (
              <div
                key={i}
                className={`border rounded-lg p-4 ${SEVERITY_COLORS[gap.severity] || ""}`}
              >
                <div className="flex items-start gap-3">
                  <div className="flex flex-col gap-1 shrink-0">
                    <span className="text-xs font-mono">{gap.story_ref}</span>
                    <span className="text-xs capitalize">{gap.severity}</span>
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium">
                      {GAP_TYPE_LABELS[gap.gap_type] || gap.gap_type}
                    </p>
                    <p className="text-xs mt-1 opacity-80">{gap.description}</p>
                    <p className="text-xs mt-2 border-t border-current/20 pt-2 opacity-70">
                      ✓ {gap.recommendation}
                    </p>
                  </div>
                  <span className="text-xs shrink-0 opacity-60">
                    {Math.round(gap.confidence_score * 100)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
