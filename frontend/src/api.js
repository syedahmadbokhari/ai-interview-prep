// Thin client for the Phase 2 FastAPI backend.
// Base URL is configurable via VITE_API_BASE_URL; the default "/api"
// relies on the dev-server/nginx proxy so the app is same-origin.

const BASE = import.meta.env.VITE_API_BASE_URL || "/api";

export class ApiError extends Error {
  constructor(status, detail) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

async function request(path, options = {}) {
  let resp;
  try {
    resp = await fetch(`${BASE}${path}`, options);
  } catch {
    throw new ApiError(0, "Cannot reach the API — is the backend running?");
  }
  let body = null;
  try {
    body = await resp.json();
  } catch {
    // non-JSON error body; fall through with generic detail
  }
  if (!resp.ok) {
    const detail =
      (body && (typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail))) ||
      `Request failed (${resp.status})`;
    throw new ApiError(resp.status, detail);
  }
  return body;
}

export function login(username, password) {
  return request("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
}

export function ask(token, question) {
  return request("/ask", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ question }),
  });
}
