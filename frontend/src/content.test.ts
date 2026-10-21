import { describe, expect, it } from "vitest";
import {
  formatCheckedDate,
  gapSentence,
  isStale,
  isStated,
  previewClaim,
  showsWait,
  readableDecision,
  readerNote,
  redirectChoices,
  showsOnPath,
} from "./content";
import type { GuideDetail } from "./types";

describe("formatCheckedDate", () => {
  it("formats an ISO date without shifting the calendar day", () => {
    expect(formatCheckedDate("2026-10-21")).toBe("21 Oct 2026");
  });

  it("leaves unexpected values readable", () => {
    expect(formatCheckedDate("October 2026")).toBe("October 2026");
  });
});

describe("previewClaim", () => {
  it("keeps a short claim and shortens a long one", () => {
    expect(previewClaim(null)).toBe("Unknown");
    expect(previewClaim("Three to five business days.")).toBe("Three to five business days.");
    const long = "Unknown. No fetched page gives a staff-review wait before anyone can authorize a new OAuth app, and the creation guide describes no review queue at all.";
    const preview = previewClaim(long, 80);
    expect(preview.endsWith("…")).toBe(true);
    expect(preview.length).toBeLessThanOrEqual(80);
    expect(preview.startsWith("Unknown. No fetched page")).toBe(true);
  });
});

describe("stated claims", () => {
  it("hides an empty unknown and keeps a documented sentence", () => {
    expect(isStated({ value: "Unknown", status: "unknown" })).toBe(false);
    expect(isStated({ value: null, status: "unknown" })).toBe(false);
    expect(isStated({ value: "OAuth 2.0", status: "documented" })).toBe(true);
    expect(showsWait({ value: "Unknown. No review queue is described.", status: "documented" })).toBe(false);
    expect(showsWait({ value: "No approval, unless the app is listed publicly.", status: "documented" })).toBe(true);
  });

  it("drops the checker’s rejection note and keeps a real condition", () => {
    expect(readerNote("The retrieved pages do not state this in matching language.")).toBeNull();
    expect(readerNote("GitHub recommends disabling wildcard matching if it is not needed.")).toContain("wildcard");
  });

  it("uses the summary when the decision names the schema", () => {
    expect(readableDecision("This JSON object outlines the OAuth setup.", "Calendly uses OAuth for its API.")).toBe(
      "Calendly uses OAuth for its API.",
    );
    expect(readableDecision("Use managed auth.", "A longer summary.")).toBe("Use managed auth.");
  });

  it("names only the gaps the pages left open", () => {
    const guide = {
      setup_path: { status: "unknown", label: "Own app unless managed auth is confirmed", value: "own_app_unless_confirmed", note: null },
      approval_wait: { value: null, status: "unknown", note: null },
      composio: {
        managed: { value: null, status: "unknown", note: null },
        bring_your_own: { value: null, status: "unknown", note: null },
        redirect_uri: { value: "https://backend.composio.dev/api/v3/toolkits/auth/callback", status: "documented", note: null },
      },
    } as GuideDetail;
    expect(gapSentence(guide)).toBe(
      "The cited pages do not establish which setup path the pages support or how long a first connection waits.",
    );
    guide.setup_path.status = "documented";
    guide.approval_wait = { value: "No review queue is described.", status: "documented", note: null };
    guide.composio.managed = { value: "Managed auth is listed.", status: "documented", note: null };
    expect(gapSentence(guide)).toBeNull();
  });
});

describe("path and freshness helpers", () => {
  it("keeps shared items on both paths and splits the rest", () => {
    expect(showsOnPath("shared", "decide")).toBe(true);
    expect(showsOnPath("shared", "register")).toBe(true);
    expect(showsOnPath("managed", "decide")).toBe(true);
    expect(showsOnPath("managed", "register")).toBe(false);
    expect(showsOnPath("own", "register")).toBe(true);
    expect(showsOnPath("own", "decide")).toBe(false);
  });

  it("treats a check older than 30 days as stale without shifting the calendar day", () => {
    expect(isStale("2026-09-01", new Date("2026-10-22T00:00:00Z"))).toBe(true);
    expect(isStale("2026-10-21", new Date("2026-10-22T00:00:00Z"))).toBe(false);
  });

  it("lists each redirect URL once", () => {
    expect(
      redirectChoices(
        "https://backend.composio.dev/api/v3/toolkits/auth/callback",
        "The older callback https://backend.composio.dev/api/v1/auth-apps/add remains supported.",
      ),
    ).toEqual([
      "https://backend.composio.dev/api/v3/toolkits/auth/callback",
      "https://backend.composio.dev/api/v1/auth-apps/add",
    ]);
  });
});
