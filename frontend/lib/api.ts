/**
 * Typed API client — all calls go through Axios with JWT injection.
 */
import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: { "Content-Type": "application/json" },
});

// Inject JWT from localStorage
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auto-refresh on 401
api.interceptors.response.use(
  (res) => res,
  async (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("access_token");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

// ─── Auth ─────────────────────────────────────────────────────────────────────

export const authApi = {
  login: (email: string, password: string) =>
    api.post("/auth/login", { email, password }).then((r) => r.data),
  register: (data: Record<string, unknown>) =>
    api.post("/auth/register", data).then((r) => r.data),
  me: () => api.get("/auth/me").then((r) => r.data),
};

// ─── Projects ─────────────────────────────────────────────────────────────────

export const projectsApi = {
  list: () => api.get("/projects").then((r) => r.data),
  get: (id: string) => api.get(`/projects/${id}`).then((r) => r.data),
  stats: (id: string) => api.get(`/projects/${id}/stats`).then((r) => r.data),
  roi: (id: string) => api.get(`/projects/${id}/roi`).then((r) => r.data),
  gaps: (id: string) => api.get(`/projects/${id}/gaps`).then((r) => r.data),
  detectGaps: (id: string) => api.post(`/projects/${id}/detect-gaps`).then((r) => r.data),
  agentLogs: (id: string, limit = 20) =>
    api.get(`/projects/${id}/agent-logs`, { params: { limit } }).then((r) => r.data),
  create: (data: Record<string, unknown>) => api.post("/projects", data).then((r) => r.data),
  update: (id: string, data: Record<string, unknown>) =>
    api.patch(`/projects/${id}`, data).then((r) => r.data),
};

// ─── Requirements ─────────────────────────────────────────────────────────────

export const requirementsApi = {
  list: (projectId: string) =>
    api.get("/requirements", { params: { project_id: projectId } }).then((r) => r.data),
  ingest: (projectId: string, content: string, sourceType: string, context?: string) =>
    api.post(`/requirements/ingest?project_id=${projectId}`, {
      content,
      source_type: sourceType,
      additional_context: context,
    }).then((r) => r.data),
  update: (id: string, data: Record<string, unknown>) =>
    api.patch(`/requirements/${id}`, data).then((r) => r.data),
  approve: (id: string) => api.patch(`/requirements/${id}/approve`).then((r) => r.data),
  approveAll: (projectId: string) =>
    api.patch(`/requirements/approve-all?project_id=${projectId}`).then((r) => r.data),
  upload: (projectId: string, file: File) => {
    const fd = new FormData();
    fd.append("project_id", projectId);
    fd.append("file", file);
    return api.post("/requirements/upload", fd, { headers: { "Content-Type": "multipart/form-data" } }).then((r) => r.data);
  },
};

// ─── Stories ──────────────────────────────────────────────────────────────────

export const storiesApi = {
  list: (projectId: string) =>
    api.get("/stories", { params: { project_id: projectId } }).then((r) => r.data),
  generate: (projectId: string) =>
    api.post(`/stories/generate?project_id=${projectId}`).then((r) => r.data),
  update: (id: string, data: Record<string, unknown>) =>
    api.patch(`/stories/${id}`, data).then((r) => r.data),
  approve: (id: string) => api.patch(`/stories/${id}/approve`).then((r) => r.data),
  approveAll: (projectId: string) =>
    api.patch(`/stories/approve-all?project_id=${projectId}`).then((r) => r.data),
};

// ─── Test Cases ───────────────────────────────────────────────────────────────

export const testCasesApi = {
  list: (projectId: string) =>
    api.get("/test-cases", { params: { project_id: projectId } }).then((r) => r.data),
  generate: (projectId: string) =>
    api.post(`/test-cases/generate?project_id=${projectId}`).then((r) => r.data),
  update: (id: string, data: Record<string, unknown>) =>
    api.patch(`/test-cases/${id}`, data).then((r) => r.data),
  approve: (id: string) => api.patch(`/test-cases/${id}/approve`).then((r) => r.data),
  approveAll: (projectId: string) =>
    api.patch(`/test-cases/approve-all?project_id=${projectId}`).then((r) => r.data),
};

// ─── Test Runs ────────────────────────────────────────────────────────────────

export const testRunsApi = {
  list: (projectId: string) =>
    api.get("/test-runs", { params: { project_id: projectId } }).then((r) => r.data),
  get: (id: string) => api.get(`/test-runs/${id}`).then((r) => r.data),
  create: (data: Record<string, unknown>) => api.post("/test-runs", data).then((r) => r.data),
  executions: (runId: string) => api.get(`/test-runs/${runId}/executions`).then((r) => r.data),
};

// ─── Bugs ─────────────────────────────────────────────────────────────────────

export const bugsApi = {
  list: (params: Record<string, string>) => api.get("/bugs", { params }).then((r) => r.data),
  get: (id: string) => api.get(`/bugs/${id}`).then((r) => r.data),
  updateStatus: (id: string, status: string) =>
    api.patch(`/bugs/${id}/status`, {}, { params: { status } }).then((r) => r.data),
};

// ─── Automation ───────────────────────────────────────────────────────────────

export const automationApi = {
  list: (projectId: string) =>
    api.get("/automation", { params: { project_id: projectId } }).then((r) => r.data),
  generate: (projectId: string, runId: string) =>
    api.post(`/automation/generate?project_id=${projectId}&run_id=${runId}`).then((r) => r.data),
  download: (projectId: string) =>
    `${API_URL}/api/automation/download/${projectId}`,
};

// ─── Traceability ─────────────────────────────────────────────────────────────

export const traceabilityApi = {
  matrix: (projectId: string) =>
    api.get(`/traceability/${projectId}`).then((r) => r.data),
};

// ─── Approvals ────────────────────────────────────────────────────────────────

export const approvalsApi = {
  create: (data: Record<string, unknown>) => api.post("/approvals", data).then((r) => r.data),
  list: (params: Record<string, string>) => api.get("/approvals", { params }).then((r) => r.data),
};
