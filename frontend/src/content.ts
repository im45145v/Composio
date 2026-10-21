import type { Audience, ClaimStatus, GuideDetail, GuideItem, GuideView } from "./types";

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

const SCHEMA_LEAK = /\b(this json|json object|managed_or_own|setup_path_value|setup_path)\b/i;

export function readableDecision(decision: string, summary: string): string {
  const trimmed = decision.replace(/\s*The passages support\b[\s\S]*$/i, "").trim();
  const chosen = trimmed || decision;
  if (SCHEMA_LEAK.test(chosen) && summary.trim() && !SCHEMA_LEAK.test(summary)) {
    return summary.trim();
  }
  return chosen;
}

export function isStated(claim: { value: string | null; status: ClaimStatus }): boolean {
  if (claim.status === "unknown") {
    return false;
  }
  const value = claim.value?.trim() ?? "";
  return value.length > 0 && value.toLowerCase() !== "unknown";
}

export function statedLabel(label: string, status: ClaimStatus): boolean {
  if (!isStated({ value: label, status })) {
    return false;
  }
  return label.trim().toLowerCase() !== "setup path";
}

export function showsWait(claim: { value: string | null; status: ClaimStatus }): boolean {
  if (!isStated(claim)) {
    return false;
  }
  return !/^unknown\b/i.test(claim.value ?? "");
}

export function callbackUrl(value: string | null | undefined): string | null {
  const match = value?.match(/https:\/\/[^\s)]+/);
  return match ? match[0].replace(/[.,]+$/, "") : null;
}

export function markFor(status: ClaimStatus): ClaimStatus | null {
  if (status === "inferred" || status === "uncertain") {
    return status;
  }
  return null;
}

export function readerNote(note: string | null | undefined): string | null {
  if (!note) {
    return null;
  }
  const cleaned = note
    .replace(/The retrieved pages do not state this in matching language\.?/gi, "")
    .replace(/No retrieved page (?:was cited for this claim|states this estimate)\.?/gi, "")
    .replace(/A citation did not match a retrieved page\.?/gi, "")
    .replace(/\s+/g, " ")
    .trim();
  return cleaned || null;
}

export function gapSentence(guide: GuideDetail): string | null {
  const missing: string[] = [];
  const pathKnown = statedLabel(guide.setup_path.label, guide.setup_path.status);
  const managedKnown = isStated(guide.composio.managed) || isStated(guide.composio.bring_your_own);
  if (!pathKnown && !managedKnown) {
    missing.push("which setup path the pages support");
  }
  if (!callbackUrl(guide.composio.redirect_uri.value)) {
    missing.push("a callback URL");
  }
  if (!isStated(guide.approval_wait)) {
    missing.push("how long a first connection waits");
  }
  if (missing.length === 0) {
    return null;
  }
  if (missing.length === 1) {
    return `The cited pages do not establish ${missing[0]}.`;
  }
  const last = missing[missing.length - 1];
  return `The cited pages do not establish ${missing.slice(0, -1).join(", ")} or ${last}.`;
}

export function leadFact(value: string | null | undefined, fallback: string, sentences = 2, max = 220): string {
  if (!value || value.trim().toLowerCase() === "unknown") {
    return fallback;
  }
  return opening(value, sentences, max);
}

export function opening(value: string | null | undefined, sentences = 2, max = 240): string {
  const text = claimText(value).replace(/\s+/g, " ").trim();
  const parts = text.split(/(?<=[.!?])\s+/).filter(Boolean);
  const joined = parts.slice(0, sentences).join(" ");
  return previewClaim(joined, max);
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

export function showsOnPath(audience: Audience, view: GuideView): boolean {
  if (audience === "shared") {
    return true;
  }
  return view === "decide" ? audience === "managed" : audience === "own";
}

export function isStale(isoDate: string, now = new Date()): boolean {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(isoDate);
  if (!match) {
    return false;
  }
  const checked = Date.UTC(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
  return now.getTime() - checked > 30 * 24 * 60 * 60 * 1000;
}

export function redirectChoices(value: string | null | undefined, note: string | null | undefined): string[] {
  const found: string[] = [];
  const text = `${value ?? ""}\n${note ?? ""}`;
  for (const match of text.matchAll(/https:\/\/[^\s)]+/g)) {
    const url = match[0].replace(/[.,]+$/, "");
    if (!found.includes(url)) {
      found.push(url);
    }
  }
  return found;
}

export function itemsFor(items: GuideItem[], view: GuideView): GuideItem[] {
  return items.filter((item) => showsOnPath(item.audience, view));
}

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
