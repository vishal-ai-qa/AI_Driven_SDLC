"use client";

import { useQuery, useMutation } from "@tanstack/react-query";
import { useStore } from "@/lib/store";
import { automationApi, testRunsApi } from "@/lib/api";
import { toast } from "sonner";
import { Code2, Download, Play, FileCode } from "lucide-react";
import { useState } from "react";

export default function AutomationPage() {
  const { activeProjectId } = useStore();
  const [selectedScript, setSelectedScript] = useState<{ file_path: string; content: string } | null>(null);

  const { data: runs = [] } = useQuery({
    queryKey: ["test-runs", activeProjectId],
    queryFn: () => testRunsApi.list(activeProjectId!),
    enabled: !!activeProjectId,
  });

  const { data: scripts = [], isLoading } = useQuery({
    queryKey: ["automation", activeProjectId],
    queryFn: () => automationApi.list(activeProjectId!),
    enabled: !!activeProjectId,
  });

  const generateMutation = useMutation({
    mutationFn: (runId: string) => automationApi.generate(activeProjectId!, runId),
    onSuccess: () => toast.success("Playwright generation started"),
    onError: () => toast.error("Generation failed"),
  });

  const latestRun = runs[0];

  return (
    <div className="space-y-6 max-w-6xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">Automation Repository</h1>
          <p className="text-sm text-muted-foreground">Phase 8 — AI-generated Playwright TypeScript framework</p>
        </div>
        <div className="flex gap-2">
          {latestRun && (
            <button
              onClick={() => generateMutation.mutate(latestRun.id)}
              disabled={generateMutation.isPending}
              className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium disabled:opacity-50"
            >
              <Play className="w-4 h-4" />
              {generateMutation.isPending ? "Generating..." : "Generate Scripts"}
            </button>
          )}
          {activeProjectId && scripts.length > 0 && (
            <a
              href={automationApi.download(activeProjectId)}
              className="flex items-center gap-2 px-4 py-2 bg-secondary text-foreground rounded-lg text-sm font-medium hover:bg-secondary/80"
            >
              <Download className="w-4 h-4" /> Download ZIP
            </a>
          )}
        </div>
      </div>

      {/* Split view: file list + code preview */}
      {scripts.length > 0 && (
        <div className="flex gap-4 rounded-xl border border-border overflow-hidden h-[600px]">
          {/* File tree */}
          <div className="w-64 border-r border-border bg-card overflow-y-auto">
            <div className="p-3 border-b border-border text-xs font-medium text-muted-foreground uppercase tracking-wide">
              Files ({scripts.length})
            </div>
            {(scripts as Array<{ id: string; file_path: string; content: string; script_id: string }>).map((script) => (
              <button
                key={script.id}
                onClick={() => setSelectedScript(script)}
                className={`w-full flex items-center gap-2 px-3 py-2 text-xs text-left hover:bg-secondary transition-colors truncate ${
                  selectedScript?.file_path === script.file_path ? "bg-primary/10 text-primary" : "text-muted-foreground"
                }`}
              >
                <FileCode className="w-3.5 h-3.5 flex-shrink-0" />
                <span className="truncate">{script.file_path}</span>
              </button>
            ))}
          </div>

          {/* Code preview */}
          <div className="flex-1 bg-black/30 overflow-auto">
            {selectedScript ? (
              <pre className="p-4 text-xs font-mono text-green-300 whitespace-pre-wrap leading-relaxed">
                {selectedScript.content}
              </pre>
            ) : (
              <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
                Select a file to preview
              </div>
            )}
          </div>
        </div>
      )}

      {!isLoading && scripts.length === 0 && (
        <div className="rounded-xl border border-dashed border-border p-12 text-center">
          <Code2 className="w-10 h-10 mx-auto mb-3 text-muted-foreground/40" />
          <p className="text-muted-foreground">No automation scripts yet.</p>
          <p className="text-xs text-muted-foreground mt-1">Complete a test run and click "Generate Scripts" to create the Playwright framework.</p>
        </div>
      )}
    </div>
  );
}
