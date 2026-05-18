"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useStore } from "@/lib/store";
import { requirementsApi } from "@/lib/api";
import { StatusBadge } from "@/components/ui/status-badge";
import { toast } from "sonner";
import {
  FileText, Upload, Zap, CheckCircle, AlertCircle,
  Pencil, X, Save, ChevronDown, ChevronRight,
} from "lucide-react";
import { useDropzone } from "react-dropzone";
import { formatDate } from "@/lib/utils";

interface Requirement {
  id: string;
  req_id: string;
  title: string;
  description: string;
  req_type: string;
  priority: string;
  confidence_score: number;
  status: string;
  needs_clarification: boolean;
  ambiguities: string[];
  assumptions: string[];
  risks: string[];
  created_at: string;
}

function EditModal({
  req,
  onClose,
  onSave,
}: {
  req: Requirement;
  onClose: () => void;
  onSave: (data: Record<string, unknown>) => void;
}) {
  const [title, setTitle] = useState(req.title);
  const [description, setDescription] = useState(req.description || "");
  const [priority, setPriority] = useState(req.priority);
  const [clarificationAnswer, setClarificationAnswer] = useState("");

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-background border rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <p className="font-mono text-xs text-muted-foreground">{req.req_id}</p>
            <h2 className="font-semibold text-lg mt-0.5">Edit Requirement</h2>
          </div>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-muted transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-6 space-y-4">
          <div>
            <label className="text-xs font-semibold text-muted-foreground uppercase mb-1 block">Title</label>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-2 text-sm bg-muted border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-muted-foreground uppercase mb-1 block">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={4}
              className="w-full px-3 py-2 text-sm bg-muted border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary resize-none"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-muted-foreground uppercase mb-1 block">Priority</label>
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
              className="w-full px-3 py-2 text-sm bg-muted border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>

          {/* Clarification section for low-confidence items */}
          {(req.needs_clarification || req.ambiguities?.length > 0) && (
            <div className="border border-yellow-800/50 rounded-xl p-4 bg-yellow-900/10 space-y-3">
              <p className="text-sm font-semibold text-yellow-400 flex items-center gap-2">
                <AlertCircle className="w-4 h-4" />
                Needs Clarification
              </p>
              {req.ambiguities?.map((a, i) => (
                <p key={i} className="text-sm text-muted-foreground">• {a}</p>
              ))}
              <div>
                <label className="text-xs font-semibold text-muted-foreground uppercase mb-1 block">
                  Your Clarification Answer
                </label>
                <textarea
                  value={clarificationAnswer}
                  onChange={(e) => setClarificationAnswer(e.target.value)}
                  placeholder="Provide clarification to resolve ambiguities and boost confidence score..."
                  rows={3}
                  className="w-full px-3 py-2 text-sm bg-muted border rounded-lg focus:outline-none focus:ring-2 focus:ring-yellow-500 resize-none"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Submitting a clarification will boost the confidence score and mark as draft.
                </p>
              </div>
            </div>
          )}
        </div>

        <div className="flex gap-2 justify-end p-6 pt-0">
          <button onClick={onClose} className="px-4 py-2 text-sm rounded-lg hover:bg-muted transition-colors">
            Cancel
          </button>
          <button
            onClick={() =>
              onSave({
                title,
                description,
                priority,
                ...(clarificationAnswer ? { clarification_answer: clarificationAnswer } : {}),
              })
            }
            className="flex items-center gap-2 px-4 py-2 text-sm bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
          >
            <Save className="w-4 h-4" />
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
}

export default function RequirementsPage() {
  const { activeProjectId } = useStore();
  const qc = useQueryClient();
  const [ingestText, setIngestText] = useState("");
  const [sourceType, setSourceType] = useState("brd");
  const [showIngest, setShowIngest] = useState(false);
  const [editingReq, setEditingReq] = useState<Requirement | null>(null);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  const { data: requirements = [], isLoading } = useQuery<Requirement[]>({
    queryKey: ["requirements", activeProjectId],
    queryFn: () => requirementsApi.list(activeProjectId!),
    enabled: !!activeProjectId,
    refetchInterval: 5000,
  });

  const ingestMutation = useMutation({
    mutationFn: () => requirementsApi.ingest(activeProjectId!, ingestText, sourceType),
    onSuccess: () => {
      toast.success("Requirement ingestion started — AI is parsing your content");
      setIngestText("");
      setShowIngest(false);
      setTimeout(() => qc.invalidateQueries({ queryKey: ["requirements"] }), 3000);
    },
    onError: () => toast.error("Ingestion failed"),
  });

  const approveMutation = useMutation({
    mutationFn: (id: string) => requirementsApi.approve(id),
    onSuccess: () => {
      toast.success("Requirement approved");
      qc.invalidateQueries({ queryKey: ["requirements"] });
    },
  });

  const approveAllMutation = useMutation({
    mutationFn: () => requirementsApi.approveAll(activeProjectId!),
    onSuccess: (data: any) => {
      toast.success(`${data.approved_count} requirements approved`);
      qc.invalidateQueries({ queryKey: ["requirements"] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Record<string, unknown> }) =>
      requirementsApi.update(id, data),
    onSuccess: () => {
      toast.success("Requirement updated");
      qc.invalidateQueries({ queryKey: ["requirements"] });
      setEditingReq(null);
    },
    onError: () => toast.error("Update failed"),
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => requirementsApi.upload(activeProjectId!, file),
    onSuccess: () => toast.success("File uploaded — parsing in background"),
  });

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: (files) => files.forEach((f) => uploadMutation.mutate(f)),
    accept: {
      "application/pdf": [],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [],
      "text/plain": [],
    },
  });

  const draftCount = requirements.filter((r) => r.status === "draft" || r.status === "needs_clarification").length;
  const clarificationCount = requirements.filter((r) => r.needs_clarification).length;

  const toggle = (id: string) =>
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });

  if (!activeProjectId) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
        <FileText className="w-12 h-12 mb-4 opacity-20" />
        <p>Select a project to manage requirements</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-5xl">
      {editingReq && (
        <EditModal
          req={editingReq}
          onClose={() => setEditingReq(null)}
          onSave={(data) => updateMutation.mutate({ id: editingReq.id, data })}
        />
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">Requirements</h1>
          <p className="text-sm text-muted-foreground">
            Phase 1 — {requirements.length} total
            {clarificationCount > 0 && (
              <span className="text-yellow-400 ml-2">· {clarificationCount} need clarification</span>
            )}
          </p>
        </div>
        <div className="flex gap-2">
          {draftCount > 0 && (
            <button
              onClick={() => approveAllMutation.mutate()}
              disabled={approveAllMutation.isPending}
              className="flex items-center gap-2 px-3 py-2 text-sm border rounded-lg hover:bg-muted transition-colors"
            >
              <CheckCircle className="w-4 h-4" />
              Approve All ({draftCount})
            </button>
          )}
          <button
            onClick={() => setShowIngest(!showIngest)}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
          >
            <Zap className="w-4 h-4" /> AI Ingest
          </button>
        </div>
      </div>

      {/* Ingest form */}
      {showIngest && (
        <div className="rounded-xl border border-primary/30 bg-card p-6 space-y-4">
          <h2 className="font-semibold text-sm flex items-center gap-2">
            <Zap className="w-4 h-4 text-primary" /> AI Requirement Ingestion
          </h2>
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
              isDragActive ? "border-primary bg-primary/5" : "border-border hover:border-primary/50"
            }`}
          >
            <input {...getInputProps()} />
            <Upload className="w-6 h-6 mx-auto mb-2 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">Drop BRD/PDF/Word files here, or click to upload</p>
          </div>
          <div className="text-center text-muted-foreground text-xs">— OR paste text below —</div>
          <select
            value={sourceType}
            onChange={(e) => setSourceType(e.target.value)}
            className="w-full bg-secondary border border-border rounded-lg px-3 py-2 text-sm"
          >
            <option value="brd">BRD (Business Requirements Document)</option>
            <option value="epic">Epic</option>
            <option value="feature">Feature Description</option>
            <option value="api_spec">API Specification</option>
            <option value="acceptance_criteria">Acceptance Criteria</option>
          </select>
          <textarea
            value={ingestText}
            onChange={(e) => setIngestText(e.target.value)}
            placeholder="Paste your BRD, epic, feature description, or any requirement text here..."
            rows={8}
            className="w-full bg-secondary border border-border rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary"
          />
          <div className="flex gap-2 justify-end">
            <button onClick={() => setShowIngest(false)} className="px-4 py-2 text-sm rounded-lg hover:bg-secondary transition-colors">
              Cancel
            </button>
            <button
              onClick={() => ingestMutation.mutate()}
              disabled={!ingestText.trim() || ingestMutation.isPending}
              className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium disabled:opacity-50"
            >
              <Zap className="w-4 h-4" />
              {ingestMutation.isPending ? "Processing..." : "Run AI Ingestion"}
            </button>
          </div>
        </div>
      )}

      {/* Requirements list */}
      {isLoading ? (
        <div className="space-y-2">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-14 rounded-lg bg-muted animate-pulse" />
          ))}
        </div>
      ) : requirements.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border p-12 text-center">
          <FileText className="w-10 h-10 mx-auto mb-3 text-muted-foreground/40" />
          <p className="text-muted-foreground">No requirements yet. Use AI Ingest to parse your documents.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {requirements.map((req) => {
            const isOpen = expanded.has(req.id);
            return (
              <div
                key={req.id}
                className={`border rounded-lg overflow-hidden ${
                  req.needs_clarification ? "border-yellow-800/50" : ""
                }`}
              >
                <div
                  className="flex items-center gap-3 p-4 cursor-pointer hover:bg-muted/40 transition-colors"
                  onClick={() => toggle(req.id)}
                >
                  {isOpen ? (
                    <ChevronDown className="w-4 h-4 shrink-0 text-muted-foreground" />
                  ) : (
                    <ChevronRight className="w-4 h-4 shrink-0 text-muted-foreground" />
                  )}
                  <span className="font-mono text-xs text-muted-foreground w-20 shrink-0">
                    {req.req_id}
                  </span>
                  <span className="flex-1 text-sm font-medium">{req.title}</span>
                  <div className="flex items-center gap-2 shrink-0">
                    {req.needs_clarification && (
                      <AlertCircle className="w-4 h-4 text-yellow-400" />
                    )}
                    {/* Confidence bar */}
                    <div className="flex items-center gap-1.5 w-20">
                      <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${
                            req.confidence_score >= 0.8
                              ? "bg-green-500"
                              : req.confidence_score >= 0.5
                              ? "bg-yellow-500"
                              : "bg-red-500"
                          }`}
                          style={{ width: `${req.confidence_score * 100}%` }}
                        />
                      </div>
                      <span className="text-xs text-muted-foreground w-8">
                        {Math.round(req.confidence_score * 100)}%
                      </span>
                    </div>
                    <span className="text-xs border rounded px-1.5 py-0.5">{req.req_type}</span>
                    <StatusBadge status={req.priority} />
                    <StatusBadge status={req.status} />
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setEditingReq(req);
                      }}
                      className="p-1.5 rounded hover:bg-muted transition-colors text-muted-foreground hover:text-foreground"
                      title="Edit"
                    >
                      <Pencil className="w-3.5 h-3.5" />
                    </button>
                    {req.status !== "approved" && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          approveMutation.mutate(req.id);
                        }}
                        className="text-xs px-2 py-1 bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
                      >
                        Approve
                      </button>
                    )}
                  </div>
                </div>

                {isOpen && (
                  <div className="px-4 pb-4 pt-0 border-t bg-muted/10 space-y-3">
                    {req.description && (
                      <p className="text-sm text-muted-foreground mt-4">{req.description}</p>
                    )}
                    <div className="grid grid-cols-2 gap-4">
                      {req.assumptions?.length > 0 && (
                        <div>
                          <p className="text-xs font-semibold text-muted-foreground uppercase mb-1">Assumptions</p>
                          <ul className="space-y-0.5">
                            {req.assumptions.map((a, i) => (
                              <li key={i} className="text-xs text-muted-foreground">• {a}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {req.risks?.length > 0 && (
                        <div>
                          <p className="text-xs font-semibold text-muted-foreground uppercase mb-1">Risks</p>
                          <ul className="space-y-0.5">
                            {req.risks.map((r, i) => (
                              <li key={i} className="text-xs text-orange-400">⚠ {r}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                    {req.ambiguities?.length > 0 && (
                      <div className="border border-yellow-800/40 rounded-lg p-3 bg-yellow-900/10">
                        <p className="text-xs font-semibold text-yellow-400 mb-1">Ambiguities — click Edit to resolve</p>
                        {req.ambiguities.map((a, i) => (
                          <p key={i} className="text-xs text-muted-foreground">• {a}</p>
                        ))}
                      </div>
                    )}
                    <p className="text-xs text-muted-foreground">Created: {formatDate(req.created_at)}</p>
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
