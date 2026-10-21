import type { ClaimStatus } from "./types";

export const CLAIM_COPY: Record<ClaimStatus, { label: string; description: string }> = {
  verified: {
    label: "Verified",
    description: "Someone ran this step and recorded the result.",
  },
  documented: {
    label: "Documented",
    description: "The cited docs say this. This project did not run it.",
  },
  uncertain: {
    label: "Uncertain",
    description: "An estimate or an open question. Not a promise from the provider.",
  },
  inferred: {
    label: "Inferred",
    description: "A reading of the retrieved pages. Not a direct statement, and not a test.",
  },
  unknown: {
    label: "Unknown",
    description: "The retrieved pages do not establish this.",
  },
};

export function claimText(value: string | null | undefined): string {
  return value && value.trim() ? value : "Unknown";
}

export function previewClaim(value: string | null | undefined, max = 110): string {
  const text = claimText(value).replace(/\s+/g, " ").trim();
  if (text.length <= max) {
    return text;
  }
  return `${text.slice(0, max - 1).trimEnd()}…`;
}

export const SETUP_FILTERS: { value: string; label: string }[] = [
  { value: "", label: "All paths" },
  { value: "managed_or_own", label: "Managed option" },
  { value: "own_app_unless_confirmed", label: "Own app first" },
];

export const GUIDE_FIELDS = [
  "Authentication type",
  "Setup path",
  "Difficulty",
  "Active effort",
  "Approval wait",
  "Prerequisites",
  "Ordered steps",
  "Blockers",
  "Human actions",
  "Source URLs",
  "Confidence",
  "Last-checked date",
] as const;

export function formatCheckedDate(isoDate: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(isoDate);
  if (!match) {
    return isoDate;
  }
  const date = new Date(Date.UTC(Number(match[1]), Number(match[2]) - 1, Number(match[3])));
  return new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  }).format(date);
}
