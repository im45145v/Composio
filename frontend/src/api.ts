import type {
  CandidateView,
  GuideDetail,
  GuideListResponse,
  ResearchRunStatus,
  ResearchSubmission,
} from "./types";

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

export async function fetchHealth(signal?: AbortSignal): Promise<"configured" | "unavailable"> {
  const response = await fetch(`${API_BASE}/health`, { signal });
  const body = await readBody(response);
  if (!response.ok || !isRecord(body) || body.research !== "configured") {
    return "unavailable";
  }
  return "configured";
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

export async function submitRecheck(slug: string, docsUrl: string): Promise<ResearchSubmission> {
  const response = await fetch(`${API_BASE}/guides/${encodeURIComponent(slug)}/recheck`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ docs_url: docsUrl.trim() ? docsUrl.trim() : null }),
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
        : "Add a public documentation URL before rechecking.";
    throw new ApiError(422, message);
  }
  throw new ApiError(response.status, "The recheck could not be started.");
}

export async function fetchCandidate(slug: string, signal: AbortSignal): Promise<CandidateView | null> {
  const response = await fetch(`${API_BASE}/guides/${encodeURIComponent(slug)}/candidate`, { signal });
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new ApiError(response.status, "The recheck candidate could not be loaded.");
  }
  return (await readBody(response)) as CandidateView;
}

export async function promoteCandidate(slug: string): Promise<void> {
  const response = await fetch(`${API_BASE}/guides/${encodeURIComponent(slug)}/candidate/promote`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new ApiError(response.status, "The candidate could not replace the live guide.");
  }
}

export async function discardCandidate(slug: string): Promise<void> {
  const response = await fetch(`${API_BASE}/guides/${encodeURIComponent(slug)}/candidate/discard`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new ApiError(response.status, "The candidate could not be discarded.");
  }
}

export function researchEventsUrl(runId: string): string {
  return `${API_BASE}/research-runs/${encodeURIComponent(runId)}/events`;
}

export async function fetchResearchRun(runId: string): Promise<ResearchRunStatus> {
  const response = await fetch(`${API_BASE}/research-runs/${encodeURIComponent(runId)}`);
  const body = await readBody(response);
  if (!response.ok || !isRecord(body) || typeof body.status !== "string") {
    throw new ApiError(response.status, "The research run could not be loaded.");
  }
  return {
    id: typeof body.id === "string" ? body.id : runId,
    status: body.status,
    message: typeof body.message === "string" ? body.message : null,
    error_code: typeof body.error_code === "string" ? body.error_code : null,
    guide_slug: typeof body.guide_slug === "string" ? body.guide_slug : null,
    guide_created: body.guide_created === true,
  };
}
