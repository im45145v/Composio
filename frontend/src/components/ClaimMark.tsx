import { CLAIM_COPY } from "../content";
import type { ClaimStatus } from "../types";

const STYLES: Record<ClaimStatus, string> = {
  verified: "bg-pine-soft text-pine",
  documented: "bg-slate-soft text-slate",
  uncertain: "bg-clay-soft text-clay",
  inferred: "bg-olive-soft text-olive",
  unknown: "bg-line text-muted",
};

export function ClaimMark({ status }: { status: ClaimStatus }) {
  const copy = CLAIM_COPY[status];
  return (
    <abbr
      title={copy.description}
      className={`inline-flex items-center px-1.5 py-0.5 font-mono text-[11px] uppercase tracking-[0.08em] no-underline ${STYLES[status]}`}
    >
      <span className="sr-only">Claim status: </span>
      {copy.label}
    </abbr>
  );
}
