import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ApiError, fetchGuide } from "../api";
import { ClaimMark } from "../components/ClaimMark";
import { ErrorBlock, LoadingBlock } from "../components/StatusBlock";
import { CLAIM_COPY, claimText, formatCheckedDate } from "../content";
import type { Claim, ClaimStatus, GuideDetail, GuideItem } from "../types";

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
  const [reloadKey, setReloadKey] = useState(0);
  const [state, setState] = useState<LoadState>({ status: "loading" });

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
          <Link to="/research" className="border border-line-strong bg-raised px-3 py-2 text-sm">
            Research an app
          </Link>
        </div>
      </div>
    );
  }

  const { guide } = state;
  const shareUrl = `${window.location.origin}/guides/${guide.slug}`;

  return (
    <div className="grid gap-10 lg:grid-cols-[minmax(0,1fr)_17.5rem] lg:items-start">
      <article>
        <p className="font-mono text-[11px] uppercase tracking-[0.16em] text-muted">{guide.slug}</p>
        <h1 className="mt-2 font-serif text-4xl leading-tight sm:text-5xl">{guide.name}</h1>
        <p className="mt-4 max-w-[68ch] font-serif text-xl leading-8">{guide.summary}</p>
        <p className="mt-5 max-w-[68ch] border-l-2 border-pine pl-4 text-sm leading-6">{guide.execution_note}</p>

        <dl className="mt-8 grid grid-cols-1 gap-px border border-line bg-line sm:grid-cols-2">
          <Meta label="Authentication" claim={guide.auth_type} />
          <Meta
            label="Setup path"
            claim={{
              value: guide.setup_path.label,
              status: guide.setup_path.status,
              note: guide.setup_path.note,
              source_url: guide.setup_path.source_url,
            }}
          />
          <Meta label="Difficulty" claim={guide.difficulty} />
          <Meta label="Active effort" claim={guide.active_effort} />
          <Meta label="Approval wait" claim={guide.approval_wait} />
          <Meta label="Confidence" claim={guide.confidence} />
        </dl>

        <section className="mt-10 border border-line bg-raised p-5 sm:p-6">
          <h2 className="font-serif text-2xl">Composio path</h2>
          <p className="mt-3 max-w-[68ch] text-[15px] leading-7">{guide.composio.decision}</p>
          <div className="mt-6 grid gap-6 md:grid-cols-2">
            <ClaimBlock title="Managed auth" claim={guide.composio.managed} />
            <ClaimBlock title="Your own OAuth app" claim={guide.composio.bring_your_own} />
          </div>
          <div className="mt-6 border-t border-line pt-4">
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="text-sm font-semibold">Redirect URI</h3>
              <ClaimMark status={guide.composio.redirect_uri.status} />
            </div>
            <p className="mt-2 break-all font-mono text-sm">{claimText(guide.composio.redirect_uri.value)}</p>
            {guide.composio.redirect_uri.note ? (
              <p className="mt-2 max-w-[68ch] text-sm leading-6 text-muted">{guide.composio.redirect_uri.note}</p>
            ) : null}
          </div>
        </section>

        <ItemSection
          title="Prerequisites"
          intro="Have these before opening the provider's form."
          items={guide.prerequisites}
        />
        <section className="mt-10">
          <h2 className="font-serif text-2xl">Steps</h2>
          <p className="mt-2 max-w-[68ch] text-sm leading-6 text-muted">In the order the cited docs describe them.</p>
          <ol className="mt-6 space-y-8">
            {guide.steps.map((step) => (
              <li key={step.position} className="grid grid-cols-[2.5rem_minmax(0,1fr)] gap-3">
                <span className="pt-1 font-mono text-sm text-muted">{String(step.position).padStart(2, "0")}</span>
                <ItemBody item={step} />
              </li>
            ))}
          </ol>
        </section>
        <ItemSection
          title="Blockers"
          intro="Reasons the launch can stall, taken from the sources or marked when the sources leave it open."
          items={guide.blockers}
        />
        <ItemSection
          title="Needs a person"
          intro="Clicks and decisions the docs leave to a human. This project did not perform them."
          items={guide.human_actions}
        />
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
        <p className="mt-6 text-sm font-semibold">How to read a mark</p>
        <ul className="mt-3 space-y-3">
          {(Object.keys(CLAIM_COPY) as ClaimStatus[]).map((status) => (
            <li key={status}>
              <ClaimMark status={status} />
              <p className="mt-1 text-sm leading-5 text-muted">{CLAIM_COPY[status].description}</p>
            </li>
          ))}
        </ul>
        <p className="mt-6 font-mono text-[11px] text-muted">Last checked {formatCheckedDate(guide.last_checked)}</p>
      </aside>
    </div>
  );
}

function Meta({ label, claim }: { label: string; claim: Claim }) {
  return (
    <div className="bg-raised px-4 py-4">
      <dt className="font-mono text-[11px] uppercase tracking-[0.12em] text-muted">{label}</dt>
      <dd className="mt-2 text-sm leading-6">
        <span>{claimText(claim.value)}</span>
        <span className="mt-2 block">
          <ClaimMark status={claim.status} />
        </span>
        {claim.note ? <span className="mt-2 block text-muted">{claim.note}</span> : null}
        <SourceLink url={claim.source_url} />
      </dd>
    </div>
  );
}

function ClaimBlock({ title, claim }: { title: string; claim: Claim }) {
  return (
    <div>
      <div className="flex flex-wrap items-center gap-2">
        <h3 className="text-sm font-semibold">{title}</h3>
        <ClaimMark status={claim.status} />
      </div>
      <p className="mt-2 text-sm leading-6">{claimText(claim.value)}</p>
      {claim.note ? <p className="mt-2 text-sm leading-6 text-muted">{claim.note}</p> : null}
      <SourceLink url={claim.source_url} />
    </div>
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
  return (
    <div>
      <div className="flex flex-wrap items-center gap-2">
        <h3 className="text-base font-semibold">{item.title}</h3>
        <ClaimMark status={item.status} />
      </div>
      <p className="mt-2 max-w-[68ch] text-[15px] leading-7">{item.body}</p>
      {item.note ? <p className="mt-2 max-w-[68ch] text-sm leading-6 text-muted">{item.note}</p> : null}
      <SourceLink url={item.source_url} />
    </div>
  );
}

function SourceLink({ url }: { url?: string | null }) {
  if (!url) {
    return null;
  }
  return (
    <a
      href={url}
      className="mt-2 block max-w-[68ch] break-all text-sm underline decoration-line-strong underline-offset-2"
    >
      {url}
    </a>
  );
}
