import { useEffect, useState, type FormEvent } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ApiError, fetchHealth, fetchResearchRun, researchEventsUrl, submitRecheck, submitResearch } from "../api";
import { ErrorBlock } from "../components/StatusBlock";
import { GUIDE_FIELDS } from "../content";
import type { ResearchProgress, ResearchUnavailable } from "../types";

type ResultState =
  | { status: "idle" }
  | { status: "submitting" }
  | { status: "unavailable"; result: ResearchUnavailable }
  | { status: "existing"; appName: string; slug: string }
  | { status: "running"; runId: string; appName: string; events: ResearchProgress[] }
  | { status: "completed"; runId: string; appName: string; slug: string; events: ResearchProgress[] }
  | { status: "candidate"; runId: string; appName: string; slug: string; events: ResearchProgress[] }
  | { status: "failed"; message: string; code: string | null; events: ResearchProgress[] }
  | { status: "error"; message: string };

function parseProgress(kind: ResearchProgress["kind"], event: MessageEvent<string>): ResearchProgress | null {
  try {
    const data = JSON.parse(event.data) as Record<string, unknown>;
    if (typeof data.message !== "string" || typeof data.stage !== "string") {
      return null;
    }
    return {
      id: Number(event.lastEventId || 0),
      kind,
      stage: data.stage,
      message: data.message,
      url: typeof data.url === "string" ? data.url : undefined,
      title: typeof data.title === "string" ? data.title : undefined,
      status: typeof data.status === "string" ? data.status : undefined,
      code: typeof data.code === "string" ? data.code : null,
      slug: typeof data.slug === "string" ? data.slug : null,
      guide_url: typeof data.guide_url === "string" ? data.guide_url : null,
      guide_created: data.guide_created === true,
    };
  } catch {
    return null;
  }
}

const STAGES = [
  { id: "identify", label: "Identify", match: ["accepted", "identifying"] },
  { id: "search", label: "Search", match: ["searching"] },
  { id: "read", label: "Read", match: ["reading"] },
  { id: "check", label: "Check", match: ["extracting", "validating"] },
  { id: "save", label: "Save", match: ["persisting", "completed", "candidate_ready", "existing_guide"] },
];

export function ResearchPage() {
  const [params] = useSearchParams();
  const prefill = params.get("app") ?? "";
  const recheck = params.get("recheck");
  const [appName, setAppName] = useState(prefill);
  const [docsUrl, setDocsUrl] = useState("");
  const [researchMode, setResearchMode] = useState<"configured" | "unavailable" | "unknown">("unknown");
  const [state, setState] = useState<ResultState>({ status: "idle" });

  useEffect(() => {
    if (prefill) {
      setAppName(prefill);
    }
  }, [prefill, recheck]);

  useEffect(() => {
    const controller = new AbortController();
    fetchHealth(controller.signal)
      .then(setResearchMode)
      .catch(() => setResearchMode("unavailable"));
    return () => controller.abort();
  }, []);

  useEffect(() => {
    document.title = "Research an app · Field Guide";
  }, []);

  const runId = state.status === "running" ? state.runId : null;

  useEffect(() => {
    if (!runId) {
      return;
    }
    const source = new EventSource(researchEventsUrl(runId));
    let closedByUs = false;
    const stop = () => {
      closedByUs = true;
      source.close();
    };
    const add = (kind: ResearchProgress["kind"]) => (event: MessageEvent<string>) => {
      const progress = parseProgress(kind, event);
      if (!progress) {
        return;
      }
      if (kind === "terminal") {
        stop();
      }
      setState((current) => {
        if (current.status !== "running" || current.runId !== runId) {
          return current;
        }
        const events = current.events.some((item) => item.id === progress.id)
          ? current.events
          : [...current.events, progress];
        if (kind === "terminal") {
          if (progress.status === "completed" || progress.status === "existing_guide") {
            return {
              status: "completed",
              runId: current.runId,
              appName: current.appName,
              slug: progress.slug || "",
              events,
            };
          }
          if (progress.status === "candidate_ready") {
            return {
              status: "candidate",
              runId: current.runId,
              appName: current.appName,
              slug: progress.slug || "",
              events,
            };
          }
          return { status: "failed", message: progress.message, code: progress.code ?? null, events };
        }
        return { ...current, events };
      });
    };
    source.addEventListener("stage", add("stage"));
    source.addEventListener("finding", add("finding"));
    source.addEventListener("terminal", add("terminal"));
    source.onerror = () => {
      if (closedByUs) {
        return;
      }
      void fetchResearchRun(runId)
        .then((run) => {
          setState((current) => {
            if (current.status !== "running" || current.runId !== runId) {
              return current;
            }
            if (run.status === "completed" || run.status === "existing_guide") {
              stop();
              return {
                status: "completed",
                runId,
                appName: current.appName,
                slug: run.guide_slug || "",
                events: current.events,
              };
            }
            if (run.status === "candidate_ready") {
              stop();
              return {
                status: "candidate",
                runId,
                appName: current.appName,
                slug: run.guide_slug || "",
                events: current.events,
              };
            }
            if (run.status === "failed" || run.status === "insufficient_evidence") {
              stop();
              return {
                status: "failed",
                message: run.message || "Research didn't produce a guide.",
                code: run.error_code,
                events: current.events,
              };
            }
            return current;
          });
        })
        .catch(() => {
          setState((current) => {
            if (current.status !== "running" || current.runId !== runId) {
              return current;
            }
            stop();
            return {
              status: "error",
              message:
                "The research progress stream disconnected, and the run status could not be loaded. If a guide was saved, open it from the library.",
            };
          });
        });
    };
    return () => stop();
  }, [runId]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setState({ status: "submitting" });
    try {
      const result = recheck ? await submitRecheck(recheck, docsUrl) : await submitResearch(appName, docsUrl);
      if (result.code === "research_unavailable") {
        setState({ status: "unavailable", result });
        return;
      }
      if (result.code === "guide_exists") {
        setState({ status: "existing", appName: result.app_name, slug: result.slug });
        return;
      }
      setState({ status: "running", runId: result.run_id, appName: result.app_name, events: [] });
    } catch (error: unknown) {
      const message =
        error instanceof ApiError ? error.message : "The research service could not be reached.";
      setState({ status: "error", message });
    }
  }

  const events =
    state.status === "running" || state.status === "completed" || state.status === "candidate" || state.status === "failed"
      ? state.events
      : [];
  const activeStage = events.reduce((best, event) => {
    const index = STAGES.findIndex((item) => item.match.includes(event.stage));
    return index > best ? index : best;
  }, -1);
  const kept = events.filter((item) => item.url && item.message.startsWith("Read "));
  const skipped = events.filter((item) => /skipped|could not read/i.test(item.message));
  const docsRequired = researchMode === "configured";

  return (
    <div className="grid gap-10 lg:grid-cols-[minmax(0,1fr)_18rem]">
      <div className="max-w-2xl">
        <p className="font-mono text-[11px] uppercase tracking-[0.16em] text-muted">
          {recheck ? "Recheck" : "Unfamiliar apps"}
        </p>
        <h1 className="mt-2 font-serif text-4xl leading-tight">
          {recheck ? `Recheck ${appName || "this guide"}` : "Research an app"}
        </h1>
        <p className="mt-4 text-[15px] leading-7 text-muted">
          {recheck
            ? "A recheck reads the docs again and stores a candidate. The live guide stays until you promote that candidate."
            : "Search official documentation, read the pages, and save a guide when those pages support one. An existing guide is left unchanged. Open it and recheck when you want a candidate instead."}
        </p>

        <form onSubmit={onSubmit} className="mt-8 space-y-5">
          <div>
            <label htmlFor="app-name" className="text-sm font-medium">
              App name or website
            </label>
            <input
              id="app-name"
              required
              readOnly={Boolean(recheck)}
              value={appName}
              onChange={(event) => setAppName(event.target.value)}
              placeholder="Notion or https://developers.notion.com"
              className="mt-2 w-full border border-line-strong bg-raised px-3 py-3 read-only:text-muted"
              autoComplete="off"
            />
          </div>
          <div>
            <label htmlFor="docs-url" className="text-sm font-medium">
              Documentation URL{" "}
              {docsRequired ? null : <span className="font-normal text-muted">(optional until research is connected)</span>}
            </label>
            <input
              id="docs-url"
              type="url"
              required={docsRequired || Boolean(recheck)}
              value={docsUrl}
              onChange={(event) => setDocsUrl(event.target.value)}
              placeholder="https://"
              className="mt-2 w-full border border-line-strong bg-raised px-3 py-3"
            />
            <p className="mt-2 text-sm leading-6 text-muted">
              Research reads at most four pages. A documentation URL keeps those pages on this app.
            </p>
          </div>
          <button
            type="submit"
            disabled={state.status === "submitting" || state.status === "running"}
            className="border border-ink bg-ink px-4 py-2 text-sm text-paper disabled:opacity-60"
          >
            {state.status === "submitting" || state.status === "running"
              ? "Researching"
              : recheck
                ? "Recheck guide"
                : "Research app"}
          </button>
        </form>

        <div className="mt-8">
          {events.length > 0 ? (
            <ol aria-label="Research stages" className="mb-4 flex flex-wrap gap-2">
              {STAGES.map((stage, index) => {
                const reached = activeStage >= index;
                return (
                  <li
                    key={stage.id}
                    className={`border px-3 py-1 font-mono text-[11px] uppercase tracking-[0.12em] ${reached ? "border-ink bg-ink text-paper" : "border-line text-muted"}`}
                  >
                    {stage.label}
                  </li>
                );
              })}
            </ol>
          ) : null}
          {kept.length > 0 || skipped.length > 0 ? (
            <div className="mb-4 grid gap-4 sm:grid-cols-2">
              <div>
                <h2 className="text-sm font-semibold">Pages kept</h2>
                <ul className="mt-2 space-y-2 text-sm">
                  {kept.map((item) => (
                    <li key={item.id}>
                      <a href={item.url} className="underline decoration-line-strong underline-offset-2">
                        {item.title || item.url}
                      </a>
                    </li>
                  ))}
                  {kept.length === 0 ? <li className="text-muted">None yet</li> : null}
                </ul>
              </div>
              <div>
                <h2 className="text-sm font-semibold">Pages skipped</h2>
                <ul className="mt-2 space-y-2 text-sm text-muted">
                  {skipped.map((item) => (
                    <li key={item.id}>{item.message}</li>
                  ))}
                  {skipped.length === 0 ? <li>None</li> : null}
                </ul>
              </div>
            </div>
          ) : null}
          {events.length > 0 ? (
            <ol aria-live="polite" className="space-y-3 border border-line bg-raised px-5 py-5">
              {events.map((item) => (
                <li key={item.id} className="border-t border-line pt-3 first:border-t-0 first:pt-0">
                  <p className="font-mono text-[11px] uppercase tracking-[0.12em] text-muted">{item.stage}</p>
                  <p className="mt-1 text-sm leading-6">{item.message}</p>
                  {item.url ? (
                    <a
                      href={item.url}
                      className="mt-1 block break-all text-sm underline decoration-line-strong underline-offset-2"
                    >
                      {item.title || item.url}
                    </a>
                  ) : null}
                </li>
              ))}
            </ol>
          ) : null}

          {state.status === "unavailable" ? (
            <div role="status" className="border border-line bg-raised px-5 py-6">
              <h2 className="font-serif text-2xl">Research is not connected</h2>
              <p className="mt-3 text-sm leading-6">{state.result.message}</p>
              <dl className="mt-4 space-y-2 text-sm">
                <div className="flex gap-3">
                  <dt className="w-28 text-muted">App</dt>
                  <dd>{state.result.app_name}</dd>
                </div>
                <div className="flex gap-3">
                  <dt className="w-28 text-muted">Docs URL</dt>
                  <dd className="break-all">{state.result.docs_url ?? "None provided"}</dd>
                </div>
                <div className="flex gap-3">
                  <dt className="w-28 text-muted">Guide created</dt>
                  <dd>No</dd>
                </div>
              </dl>
              <Link to="/" className="mt-5 inline-block text-sm underline decoration-line-strong underline-offset-2">
                Return to the library
              </Link>
            </div>
          ) : null}

          {state.status === "existing" || state.status === "completed" ? (
            <div role="status" className="mt-4 border border-line bg-raised px-5 py-6">
              <h2 className="font-serif text-2xl">
                {state.status === "existing" ? "This guide is already in the library" : "Guide saved"}
              </h2>
              <p className="mt-3 text-sm leading-6">
                {state.status === "existing"
                  ? `${state.appName} is already in the library, so this request left it unchanged. Recheck from the guide when you want a candidate.`
                  : `${state.appName} now has a stable address from the pages that were read.`}
              </p>
              {state.slug ? (
                <Link
                  to={`/guides/${state.slug}`}
                  className="mt-5 inline-block border border-ink bg-ink px-3 py-2 text-sm text-paper"
                >
                  Open the guide
                </Link>
              ) : null}
            </div>
          ) : null}

          {state.status === "candidate" ? (
            <div role="status" className="mt-4 border border-line bg-raised px-5 py-6">
              <h2 className="font-serif text-2xl">Candidate ready</h2>
              <p className="mt-3 text-sm leading-6">
                {state.appName} has a recheck waiting. The live guide was not changed.
              </p>
              {state.slug ? (
                <Link
                  to={`/guides/${state.slug}`}
                  className="mt-5 inline-block border border-ink bg-ink px-3 py-2 text-sm text-paper"
                >
                  Review the candidate
                </Link>
              ) : null}
            </div>
          ) : null}

          {state.status === "failed" || state.status === "error" ? (
            <div className="mt-4">
              <ErrorBlock title="Research didn't produce a guide" detail={state.message} />
              {state.status === "failed" && state.code === "insufficient_evidence" ? (
                <p className="mt-3 max-w-xl text-sm leading-6 text-muted">
                  Try a different documentation URL that names this app. Pages that do not discuss it are skipped,
                  and nothing is saved.
                </p>
              ) : null}
            </div>
          ) : null}
        </div>
      </div>

      <aside className="border border-line bg-raised p-5">
        <h2 className="text-sm font-semibold">What a finished guide has to answer</h2>
        <ol className="mt-3 space-y-2 text-sm leading-6">
          {GUIDE_FIELDS.map((field) => (
            <li key={field}>{field}</li>
          ))}
        </ol>
        <p className="mt-4 text-sm leading-6 text-muted">
          Documented means a retrieved page states it. Inferred is a reading of those pages. Unknown means the
          pages did not say. Verified is unused here.
        </p>
      </aside>
    </div>
  );
}
