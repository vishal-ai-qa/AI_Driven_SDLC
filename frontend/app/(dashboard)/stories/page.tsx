"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useStore } from "@/lib/store";
import { storiesApi } from "@/lib/api";
import { StatusBadge } from "@/components/ui/status-badge";
import { toast } from "sonner";
import { BookOpen, ChevronDown, ChevronRight, Zap, CheckCircle } from "lucide-react";
import { useState } from "react";
import { formatDate } from "@/lib/utils";

interface Story {
  id: string;
  story_id: string;
  title: string;
  role: string;
  goal: string;
  business_value: string;
  acceptance_criteria: string[];
  priority: string;
  risk_level: string;
  story_points: number | null;
  status: string;
  confidence_score: number;
  created_at: string;
}

export default function StoriesPage() {
  const { activeProjectId } = useStore();
  const qc = useQueryClient();
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  const { data: stories = [], isLoading } = useQuery<Story[]>({
    queryKey: ["stories", activeProjectId],
    queryFn: () => storiesApi.list(activeProjectId!),
    enabled: !!activeProjectId,
    refetchInterval: 5000,
  });

  const generateMutation = useMutation({
    mutationFn: () => storiesApi.generate(activeProjectId!),
    onSuccess: () => {
      toast.success("Story generation started — AI is processing approved requirements");
      setTimeout(() => qc.invalidateQueries({ queryKey: ["stories"] }), 5000);
    },
    onError: (e: any) =>
      toast.error(e?.response?.data?.detail || "Generation failed. Approve requirements first."),
  });

  const approveMutation = useMutation({
    mutationFn: (id: string) => storiesApi.approve(id),
    onSuccess: () => {
      toast.success("Story approved");
      qc.invalidateQueries({ queryKey: ["stories"] });
    },
  });

  const approveAllMutation = useMutation({
    mutationFn: () => storiesApi.approveAll(activeProjectId!),
    onSuccess: (data: any) => {
      toast.success(`${data.approved_count} stories approved`);
      qc.invalidateQueries({ queryKey: ["stories"] });
    },
  });

  const toggle = (id: string) =>
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });

  const draftCount = stories.filter((s) => s.status === "draft").length;
  const approvedCount = stories.filter((s) => s.status === "approved").length;

  if (!activeProjectId) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
        <BookOpen className="w-12 h-12 mb-4 opacity-20" />
        <p>Select a project to view user stories</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">User Stories</h1>
          <p className="text-sm text-muted-foreground mt-1">
            {stories.length} stories — {approvedCount} approved, {draftCount} pending review
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
            {generateMutation.isPending ? "Generating…" : "Generate Stories"}
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: "Total Stories", value: stories.length },
          { label: "Approved", value: approvedCount },
          { label: "Draft", value: draftCount },
          {
            label: "Avg Story Points",
            value:
              stories.filter((s) => s.story_points).length > 0
                ? Math.round(
                    stories.reduce((sum, s) => sum + (s.story_points || 0), 0) /
                      stories.filter((s) => s.story_points).length
                  )
                : "—",
          },
        ].map((stat) => (
          <div key={stat.label} className="border rounded-lg p-4">
            <p className="text-sm text-muted-foreground">{stat.label}</p>
            <p className="text-2xl font-bold mt-1">{stat.value}</p>
          </div>
        ))}
      </div>

      {/* Story list */}
      {isLoading ? (
        <div className="space-y-2">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-16 rounded-lg bg-muted animate-pulse" />
          ))}
        </div>
      ) : stories.length === 0 ? (
        <div className="border rounded-lg p-12 text-center text-muted-foreground">
          <BookOpen className="w-8 h-8 mx-auto mb-3 opacity-20" />
          <p>No user stories yet.</p>
          <p className="text-xs mt-1">Approve requirements first, then click Generate Stories.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {stories.map((story) => {
            const isOpen = expanded.has(story.id);
            return (
              <div key={story.id} className="border rounded-lg overflow-hidden">
                <div
                  className="flex items-center gap-3 p-4 cursor-pointer hover:bg-muted/50 transition-colors"
                  onClick={() => toggle(story.id)}
                >
                  {isOpen ? (
                    <ChevronDown className="w-4 h-4 shrink-0 text-muted-foreground" />
                  ) : (
                    <ChevronRight className="w-4 h-4 shrink-0 text-muted-foreground" />
                  )}
                  <span className="font-mono text-xs text-muted-foreground w-16 shrink-0">
                    {story.story_id}
                  </span>
                  <span className="flex-1 text-sm font-medium">{story.title}</span>
                  <div className="flex items-center gap-2 shrink-0">
                    {story.story_points && (
                      <span className="text-xs border rounded px-1.5 py-0.5">
                        {story.story_points} pts
                      </span>
                    )}
                    <StatusBadge status={story.priority} />
                    <StatusBadge status={story.status} />
                    {story.status !== "approved" && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          approveMutation.mutate(story.id);
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
                    <div className="grid grid-cols-2 gap-4 mt-4">
                      <div>
                        <p className="text-xs font-semibold text-muted-foreground uppercase mb-1">
                          As a
                        </p>
                        <p className="text-sm">{story.role}</p>
                      </div>
                      <div>
                        <p className="text-xs font-semibold text-muted-foreground uppercase mb-1">
                          I want to
                        </p>
                        <p className="text-sm">{story.goal}</p>
                      </div>
                    </div>

                    {story.business_value && (
                      <div>
                        <p className="text-xs font-semibold text-muted-foreground uppercase mb-1">
                          Business Value
                        </p>
                        <p className="text-sm text-muted-foreground">{story.business_value}</p>
                      </div>
                    )}

                    {story.acceptance_criteria?.length > 0 && (
                      <div>
                        <p className="text-xs font-semibold text-muted-foreground uppercase mb-2">
                          Acceptance Criteria
                        </p>
                        <ul className="space-y-1">
                          {story.acceptance_criteria.map((ac, i) => (
                            <li key={i} className="flex items-start gap-2 text-sm">
                              <span className="text-green-500 mt-0.5">✓</span>
                              <span>{ac}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    <div className="flex items-center gap-4 text-xs text-muted-foreground">
                      <span>Risk: {story.risk_level}</span>
                      <span>Confidence: {Math.round(story.confidence_score * 100)}%</span>
                      <span>Created: {formatDate(story.created_at)}</span>
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
