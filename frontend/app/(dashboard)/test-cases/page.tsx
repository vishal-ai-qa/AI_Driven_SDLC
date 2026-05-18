"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useStore } from "@/lib/store";
import { testCasesApi } from "@/lib/api";
import { StatusBadge } from "@/components/ui/status-badge";
import { toast } from "sonner";
import {
  FlaskConical,
  ChevronDown,
  ChevronRight,
  Zap,
  CheckCircle,
  Shield,
  Globe,
  Accessibility,
  Gauge,
} from "lucide-react";
import { formatDate } from "@/lib/utils";

interface TestStep {
  step_number: number;
  action: string;
  test_data?: string;
  expected_result: string;
}

interface TestCase {
  id: string;
  tc_id: string;
  title: string;
  description: string | null;
  test_type: string;
  preconditions: string[];
  test_steps: TestStep[];
  expected_result: string;
  priority: string;
  severity: string;
  status: string;
  automation_feasibility: string;
  tags: string[];
  requirement_ref: string | null;
  story_ref: string | null;
  confidence_score: number;
  created_at: string;
}

const TEST_TYPE_ICONS: Record<string, React.ReactNode> = {
  functional: <FlaskConical className="w-3 h-3" />,
  security: <Shield className="w-3 h-3" />,
  api: <Globe className="w-3 h-3" />,
  accessibility: <Accessibility className="w-3 h-3" />,
  performance: <Gauge className="w-3 h-3" />,
};

const TEST_TYPES = [
  "functional", "negative", "boundary", "security",
  "api", "ui", "accessibility", "performance", "integration", "regression",
];

export default function TestCasesPage() {
  const { activeProjectId } = useStore();
  const qc = useQueryClient();
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [filterType, setFilterType] = useState<string>("");
  const [filterStatus, setFilterStatus] = useState<string>("");

  const { data: testCases = [], isLoading } = useQuery<TestCase[]>({
    queryKey: ["test-cases", activeProjectId, filterType, filterStatus],
    queryFn: () => testCasesApi.list(activeProjectId!),
    enabled: !!activeProjectId,
    refetchInterval: 5000,
  });

  const filtered = testCases.filter((tc) => {
    if (filterType && tc.test_type !== filterType) return false;
    if (filterStatus && tc.status !== filterStatus) return false;
    return true;
  });

  const generateMutation = useMutation({
    mutationFn: () => testCasesApi.generate(activeProjectId!),
    onSuccess: () => {
      toast.success("Test case generation started — AI is processing approved stories");
      setTimeout(() => qc.invalidateQueries({ queryKey: ["test-cases"] }), 5000);
    },
    onError: (e: any) =>
      toast.error(e?.response?.data?.detail || "Generation failed. Approve stories first."),
  });

  const approveMutation = useMutation({
    mutationFn: (id: string) => testCasesApi.approve(id),
    onSuccess: () => {
      toast.success("Test case approved");
      qc.invalidateQueries({ queryKey: ["test-cases"] });
    },
  });

  const approveAllMutation = useMutation({
    mutationFn: () => testCasesApi.approveAll(activeProjectId!),
    onSuccess: (data: any) => {
      toast.success(`${data.approved_count} test cases approved`);
      qc.invalidateQueries({ queryKey: ["test-cases"] });
    },
  });

  const toggle = (id: string) =>
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });

  const draftCount = testCases.filter((tc) => tc.status === "draft").length;
  const approvedCount = testCases.filter((tc) => tc.status === "approved").length;
  const automatable = testCases.filter((tc) => tc.automation_feasibility === "automatable").length;

  const byType = TEST_TYPES.reduce<Record<string, number>>((acc, t) => {
    acc[t] = testCases.filter((tc) => tc.test_type === t).length;
    return acc;
  }, {});

  if (!activeProjectId) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
        <FlaskConical className="w-12 h-12 mb-4 opacity-20" />
        <p>Select a project to view test cases</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Test Cases</h1>
          <p className="text-sm text-muted-foreground mt-1">
            {testCases.length} test cases — {approvedCount} approved, {automatable} automatable
          </p>
        </div>
        <div className="flex gap-2">
          {draftCount > 0 && (
            <button
              onClick={() => approveAllMutation.mutate()}
              disabled={approveAllMutation.isPending}
              className="flex items-center gap-2 px-4 py-2 text-sm border rounded-lg hover:bg-muted transition-colors"
            >
              <CheckCircle className="w-4 h-4" />
              Approve All ({draftCount})
            </button>
          )}
          <button
            onClick={() => generateMutation.mutate()}
            disabled={generateMutation.isPending}
            className="flex items-center gap-2 px-4 py-2 text-sm bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
          >
            <Zap className="w-4 h-4" />
            {generateMutation.isPending ? "Generating…" : "Generate Test Cases"}
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: "Total", value: testCases.length },
          { label: "Approved", value: approvedCount },
          { label: "Automatable", value: automatable },
          { label: "Draft", value: draftCount },
        ].map((stat) => (
          <div key={stat.label} className="border rounded-lg p-4">
            <p className="text-sm text-muted-foreground">{stat.label}</p>
            <p className="text-2xl font-bold mt-1">{stat.value}</p>
          </div>
        ))}
      </div>

      {/* Type breakdown */}
      <div className="border rounded-lg p-4">
        <p className="text-sm font-medium mb-3">Test Coverage by Type</p>
        <div className="flex flex-wrap gap-2">
          {TEST_TYPES.filter((t) => byType[t] > 0).map((t) => (
            <button
              key={t}
              onClick={() => setFilterType(filterType === t ? "" : t)}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-full border transition-colors ${
                filterType === t
                  ? "bg-primary text-primary-foreground border-primary"
                  : "hover:bg-muted"
              }`}
            >
              {TEST_TYPE_ICONS[t] ?? <FlaskConical className="w-3 h-3" />}
              {t} ({byType[t]})
            </button>
          ))}
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-3 items-center">
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="text-sm border rounded-lg px-3 py-1.5 bg-background"
        >
          <option value="">All statuses</option>
          <option value="draft">Draft</option>
          <option value="approved">Approved</option>
          <option value="review">Review</option>
        </select>
        {(filterType || filterStatus) && (
          <button
            onClick={() => { setFilterType(""); setFilterStatus(""); }}
            className="text-xs text-muted-foreground hover:text-foreground"
          >
            Clear filters
          </button>
        )}
        <span className="text-xs text-muted-foreground ml-auto">
          Showing {filtered.length} of {testCases.length}
        </span>
      </div>

      {/* Test case list */}
      {isLoading ? (
        <div className="space-y-2">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-14 rounded-lg bg-muted animate-pulse" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="border rounded-lg p-12 text-center text-muted-foreground">
          <FlaskConical className="w-8 h-8 mx-auto mb-3 opacity-20" />
          <p>{testCases.length === 0 ? "No test cases yet." : "No test cases match the filter."}</p>
          {testCases.length === 0 && (
            <p className="text-xs mt-1">Approve stories first, then click Generate Test Cases.</p>
          )}
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map((tc) => {
            const isOpen = expanded.has(tc.id);
            return (
              <div key={tc.id} className="border rounded-lg overflow-hidden">
                <div
                  className="flex items-center gap-3 p-4 cursor-pointer hover:bg-muted/50 transition-colors"
                  onClick={() => toggle(tc.id)}
                >
                  {isOpen ? (
                    <ChevronDown className="w-4 h-4 shrink-0 text-muted-foreground" />
                  ) : (
                    <ChevronRight className="w-4 h-4 shrink-0 text-muted-foreground" />
                  )}
                  <span className="font-mono text-xs text-muted-foreground w-20 shrink-0">
                    {tc.tc_id}
                  </span>
                  <span className="flex-1 text-sm font-medium">{tc.title}</span>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="flex items-center gap-1 text-xs border rounded px-2 py-0.5">
                      {TEST_TYPE_ICONS[tc.test_type] ?? <FlaskConical className="w-3 h-3" />}
                      {tc.test_type}
                    </span>
                    <StatusBadge status={tc.severity} />
                    <StatusBadge status={tc.status} />
                    {tc.status !== "approved" && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          approveMutation.mutate(tc.id);
                        }}
                        className="text-xs px-2 py-1 bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
                      >
                        Approve
                      </button>
                    )}
                  </div>
                </div>

                {isOpen && (
                  <div className="px-4 pb-4 pt-0 border-t bg-muted/20 space-y-4">
                    {tc.description && (
                      <div className="mt-4">
                        <p className="text-xs font-semibold text-muted-foreground uppercase mb-1">
                          Description
                        </p>
                        <p className="text-sm text-muted-foreground">{tc.description}</p>
                      </div>
                    )}

                    {(tc.preconditions?.length ?? 0) > 0 && (
                      <div>
                        <p className="text-xs font-semibold text-muted-foreground uppercase mb-2">
                          Preconditions
                        </p>
                        <ul className="space-y-1">
                          {tc.preconditions.map((pc, i) => (
                            <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                              <span className="mt-0.5">•</span>
                              {pc}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {(tc.test_steps?.length ?? 0) > 0 && (
                      <div>
                        <p className="text-xs font-semibold text-muted-foreground uppercase mb-2">
                          Test Steps
                        </p>
                        <div className="space-y-2">
                          {tc.test_steps.map((step, i) => (
                            <div key={i} className="flex gap-3 text-sm">
                              <span className="w-6 h-6 rounded-full bg-muted flex items-center justify-center text-xs font-bold shrink-0">
                                {step.step_number ?? i + 1}
                              </span>
                              <div className="flex-1">
                                <p>{step.action}</p>
                                {step.test_data && (
                                  <p className="text-xs text-muted-foreground mt-0.5">
                                    Data: {step.test_data}
                                  </p>
                                )}
                                {step.expected_result && (
                                  <p className="text-xs text-green-600 dark:text-green-400 mt-0.5">
                                    ✓ {step.expected_result}
                                  </p>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {tc.expected_result && (
                      <div>
                        <p className="text-xs font-semibold text-muted-foreground uppercase mb-1">
                          Expected Result
                        </p>
                        <p className="text-sm">{tc.expected_result}</p>
                      </div>
                    )}

                    <div className="flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
                      <span>Automation: {tc.automation_feasibility}</span>
                      {tc.story_ref && <span>Story: {tc.story_ref}</span>}
                      {tc.requirement_ref && <span>Req: {tc.requirement_ref}</span>}
                      <span>Confidence: {Math.round(tc.confidence_score * 100)}%</span>
                      <span>Created: {formatDate(tc.created_at)}</span>
                    </div>

                    {(tc.tags?.length ?? 0) > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {tc.tags.map((tag) => (
                          <span
                            key={tag}
                            className="text-xs border rounded px-2 py-0.5 bg-muted"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
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
