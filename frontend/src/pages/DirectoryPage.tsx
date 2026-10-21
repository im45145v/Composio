import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ApiError, fetchGuides } from "../api";
import { ClaimMark } from "../components/ClaimMark";
import { EmptyBlock, ErrorBlock, LoadingBlock } from "../components/StatusBlock";
import { SETUP_FILTERS, formatCheckedDate, leadFact, markFor, previewClaim, readableDecision, statedLabel } from "../content";
import type { GuideSummary } from "../types";

type LoadState =
  | { status: "loading" }
  | { status: "ready"; guides: GuideSummary[]; count: number }
  | { status: "error"; message: string };

export function DirectoryPage() {
  const [params, setParams] = useSearchParams();
  const query = params.get("q") ?? "";
  const path = params.get("path") ?? "";
  const [draft, setDraft] = useState(query);
  const [seenQuery, setSeenQuery] = useState(query);
  const [reloadKey, setReloadKey] = useState(0);
  const [state, setState] = useState<LoadState>({ status: "loading" });
  if (query !== seenQuery) {
    setSeenQuery(query);
    setDraft(query);
  }

  useEffect(() => {
    document.title = "Library · Field Guide";
  }, []);

  useEffect(() => {
    const handle = window.setTimeout(() => {
      const trimmed = draft.trim();
      if (trimmed === query) {
        return;
      }
      setState({ status: "loading" });
      setParams(
        (current) => {
          const next = new URLSearchParams(current);
          if (trimmed) {
            next.set("q", trimmed);
          } else {
            next.delete("q");
          }
          return next;
        },
        { replace: true },
      );
    }, 200);
    return () => window.clearTimeout(handle);
  }, [draft, query, setParams]);

  useEffect(() => {
    const controller = new AbortController();
    fetchGuides(query, path, controller.signal)
      .then((body) => {
        setState({ status: "ready", guides: body.guides, count: body.count });
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }
        const message = error instanceof ApiError ? error.message : "The guide library could not be loaded.";
        setState({ status: "error", message });
      });
    return () => controller.abort();
  }, [query, path, reloadKey]);

  function setPath(nextPath: string) {
    setState({ status: "loading" });
    setParams((current) => {
      const next = new URLSearchParams(current);
      if (nextPath) {
        next.set("path", nextPath);
      } else {
        next.delete("path");
      }
      return next;
    });
  }

  const filtered = query.trim().length > 0 || path.length > 0;

  return (
    <div>
      <p className="font-mono text-[11px] uppercase tracking-[0.16em] text-muted">Integration library</p>
      <h1 className="mt-2 max-w-3xl font-serif text-4xl leading-tight sm:text-5xl">
        Can you connect it with managed auth?
      </h1>
      <p className="mt-4 max-w-2xl text-[15px] leading-7 text-muted">
        Each card leads with difficulty, hands-on work, and the approval wait. Open a guide for the
        steps, what can stall a launch, and the split between what was already collected and what you
        still have to do. Nothing here was installed or approved by this project.
      </p>

      <form
        role="search"
        className="mt-8"
        onSubmit={(event) => {
          event.preventDefault();
          const trimmed = draft.trim();
          setParams((current) => {
            const next = new URLSearchParams(current);
            if (trimmed) {
              next.set("q", trimmed);
            } else {
              next.delete("q");
            }
            return next;
          });
        }}
      >
        <label htmlFor="guide-search" className="text-sm font-medium">
          Search guides
        </label>
        <input
          id="guide-search"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="GitHub, Calendar, Slack"
          className="mt-2 w-full border border-line-strong bg-raised px-3 py-3 text-base sm:max-w-xl"
        />
      </form>

      <div className="mt-4 flex flex-wrap gap-2" role="group" aria-label="Setup path">
        {SETUP_FILTERS.map((filter) => {
          const selected = path === filter.value;
          return (
            <button
              key={filter.value || "all"}
              type="button"
              aria-pressed={selected}
              onClick={() => setPath(filter.value)}
              className={`border px-3.5 py-2 text-sm ${selected ? "border-ink bg-ink text-paper" : "border-line-strong bg-raised text-ink"}`}
            >
              {filter.label}
            </button>
          );
        })}
      </div>

      <div className="mt-8">
        {state.status === "loading" ? <LoadingBlock label="Loading guides" /> : null}
        {state.status === "error" ? (
          <ErrorBlock
            title="The library didn't load"
            detail={state.message}
            onRetry={() => {
              setState({ status: "loading" });
              setReloadKey((value) => value + 1);
            }}
          />
        ) : null}
        {state.status === "ready" && state.guides.length === 0 ? (
          <EmptyBlock
            title={filtered ? "No guides match" : "The library is empty"}
            detail={
              path === "own_app_unless_confirmed" && !query.trim()
                ? "No guide is currently marked own-app first."
                : filtered
                  ? `Nothing in the library matches “${query.trim() || "that path"}”.`
                  : "The database has no guides. Start the API so it can load the seed data."
            }
            action={
              query.trim() ? (
                <div className="flex flex-wrap gap-3">
                  <Link
                    to={`/research?app=${encodeURIComponent(query.trim())}`}
                    className="border border-ink bg-ink px-3 py-2 text-sm text-paper"
                  >
                    Research {query.trim()}
                  </Link>
                  <button
                    type="button"
                    className="border border-ink px-3 py-2 text-sm"
                    onClick={() => {
                      setDraft("");
                      setSeenQuery("");
                      setState({ status: "loading" });
                      setParams(new URLSearchParams());
                    }}
                  >
                    Clear search
                  </button>
                </div>
              ) : filtered ? (
                <button
                  type="button"
                  className="border border-ink px-3 py-2 text-sm"
                  onClick={() => {
                    setDraft("");
                    setSeenQuery("");
                    setState({ status: "loading" });
                    setParams(new URLSearchParams());
                  }}
                >
                  Clear filter
                </button>
              ) : null
            }
          />
        ) : null}
        {state.status === "ready" && state.guides.length > 0 ? (
          <div>
            <p className="font-mono text-xs text-muted" aria-live="polite">
              {state.count} {state.count === 1 ? "guide" : "guides"}
            </p>
            <ul className="mt-3 border-t border-line">
              {state.guides.map((guide) => (
                <li key={guide.slug}>
                  <Link
                    to={`/guides/${guide.slug}`}
                    className="block min-w-0 overflow-hidden border-b border-line py-6 hover:bg-raised"
                  >
                    <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
                      <h2 className="font-serif text-2xl">{guide.name}</h2>
                      <p className="font-mono text-xs text-muted">Checked {formatCheckedDate(guide.last_checked)}</p>
                    </div>
                    <p className="mt-2 max-w-3xl break-words text-[15px] leading-7">
                      {previewClaim(readableDecision(guide.decision, guide.summary), 220)}
                    </p>
                    <dl className="mt-4 grid min-w-0 gap-x-8 gap-y-4 text-sm leading-6 sm:grid-cols-3">
                      <div className="min-w-0 break-words">
                        <dt className="font-mono text-[11px] uppercase tracking-[0.12em] text-muted">Difficulty</dt>
                        <dd className="mt-1">
                          {leadFact(guide.difficulty.value, "The cited pages do not rate how hard this is.", 1, 120)}
                          {markFor(guide.difficulty.status) ? (
                            <span className="ml-2">
                              <ClaimMark status={markFor(guide.difficulty.status) ?? "uncertain"} />
                            </span>
                          ) : null}
                        </dd>
                      </div>
                      <div className="min-w-0 break-words">
                        <dt className="font-mono text-[11px] uppercase tracking-[0.12em] text-muted">Hands-on</dt>
                        <dd className="mt-1">
                          {leadFact(guide.active_effort.value, "The cited pages do not say how long the steps take.", 2, 180)}
                        </dd>
                      </div>
                      <div className="min-w-0 break-words">
                        <dt className="font-mono text-[11px] uppercase tracking-[0.12em] text-muted">Approval wait</dt>
                        <dd className="mt-1">
                          {leadFact(
                            guide.approval_wait.value,
                            "The cited pages do not establish how long a first connection waits.",
                            2,
                            220,
                          )}
                        </dd>
                      </div>
                    </dl>
                    {statedLabel(guide.setup_path.label, guide.setup_path.status) ? (
                      <p className="mt-3 text-sm text-muted">{guide.setup_path.label}</p>
                    ) : null}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </div>
    </div>
  );
}
