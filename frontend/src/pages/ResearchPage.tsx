import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { ApiError, researchEventsUrl, submitResearch } from "../api";
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
  | { status: "failed"; message: string; events: ResearchProgress[] }
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

export function ResearchPage() {
  const [appName, setAppName] = useState("");
  const [docsUrl, setDocsUrl] = useState("");
  const [state, setState] = useState<ResultState>({ status: "idle" });

  useEffect(() => {
    document.title = "Research an app · Field Guide";
  }, []);

  const runId = state.status === "running" ? state.runId : null;

  useEffect(() => {
    if (!runId) {
      return;
    }
    const source = new EventSource(researchEventsUrl(runId));
    const add = (kind: ResearchProgress["kind"]) => (event: MessageEvent<string>) => {
      const progress = parseProgress(kind, event);
      if (!progress) {
        return;
      }
      setState((current) => {
        if (current.status !== "running" || current.runId !== runId) {
          return current;
        }
        const events = current.events.some((item) => item.id === progress.id)
          ? current.events
          : [...current.events, progress];
        if (kind === "terminal") {
          source.close();
          if (progress.status === "completed" || progress.status === "existing_guide") {
            return {
              status: "completed",
              runId: current.runId,
              appName: current.appName,
              slug: progress.slug || "",
              events,
            };
          }
          return { status: "failed", message: progress.message, events };
        }
        return { ...current, events };
      });
    };
    source.addEventListener("stage", add("stage"));
    source.addEventListener("finding", add("finding"));
    source.addEventListener("terminal", add("terminal"));
    return () => source.close();
  }, [runId]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setState({ status: "submitting" });
    try {
      const result = await submitResearch(appName, docsUrl);
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

  const events = state.status === "running" || state.status === "completed" || state.status === "failed" ? state.events : [];

  return (
    <div className="grid gap-10 lg:grid-cols-[minmax(0,1fr)_18rem]">
      <div className="max-w-2xl">
        <p className="font-mono text-[11px] uppercase tracking-[0.16em] text-muted">Unfamiliar apps</p>
        <h1 className="mt-2 font-serif text-4xl leading-tight">Research an app</h1>
        <p className="mt-4 text-[15px] leading-7 text-muted">
          Search official documentation, read the pages, and save a guide when those pages support one. If a
          guide already exists, you get its address instead of a second copy. Nothing is marked verified,
          because this project does not run the provider's OAuth flow.
        </p>

        <form onSubmit={onSubmit} className="mt-8 space-y-5">
          <div>
            <label htmlFor="app-name" className="text-sm font-medium">
              App name or website
            </label>
            <input
              id="app-name"
              required
              value={appName}
              onChange={(event) => setAppName(event.target.value)}
              placeholder="Notion or https://developers.notion.com"
              className="mt-2 w-full border border-line-strong bg-raised px-3 py-3"
              autoComplete="off"
            />
          </div>
          <div>
            <label htmlFor="docs-url" className="text-sm font-medium">
              Documentation URL <span className="font-normal text-muted">(optional)</span>
            </label>
            <input
              id="docs-url"
              type="url"
              value={docsUrl}
              onChange={(event) => setDocsUrl(event.target.value)}
              placeholder="https://"
              className="mt-2 w-full border border-line-strong bg-raised px-3 py-3"
            />
          </div>
          <button
            type="submit"
            disabled={state.status === "submitting" || state.status === "running"}
            className="border border-ink bg-ink px-4 py-2 text-sm text-paper disabled:opacity-60"
          >
            {state.status === "submitting" || state.status === "running" ? "Researching" : "Research app"}
          </button>
        </form>

        <div className="mt-8">
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
                  ? `${state.appName} is already in the library, so the existing guide was left unchanged.`
                  : `${state.appName} now has a stable address from the pages that were read.`}
              </p>
              <Link
                to={`/guides/${state.slug}`}
                className="mt-5 inline-block border border-ink bg-ink px-3 py-2 text-sm text-paper"
              >
                Open the guide
              </Link>
            </div>
          ) : null}

          {state.status === "failed" || state.status === "error" ? (
            <div className="mt-4">
              <ErrorBlock
                title="Research didn't produce a guide"
                detail={state.message}
              />
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
