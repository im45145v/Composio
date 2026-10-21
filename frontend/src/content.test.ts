import { describe, expect, it } from "vitest";
import { formatCheckedDate } from "./content";

describe("formatCheckedDate", () => {
  it("formats an ISO date without shifting the calendar day", () => {
    expect(formatCheckedDate("2026-10-21")).toBe("21 Oct 2026");
  });

  it("leaves unexpected values readable", () => {
    expect(formatCheckedDate("October 2026")).toBe("October 2026");
  });
});
