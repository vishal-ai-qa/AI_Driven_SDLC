"use client";

import { useQuery } from "@tanstack/react-query";
import { useStore } from "@/lib/store";
import { traceabilityApi } from "@/lib/api";
import { StatusBadge } from "@/components/ui/status-badge";
import { GitBranch, ChevronRight, ChevronDown } from "lucide-react";
import { useState } from "react";

interface TraceNode {
  id: string;
  type: string;
  title: string;
  status: string;
  children: TraceNode[];
}

function TreeNode({ node, depth = 0 }: { node: TraceNode; depth?: number }) {
  const [open, setOpen] = useState(depth < 2);
  const hasChildren = node.children?.length > 0;

  const typeColors: Record<string, string> = {
    requirement: "text-blue-400",
    story: "text-purple-400",
    test_case: "text-green-400",
  };

  return (
    <div>
      <div
        className={`flex items-center gap-2 py-1.5 px-2 rounded hover:bg-secondary/50 cursor-pointer group ${depth > 0 ? "ml-6" : ""}`}
        onClick={() => setOpen(!open)}
        style={{ paddingLeft: `${depth * 24 + 8}px` }}
      >
        {hasChildren ? (
          open ? <ChevronDown className="w-3.5 h-3.5 text-muted-foreground flex-shrink-0" /> : <ChevronRight className="w-3.5 h-3.5 text-muted-foreground flex-shrink-0" />
        ) : (
          <span className="w-3.5 flex-shrink-0" />
        )}
        <span className={`text-xs font-mono flex-shrink-0 ${typeColors[node.type] || "text-muted-foreground"}`}>
          {node.type.replace("_", " ").toUpperCase()} • {node.id}
        </span>
        <span className="text-sm truncate flex-1">{node.title}</span>
        <StatusBadge status={node.status} size="sm" />
      </div>
      {open && hasChildren && node.children.map((child) => (
        <TreeNode key={`${child.type}-${child.id}`} node={child} depth={depth + 1} />
      ))}
    </div>
  );
}

export default function TraceabilityPage() {
  const { activeProjectId } = useStore();

  const { data, isLoading } = useQuery({
    queryKey: ["traceability", activeProjectId],
    queryFn: () => traceabilityApi.matrix(activeProjectId!),
    enabled: !!activeProjectId,
  });

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <h1 className="text-xl font-bold">Traceability Matrix</h1>
        <p className="text-sm text-muted-foreground">Requirement → Story → Test Case coverage</p>
      </div>

      {!activeProjectId ? (
        <div className="flex items-center justify-center h-40 text-muted-foreground text-sm">Select a project</div>
      ) : isLoading ? (
        <div className="flex items-center justify-center h-40 text-muted-foreground text-sm">Computing matrix...</div>
      ) : data ? (
        <>
          {/* Coverage summary */}
          <div className="grid grid-cols-3 gap-4">
            <div className="rounded-xl border border-border bg-card p-5 text-center">
              <p className="text-3xl font-bold text-primary">{data.coverage_percentage}%</p>
              <p className="text-xs text-muted-foreground mt-1">Requirement Coverage</p>
            </div>
            <div className="rounded-xl border border-border bg-card p-5 text-center">
              <p className="text-3xl font-bold">{data.nodes?.length || 0}</p>
              <p className="text-xs text-muted-foreground mt-1">Total Requirements</p>
            </div>
            <div className="rounded-xl border border-border bg-card p-5 text-center">
              <p className="text-3xl font-bold text-red-400">{data.uncovered_requirements?.length || 0}</p>
              <p className="text-xs text-muted-foreground mt-1">Uncovered</p>
            </div>
          </div>

          {/* Coverage bar */}
          <div className="rounded-xl border border-border bg-card p-5">
            <div className="flex items-center justify-between text-xs text-muted-foreground mb-2">
              <span>Overall Coverage</span>
              <span>{data.coverage_percentage}%</span>
            </div>
            <div className="h-2 bg-secondary rounded-full overflow-hidden">
              <div
                className="h-full bg-primary rounded-full transition-all"
                style={{ width: `${data.coverage_percentage}%` }}
              />
            </div>
            {data.uncovered_requirements?.length > 0 && (
              <p className="text-xs text-red-400 mt-2">
                Uncovered: {data.uncovered_requirements.join(", ")}
              </p>
            )}
          </div>

          {/* Tree */}
          <div className="rounded-xl border border-border bg-card p-4">
            <div className="flex items-center gap-2 mb-4 pb-3 border-b border-border">
              <GitBranch className="w-4 h-4 text-primary" />
              <span className="font-semibold text-sm">Traceability Tree</span>
            </div>
            <div className="space-y-0.5">
              {data.nodes?.map((node: TraceNode) => (
                <TreeNode key={node.id} node={node} depth={0} />
              ))}
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
}
