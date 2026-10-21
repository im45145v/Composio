import type { GuideDetail, GuideListResponse, ResearchSubmission } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "/api";

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function readBody(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) {
    return null;
  }
  try {
    return JSON.parse(text) as unknown;
  } catch {
    return null;
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

export async function fetchGuides(
  query: string,
  path: string,
  signal: AbortSignal,
): Promise<GuideListResponse> {
  const params = new URLSearchParams();
  if (query) {
    params.set("q", query);
  }
  if (path) {
    params.set("path", path);
  }
  const suffix = params.size > 0 ? `?${params.toString()}` : "";
  const response = await fetch(`${API_BASE}/guides${suffix}`, { signal });
  if (!response.ok) {
    throw new ApiError(response.status, "The guide library could not be loaded.");
  }
  return (await readBody(response)) as GuideListResponse;
}

export async function fetchGuide(slug: string, signal: AbortSignal): Promise<GuideDetail | null> {
  const response = await fetch(`${API_BASE}/guides/${encodeURIComponent(slug)}`, { signal });
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new ApiError(response.status, "This guide could not be loaded.");
  }
  return (await readBody(response)) as GuideDetail;
}

export async function submitResearch(appName: string, docsUrl: string): Promise<ResearchSubmission> {
  const response = await fetch(`${API_BASE}/research-requests`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      app_name: appName,
      docs_url: docsUrl.trim() ? docsUrl.trim() : null,
    }),
  });
  const body = await readBody(response);
  if (isResearchSubmission(response.status, body)) {
    return body;
  }
  if (response.status === 422) {
    const detail = isRecord(body) && isRecord(body.detail) ? body.detail : null;
    const message =
      detail && typeof detail.message === "string"
        ? detail.message
        : "Enter an app name or public website. A documentation URL, if you include one, must be http or https.";
    throw new ApiError(422, message);
  }
  throw new ApiError(response.status, "The research service could not be reached.");
}

function isResearchSubmission(status: number, body: unknown): body is ResearchSubmission {
  if (!isRecord(body) || typeof body.code !== "string") {
    return false;
  }
  if (status === 503 && body.code === "research_unavailable" && body.guide_created === false) {
    return true;
  }
  if (status === 200 && body.code === "guide_exists" && typeof body.slug === "string") {
    return true;
  }
  if (
    (status === 202 || status === 200) &&
    (body.code === "research_started" || body.code === "research_in_progress") &&
    typeof body.run_id === "string"
  ) {
    return true;
  }
  return false;
}

export function researchEventsUrl(runId: string): string {
  return `${API_BASE}/research-runs/${encodeURIComponent(runId)}/events`;
}
