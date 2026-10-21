export type ClaimStatus = "verified" | "documented" | "uncertain" | "inferred" | "unknown";

export type SetupPathValue = "managed_or_own" | "own_app_unless_confirmed";

export interface Claim {
  value: string | null;
  status: ClaimStatus;
  note: string | null;
  source_url?: string | null;
}

export interface SetupPath {
  value: SetupPathValue;
  label: string;
  status: ClaimStatus;
  note: string | null;
  source_url?: string | null;
}

export interface GuideItem {
  position: number;
  title: string;
  body: string;
  status: ClaimStatus;
  note: string | null;
  source_url?: string | null;
}

export interface Source {
  title: string;
  url: string;
  publisher: string;
  accessed_on: string;
}

export interface ComposioSection {
  decision: string;
  managed: Claim;
  bring_your_own: Claim;
  redirect_uri: Claim;
}

export interface GuideSummary {
  slug: string;
  name: string;
  summary: string;
  auth_type: Claim;
  setup_path: SetupPath;
  difficulty: Claim;
  active_effort: Claim;
  approval_wait: Claim;
  confidence: Claim;
  tested: boolean;
  last_checked: string;
}

export interface GuideDetail extends GuideSummary {
  execution_note: string;
  composio: ComposioSection;
  prerequisites: GuideItem[];
  steps: GuideItem[];
  blockers: GuideItem[];
  human_actions: GuideItem[];
  sources: Source[];
}

export interface GuideListResponse {
  guides: GuideSummary[];
  count: number;
}

export interface ResearchUnavailable {
  code: "research_unavailable";
  message: string;
  app_name: string;
  docs_url: string | null;
  guide_created: false;
}

export interface GuideExists {
  code: "guide_exists";
  app_name: string;
  slug: string;
  guide_url: string;
  guide_created: false;
}

export interface ResearchAccepted {
  code: "research_started" | "research_in_progress";
  run_id: string;
  app_name: string;
  events_url: string;
  status: string;
  guide_created: boolean;
  guide_url: string | null;
  slug: string | null;
}

export type ResearchSubmission = ResearchUnavailable | GuideExists | ResearchAccepted;

export interface ResearchRunStatus {
  id: string;
  status: string;
  message: string | null;
  error_code: string | null;
  guide_slug: string | null;
  guide_created: boolean;
}

export interface ResearchProgress {
  id: number;
  kind: "stage" | "finding" | "terminal";
  stage: string;
  message: string;
  url?: string;
  title?: string;
  status?: string;
  code?: string | null;
  slug?: string | null;
  guide_url?: string | null;
  guide_created?: boolean;
}
