"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useStore } from "@/lib/store";
import { projectsApi } from "@/lib/api";
import { toast } from "sonner";
import { ChevronDown, Plus, FolderOpen, Check, X, Loader2 } from "lucide-react";

interface Project {
  id: string;
  name: string;
  description?: string;
  status: string;
}

export function ProjectSelector() {
  const { activeProjectId, setActiveProject } = useStore();
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [appUrl, setAppUrl] = useState("");

  const { data: projects = [] } = useQuery<Project[]>({
    queryKey: ["projects"],
    queryFn: projectsApi.list,
  });

  const activeProject = projects.find((p) => p.id === activeProjectId);

  const createMutation = useMutation({
    mutationFn: () =>
      projectsApi.create({ name: name.trim(), description: description.trim(), app_url: appUrl.trim() || undefined }),
    onSuccess: (created: Project) => {
      qc.invalidateQueries({ queryKey: ["projects"] });
      setActiveProject(created.id);
      toast.success(`Project "${created.name}" created`);
      setShowCreate(false);
      setName("");
      setDescription("");
      setAppUrl("");
      setOpen(false);
    },
    onError: () => toast.error("Failed to create project"),
  });

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg border hover:bg-muted transition-colors text-sm max-w-48"
      >
        <FolderOpen className="w-3.5 h-3.5 shrink-0 text-primary" />
        <span className="truncate">
          {activeProject?.name || "Select Project"}
        </span>
        <ChevronDown className="w-3.5 h-3.5 shrink-0 text-muted-foreground" />
      </button>

      {open && (
        <>
          {/* Backdrop */}
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />

          <div className="absolute left-0 top-full mt-1 w-72 bg-popover border rounded-xl shadow-lg z-50 overflow-hidden">
            {/* Project list */}
            <div className="max-h-64 overflow-y-auto p-1">
              {projects.length === 0 ? (
                <div className="px-3 py-4 text-center text-sm text-muted-foreground">
                  No projects yet
                </div>
              ) : (
                projects.map((project) => (
                  <button
                    key={project.id}
                    onClick={() => {
                      setActiveProject(project.id);
                      setOpen(false);
                    }}
                    className="w-full flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-muted transition-colors text-left"
                  >
                    <div className="w-6 h-6 rounded bg-primary/20 flex items-center justify-center text-xs font-bold text-primary shrink-0">
                      {project.name[0].toUpperCase()}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{project.name}</p>
                      {project.description && (
                        <p className="text-xs text-muted-foreground truncate">{project.description}</p>
                      )}
                    </div>
                    {project.id === activeProjectId && (
                      <Check className="w-4 h-4 text-primary shrink-0" />
                    )}
                  </button>
                ))
              )}
            </div>

            <div className="border-t p-1">
              {!showCreate ? (
                <button
                  onClick={() => setShowCreate(true)}
                  className="w-full flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-muted transition-colors text-sm text-primary"
                >
                  <Plus className="w-4 h-4" />
                  New Project
                </button>
              ) : (
                <div className="p-2 space-y-2">
                  <div className="flex items-center justify-between">
                    <p className="text-xs font-semibold text-muted-foreground">New Project</p>
                    <button
                      onClick={() => setShowCreate(false)}
                      className="text-muted-foreground hover:text-foreground"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                  <input
                    autoFocus
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Project name *"
                    className="w-full px-3 py-1.5 text-sm bg-background border rounded-lg focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                  <input
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Description (optional)"
                    className="w-full px-3 py-1.5 text-sm bg-background border rounded-lg focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                  <input
                    value={appUrl}
                    onChange={(e) => setAppUrl(e.target.value)}
                    placeholder="App URL (optional)"
                    className="w-full px-3 py-1.5 text-sm bg-background border rounded-lg focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                  <button
                    onClick={() => createMutation.mutate()}
                    disabled={!name.trim() || createMutation.isPending}
                    className="w-full py-1.5 text-sm bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    {createMutation.isPending ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <Plus className="w-3.5 h-3.5" />
                    )}
                    Create Project
                  </button>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
