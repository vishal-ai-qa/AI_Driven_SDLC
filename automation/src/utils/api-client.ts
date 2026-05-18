/**
 * Typed API client for Playwright tests — handles auth token injection.
 */
import { APIRequestContext } from "@playwright/test";

export class ApiClient {
  private token: string | null = null;

  constructor(private readonly request: APIRequestContext) {}

  async authenticate(email: string, password: string): Promise<void> {
    const res = await this.request.post("/api/auth/login", {
      data: { email, password },
    });
    if (!res.ok()) throw new Error(`Auth failed: ${res.status()}`);
    const body = await res.json();
    this.token = body.access_token;
  }

  private headers() {
    return this.token ? { Authorization: `Bearer ${this.token}` } : {};
  }

  async getProjects() {
    return this.request.get("/api/projects", { headers: this.headers() });
  }

  async createProject(name: string, description?: string) {
    return this.request.post("/api/projects", {
      headers: this.headers(),
      data: { name, description },
    });
  }

  async ingestRequirements(projectId: string, content: string, sourceType = "brd") {
    return this.request.post(`/api/requirements/ingest?project_id=${projectId}`, {
      headers: this.headers(),
      data: { content, source_type: sourceType },
    });
  }

  async listRequirements(projectId: string) {
    return this.request.get(`/api/requirements?project_id=${projectId}`, {
      headers: this.headers(),
    });
  }
}
