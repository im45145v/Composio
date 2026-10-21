import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { ApiError, discardCandidate, fetchCandidate, fetchGuide, promoteCandidate } from "../api";
import { ClaimMark } from "../components/ClaimMark";
import { ErrorBlock, LoadingBlock } from "../components/StatusBlock";
import {
  callbackUrl,
  claimText,
  formatCheckedDate,
  gapSentence,
  isStale,
  isStated,
  itemsFor,
  markFor,
  readableDecision,
  readerNote,
  redirectChoices,
  statedLabel,
} from "../content";
import type { CandidateView, Claim, GuideDetail, GuideItem, GuideView } from "../types";

type LoadState =
  | { status: "loading" }
  | { status: "missing" }
  | { status: "ready"; guide: GuideDetail }
  | { status: "error"; message: string };

export function GuidePage() {
  const { slug = "" } = useParams();
  return <GuideDocument key={slug} slug={slug} />;
}

function GuideDocument({ slug }: { slug: string }) {
  const [params, setParams] = useSearchParams();
  const view: GuideView = params.get("view") === "register" ? "register" : "decide";
  const [reloadKey, setReloadKey] = useState(0);
  const [state, setState] = useState<LoadState>({ status: "loading" });
  const [candidate, setCandidate] = useState<CandidateView | null>(null);
  const [candidateError, setCandidateError] = useState<string | null>(null);
  const [promoting, setPromoting] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    fetchGuide(slug, controller.signal)
      .then((guide) => {
        if (!guide) {
          document.title = "Guide not found · Field Guide";
          setState({ status: "missing" });
          return;
        }
        document.title = `${guide.name} · Field Guide`;
        setState({ status: "ready", guide });
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }
        document.title = "Guide unavailable · Field Guide";
        const message = error instanceof ApiError ? error.message : "This guide could not be loaded.";
        setState({ status: "error", message });
      });
    return () => controller.abort();
  }, [slug, reloadKey]);

  const pendingId = state.status === "ready" ? state.guide.pending_candidate?.id : null;

  useEffect(() => {
    if (!pendingId) {
      setCandidate(null);
      return;
    }
    const controller = new AbortController();
    fetchCandidate(slug, controller.signal)
      .then((body) => setCandidate(body))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }
        setCandidateError(error instanceof ApiError ? error.message : "The recheck could not be loaded.");
      });
    return () => controller.abort();
  }, [pendingId, slug]);

  function setView(next: GuideView) {
    setParams((current) => {
      const paramsNext = new URLSearchParams(current);
      if (next === "register") {
        paramsNext.set("view", "register");
      } else {
        paramsNext.delete("view");
      }
      return paramsNext;
    });
  }

  if (state.status === "loading") {
    return <LoadingBlock label="Loading guide" />;
  }
  if (state.status === "error") {
    return (
      <ErrorBlock
        title="This guide didn't load"
        detail={state.message}
        onRetry={() => {
          setState({ status: "loading" });
          setReloadKey((value) => value + 1);
        }}
      />
    );
  }
  if (state.status === "missing") {
    return (
      <div className="max-w-xl">
        <p className="font-mono text-[11px] uppercase tracking-[0.16em] text-muted">Not found</p>
        <h1 className="mt-2 font-serif text-4xl">No guide for this address</h1>
        <p className="mt-3 text-sm leading-6 text-muted">
          <span className="font-mono text-ink">{slug || "that slug"}</span> is not in the library. Research saves a
          guide only when the pages it reads support one.
        </p>
        <div className="mt-5 flex flex-wrap gap-3">
          <Link to="/" className="border border-ink bg-ink px-3 py-2 text-sm text-paper">
            Back to the library
          </Link>
          <Link
            to={`/research?app=${encodeURIComponent(slug)}`}
            className="border border-line-strong bg-raised px-3 py-2 text-sm"
          >
            Research this name
          </Link>
        </div>
      </div>
    );
  }

  const { guide } = state;
  const shareUrl = `${window.location.origin}/guides/${guide.slug}`;
  const stale = isStale(guide.last_checked);
  const decision = readableDecision(guide.composio.decision, guide.summary);
  const recheckHref = `/research?recheck=${encodeURIComponent(guide.slug)}&app=${encodeURIComponent(guide.name)}`;

  async function onPromote() {
    setPromoting(true);
    setCandidateError(null);
    try {
      await promoteCandidate(guide.slug);
      setCandidate(null);
      setReloadKey((value) => value + 1);
    } catch (error: unknown) {
      setCandidateError(error instanceof ApiError ? error.message : "The candidate could not replace the live guide.");
    } finally {
      setPromoting(false);
    }
  }

  async function onDiscard() {
    setPromoting(true);
    setCandidateError(null);
    try {
      await discardCandidate(guide.slug);
      setCandidate(null);
      setReloadKey((value) => value + 1);
    } catch (error: unknown) {
      setCandidateError(error instanceof ApiError ? error.message : "The candidate could not be discarded.");
    } finally {
      setPromoting(false);
    }
  }

  return (
    <div className="grid gap-10 lg:grid-cols-[minmax(0,1fr)_17.5rem] lg:items-start">
      <article>
        <p className="font-mono text-[11px] uppercase tracking-[0.16em] text-muted">
          {guide.origin === "researched" ? "Researched guide" : "Editorial guide"} · {guide.slug}
        </p>
        <h1 className="mt-2 font-serif text-4xl leading-tight sm:text-5xl">{guide.name}</h1>
        <p className="mt-4 max-w-[68ch] font-serif text-xl leading-8">{decision}</p>

        <Headline guide={guide} />
        <Handoff />

        <div className="mt-6 flex flex-wrap gap-2" role="group" aria-label="Guide path">
          <PathButton selected={view === "decide"} onClick={() => setView("decide")}>
            Managed auth
          </PathButton>
          <PathButton selected={view === "register"} onClick={() => setView("register")}>
            Register an app
          </PathButton>
        </div>

        {candidate ? (
          <div className="mt-6 border border-line bg-raised p-5">
            <h2 className="font-serif text-2xl">A recheck is waiting</h2>
            <p className="mt-2 max-w-[68ch] text-sm leading-6">
              The live guide was not changed. Promote replaces it with the candidate. Discard leaves this guide as it is.
            </p>
            <p className="mt-3 text-sm leading-6">
              {candidate.changed_fields.length > 0
                ? `Different: ${candidate.changed_fields.join(", ")}.`
                : "The decision, redirect, and approval wait match. Steps may still differ."}
            </p>
            {candidate.changed_fields.includes("Decision") ? (
              <p className="mt-3 max-w-[68ch] text-sm leading-6 text-muted">{candidate.guide.composio.decision}</p>
            ) : null}
            <div className="mt-4 flex flex-wrap gap-3">
              <button
                type="button"
                disabled={promoting}
                onClick={() => void onPromote()}
                className="border border-ink bg-ink px-3 py-2 text-sm text-paper disabled:opacity-60"
              >
                Promote candidate
              </button>
              <button
                type="button"
                disabled={promoting}
                onClick={() => void onDiscard()}
                className="border border-line-strong bg-paper px-3 py-2 text-sm disabled:opacity-60"
              >
                Discard
              </button>
            </div>
          </div>
        ) : null}
        {candidateError ? <p className="mt-3 text-sm text-danger">{candidateError}</p> : null}

        {view === "decide" ? (
          <DecideBody guide={guide} onRegister={() => setView("register")} />
        ) : (
          <RegisterBody guide={guide} />
        )}
      </article>

      <aside className="border border-line bg-raised p-5 lg:sticky lg:top-20">
        <h2 className="text-sm font-semibold">Share this guide</h2>
        <label htmlFor="share-url" className="sr-only">
          Shareable guide URL
        </label>
        <input
          id="share-url"
          readOnly
          value={shareUrl}
          onFocus={(event) => event.currentTarget.select()}
          className="mt-2 w-full border border-line bg-paper px-2 py-2 font-mono text-xs"
        />
        <p className="mt-6 text-sm font-semibold">Sources</p>
        <ol className="mt-3 space-y-3">
          {guide.sources.map((source) => (
            <li key={source.url} className="text-sm leading-5">
              <a href={source.url} className="underline decoration-line-strong underline-offset-2">
                {source.title}
              </a>
              <span className="mt-1 block font-mono text-[11px] text-muted">
                {source.publisher} · {formatCheckedDate(source.accessed_on)}
              </span>
            </li>
          ))}
        </ol>
        <p className="mt-6 text-sm leading-6 text-muted">
          A mark appears only on an estimate or a reading. Everything else is a statement from the sources below.
          This project did not run the OAuth flow.
        </p>
        <p className="mt-4 font-mono text-[11px] text-muted">
          Last checked {formatCheckedDate(guide.last_checked)}
          {stale ? " · older than 30 days" : ""}
        </p>
        <Link to={recheckHref} className="mt-3 inline-block text-sm underline decoration-line-strong underline-offset-2">
          {stale ? "Recheck these docs" : "Recheck this guide"}
        </Link>
      </aside>
    </div>
  );
}

function PathButton({
  selected,
  onClick,
  children,
}: {
  selected: boolean;
  onClick: () => void;
  children: string;
}) {
  return (
    <button
      type="button"
      aria-pressed={selected}
      onClick={onClick}
      className={`border px-3 py-1.5 text-sm ${selected ? "border-ink bg-ink text-paper" : "border-line-strong bg-raised text-ink"}`}
    >
      {children}
    </button>
  );
}

function headlineClaim(claim: Claim, fallback: string): Claim {
  if (isStated(claim)) {
    return claim;
  }
  return { value: fallback, status: "unknown", note: claim.note, source_url: claim.source_url };
}

function Headline({ guide }: { guide: GuideDetail }) {
  const setup = {
    value: guide.setup_path.label,
    status: guide.setup_path.status,
    note: guide.setup_path.note,
    source_url: guide.setup_path.source_url,
  };
  const facts = [
    {
      label: "Difficulty",
      claim: headlineClaim(guide.difficulty, "The cited pages do not rate how hard this is."),
    },
    {
      label: "Hands-on work",
      claim: headlineClaim(guide.active_effort, "The cited pages do not say how long the steps take."),
    },
    {
      label: "Wait for a first connection",
      claim: headlineClaim(guide.approval_wait, "The cited pages do not establish how long a first connection waits."),
    },
    statedLabel(guide.setup_path.label, guide.setup_path.status) ? { label: "Setup path", claim: setup } : null,
  ].filter((fact) => fact !== null);
  const gap = gapSentence(guide);
  return (
    <>
      <dl className="mt-8 grid grid-cols-1 gap-px border border-line bg-line sm:grid-cols-2">
        {facts.map((fact) => (
          <Meta key={fact.label} label={fact.label} claim={fact.claim} />
        ))}
      </dl>
      {gap ? <p className="mt-4 max-w-[68ch] text-sm leading-6 text-muted">{gap}</p> : null}
    </>
  );
}

function Handoff() {
  return (
    <section className="mt-8 grid gap-px border border-line bg-line sm:grid-cols-2" aria-label="Who does what">
      <div className="bg-raised p-5">
        <h2 className="font-serif text-2xl">Already collected</h2>
        <p className="mt-2 text-sm leading-6">
          The sources, the redirect URI when a page printed one, the ordered steps, and the checklist. No OAuth app
          was created, no client secret was stored, and no review was submitted.
        </p>
      </div>
      <div className="bg-raised p-5">
        <h2 className="font-serif text-2xl">You take over</h2>
        <p className="mt-2 text-sm leading-6">
          Create the app in the provider console, keep the client secret, and submit verification or Marketplace
          review when you need a public listing. On managed auth, a person still has to approve the consent screen.
        </p>
      </div>
    </section>
  );
}

function DecideBody({ guide, onRegister }: { guide: GuideDetail; onRegister: () => void }) {
  const steps = itemsFor(guide.steps, "decide");
  const blockers = itemsFor(guide.blockers, "decide");
  const humans = itemsFor(guide.human_actions, "decide");
  return (
    <>
      {isStated(guide.composio.managed) ? (
        <section className="mt-10 border border-line bg-raised p-5 sm:p-6">
          <h2 className="font-serif text-2xl">Managed auth</h2>
          <ClaimBlock title="What you use" claim={guide.composio.managed} />
          <div className="mt-6">
            <button type="button" onClick={onRegister} className="border border-ink px-3 py-2 text-sm">
              I need my own app
            </button>
          </div>
        </section>
      ) : (
        <div className="mt-8">
          <button type="button" onClick={onRegister} className="border border-ink px-3 py-2 text-sm">
            Register an app instead
          </button>
        </div>
      )}

      {steps.length > 0 ? (
        <StepList title="Setup" intro="In the order the cited pages describe." items={steps} />
      ) : null}
      {blockers.length > 0 ? (
        <ItemSection title="What can stall a first connection" intro="These apply before anyone registers an app." items={blockers} />
      ) : null}
      {humans.length > 0 ? (
        <Checklist slug={guide.slug} kind="human_action" title="Needs a person" items={humans} />
      ) : null}
    </>
  );
}

function RegisterBody({ guide }: { guide: GuideDetail }) {
  const prerequisites = itemsFor(guide.prerequisites, "register");
  const steps = itemsFor(guide.steps, "register");
  const blockers = itemsFor(guide.blockers, "register");
  const humans = itemsFor(guide.human_actions, "register");
  const redirects = redirectChoices(guide.composio.redirect_uri.value, guide.composio.redirect_uri.note);
  const primary = callbackUrl(guide.composio.redirect_uri.value);
  return (
    <>
      <section className="mt-8 border border-line bg-raised p-5 sm:p-6">
        <h2 className="font-serif text-2xl">Your own OAuth app</h2>
        {isStated(guide.composio.bring_your_own) ? (
          <ClaimBlock title="When this path applies" claim={guide.composio.bring_your_own} />
        ) : (
          <p className="mt-3 max-w-[68ch] text-sm leading-6 text-muted">
            The steps below are what the cited pages say about registering an app.
          </p>
        )}
        <div className="mt-6 border-t border-line pt-4">
          <h3 className="text-sm font-semibold">Redirect URI</h3>
          {primary ? (
            <CopyValue value={primary} />
          ) : (
            <p className="mt-2 text-sm leading-6 text-muted">The cited pages do not print a callback URL.</p>
          )}
          {redirects.filter((url) => url !== primary).length > 0 ? (
            <div className="mt-4">
              <p className="text-sm leading-6 text-muted">
                Pages also name another callback. The provider and the auth config have to use the same one.
              </p>
              <ul className="mt-2 space-y-2">
                {redirects
                  .filter((url) => url !== primary)
                  .map((url) => (
                    <li key={url}>
                      <CopyValue value={url} />
                    </li>
                  ))}
              </ul>
            </div>
          ) : null}
          {readerNote(guide.composio.redirect_uri.note) ? (
            <p className="mt-3 max-w-[68ch] text-sm leading-6 text-muted">{readerNote(guide.composio.redirect_uri.note)}</p>
          ) : null}
        </div>
      </section>
      {prerequisites.length > 0 ? (
        <ItemSection title="Prerequisites" intro="Have these before opening the provider's form." items={prerequisites} />
      ) : null}
      {steps.length > 0 ? (
        <StepList title="Steps" intro="In the order the cited pages describe." items={steps} />
      ) : null}
      {blockers.length > 0 ? (
        <ItemSection
          title="Blockers on this path"
          intro="These apply when you register your own app. A Marketplace or verification wait stays here."
          items={blockers}
        />
      ) : null}
      {humans.length > 0 ? (
        <Checklist slug={guide.slug} kind="human_action" title="Needs a person" items={humans} />
      ) : null}
    </>
  );
}

function Checklist({
  slug,
  kind,
  title,
  items,
}: {
  slug: string;
  kind: string;
  title: string;
  items: GuideItem[];
}) {
  const storageKey = `field-guide-checks:${slug}`;
  const [checked, setChecked] = useState<string[]>(() => readChecks(storageKey));

  function toggle(id: string) {
    setChecked((current) => {
      const next = current.includes(id) ? current.filter((item) => item !== id) : [...current, id];
      window.localStorage.setItem(storageKey, JSON.stringify(next));
      return next;
    });
  }

  return (
    <section className="mt-10">
      <h2 className="font-serif text-2xl">{title}</h2>
      <p className="mt-2 max-w-[68ch] text-sm leading-6 text-muted">
        Saved in this browser. Checking an item records that you did it. It does not record a test of the OAuth flow.
      </p>
      <ul className="mt-5 space-y-5">
        {items.map((item) => {
          const id = `${kind}:${item.position}`;
          const done = checked.includes(id);
          return (
            <li key={id} className="border-t border-line pt-4">
              <label className="flex items-start gap-3">
                <input
                  type="checkbox"
                  className="mt-1"
                  checked={done}
                  onChange={() => toggle(id)}
                />
                <span>
                  <ItemBody item={item} />
                </span>
              </label>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

function readChecks(key: string): string[] {
  try {
    const raw = window.localStorage.getItem(key);
    const parsed = raw ? (JSON.parse(raw) as unknown) : [];
    return Array.isArray(parsed) ? parsed.filter((item) => typeof item === "string") : [];
  } catch {
    return [];
  }
}

function CopyValue({ value }: { value: string }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  }

  return (
    <div className="mt-2 flex flex-wrap items-center gap-3">
      <code className="break-all font-mono text-sm">{value}</code>
      <button type="button" onClick={() => void copy()} className="border border-ink px-2 py-1 text-sm">
        {copied ? "Copied" : "Copy"}
      </button>
    </div>
  );
}

function Meta({ label, claim }: { label: string; claim: Claim }) {
  const note = readerNote(claim.note);
  const mark = markFor(claim.status);
  return (
    <div className="bg-raised px-4 py-4">
      <dt className="font-mono text-[11px] uppercase tracking-[0.12em] text-muted">{label}</dt>
      <dd className="mt-2 text-sm leading-6">
        <span>{claimText(claim.value)}</span>
        {mark ? (
          <span className="mt-2 block">
            <ClaimMark status={mark} />
          </span>
        ) : null}
        {note ? <span className="mt-2 block text-muted">{note}</span> : null}
        <SourceLink url={claim.source_url} />
      </dd>
    </div>
  );
}

function ClaimBlock({ title, claim }: { title: string; claim: Claim }) {
  const note = readerNote(claim.note);
  const mark = markFor(claim.status);
  return (
    <div className="mt-4">
      <div className="flex flex-wrap items-center gap-2">
        <h3 className="text-sm font-semibold">{title}</h3>
        {mark ? <ClaimMark status={mark} /> : null}
      </div>
      <p className="mt-2 text-sm leading-6">{claimText(claim.value)}</p>
      {note ? <p className="mt-2 text-sm leading-6 text-muted">{note}</p> : null}
      <SourceLink url={claim.source_url} />
    </div>
  );
}

function StepList({ title, intro, items }: { title: string; intro: string; items: GuideItem[] }) {
  return (
    <section className="mt-10">
      <h2 className="font-serif text-2xl">{title}</h2>
      <p className="mt-2 max-w-[68ch] text-sm leading-6 text-muted">{intro}</p>
      <ol className="mt-6 space-y-8">
        {items.map((step, index) => (
          <li key={step.position} className="grid grid-cols-[2.5rem_minmax(0,1fr)] gap-3">
            <span className="pt-1 font-mono text-sm text-muted">{String(index + 1).padStart(2, "0")}</span>
            <ItemBody item={step} />
          </li>
        ))}
      </ol>
    </section>
  );
}

function ItemSection({ title, intro, items }: { title: string; intro: string; items: GuideItem[] }) {
  return (
    <section className="mt-10">
      <h2 className="font-serif text-2xl">{title}</h2>
      <p className="mt-2 max-w-[68ch] text-sm leading-6 text-muted">{intro}</p>
      <ol className="mt-5 space-y-5">
        {items.map((item) => (
          <li key={item.position} className="border-t border-line pt-4">
            <ItemBody item={item} />
          </li>
        ))}
      </ol>
    </section>
  );
}

function ItemBody({ item }: { item: GuideItem }) {
  const note = readerNote(item.note);
  const mark = markFor(item.status);
  return (
    <div>
      <div className="flex flex-wrap items-center gap-2">
        <h3 className="text-base font-semibold">{item.title.replace(/\.$/, "")}</h3>
        {mark ? <ClaimMark status={mark} /> : null}
      </div>
      <p className="mt-2 max-w-[68ch] text-[15px] leading-7">{item.body}</p>
      {note ? <p className="mt-2 max-w-[68ch] text-sm leading-6 text-muted">{note}</p> : null}
      <SourceLink url={item.source_url} />
    </div>
  );
}

function SourceLink({ url }: { url?: string | null }) {
  if (!url) {
    return null;
  }
  let label = url;
  try {
    label = new URL(url).hostname.replace(/^www\./, "");
  } catch {
    label = url;
  }
  return (
    <a href={url} title={url} className="mt-2 inline-block text-sm underline decoration-line-strong underline-offset-2">
      {label}
    </a>
  );
}
