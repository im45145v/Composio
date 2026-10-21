import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ApiError, fetchGuides } from "../api";
import { ClaimMark } from "../components/ClaimMark";
import { EmptyBlock, ErrorBlock, LoadingBlock } from "../components/StatusBlock";
import { SETUP_FILTERS, claimText, formatCheckedDate } from "../content";
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
      <h1 className="mt-2 max-w-3xl font-serif text-4xl leading-tight sm:text-5xl">OAuth setup, from the docs</h1>
      <p className="mt-4 max-w-2xl text-[15px] leading-7 text-muted">
        What it takes to configure GitHub, Google Calendar, and Slack, including whether Composio managed
        auth is enough. Nothing in this library was installed or approved while it was written. Documented
        means a cited source says it. Uncertain means the sources leave it open. Verified would mean this
        project ran it.
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
              className={`border px-3 py-1.5 text-sm ${selected ? "border-ink bg-ink text-paper" : "border-line-strong bg-raised text-ink"}`}
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
              filtered
                ? `Nothing in the library matches “${query || "that path"}”. The three seeded providers are GitHub, Google Calendar, and Slack.`
                : "The database has no guides. Start the API so it can load the seed data."
            }
            action={
              filtered ? (
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
                    className="block border-b border-line py-5 hover:bg-raised"
                  >
                    <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
                      <h2 className="font-serif text-2xl">{guide.name}</h2>
                      <p className="font-mono text-xs text-muted">Checked {formatCheckedDate(guide.last_checked)}</p>
                    </div>
                    <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">{guide.summary}</p>
                    <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2 text-sm">
                      <span>{claimText(guide.auth_type.value)}</span>
                      <span className="text-line-strong" aria-hidden="true">
                        /
                      </span>
                      <span>{guide.setup_path.label}</span>
                      <ClaimMark status={guide.setup_path.status} />
                      <span className="text-line-strong" aria-hidden="true">
                        /
                      </span>
                      <span>{claimText(guide.difficulty.value)}</span>
                      <ClaimMark status={guide.difficulty.status} />
                    </div>
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
