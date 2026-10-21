import { describe, expect, it } from "vitest";
import { formatCheckedDate, previewClaim } from "./content";

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
