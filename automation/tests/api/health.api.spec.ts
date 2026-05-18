/**
 * API Test Suite — Backend health and core endpoint validation.
 * Runs in the "api" Playwright project (no browser).
 */
import { test, expect } from "@playwright/test";

const API = process.env.API_URL || "http://localhost:8000";

test.describe("API — Health & Auth", () => {
  test("GET /api/health returns 200", async ({ request }) => {
    const res = await request.get(`${API}/api/health`);
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body.status).toBe("healthy");
  });

  test("POST /api/auth/login with valid credentials returns tokens", async ({ request }) => {
    const res = await request.post(`${API}/api/auth/login`, {
      data: {
        email: process.env.TEST_USER_EMAIL || "admin@qagent.dev",
        password: process.env.TEST_USER_PASSWORD || "Admin@1234",
      },
    });
    expect(res.status()).toBe(200);
    const body = await res.json();
    expect(body.access_token).toBeTruthy();
    expect(body.user).toBeDefined();
  });

  test("POST /api/auth/login with invalid credentials returns 401", async ({ request }) => {
    const res = await request.post(`${API}/api/auth/login`, {
      data: { email: "bad@example.com", password: "wrongpassword" },
    });
    expect(res.status()).toBe(401);
  });

  test("GET /api/projects requires auth", async ({ request }) => {
    const res = await request.get(`${API}/api/projects`);
    expect(res.status()).toBe(401);
  });
});
