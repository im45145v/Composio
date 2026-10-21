import type { ReactNode } from "react";

export function LoadingBlock({ label }: { label: string }) {
  return (
    <div role="status" aria-live="polite" className="space-y-4">
      <p className="text-sm text-muted">{label}</p>
      <div className="h-10 border border-line bg-raised" />
      <div className="h-28 border border-line bg-raised" />
      <div className="h-28 border border-line bg-raised" />
    </div>
  );
}

export function ErrorBlock({
  title,
  detail,
  onRetry,
}: {
  title: string;
  detail: string;
  onRetry?: () => void;
}) {
  return (
    <div role="alert" className="border border-danger/30 bg-danger-soft px-5 py-6">
      <h2 className="font-serif text-2xl">{title}</h2>
      <p className="mt-2 max-w-xl text-sm leading-6">{detail}</p>
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="mt-4 border border-ink bg-ink px-3 py-2 text-sm text-paper"
        >
          Try again
        </button>
      ) : null}
    </div>
  );
}

export function EmptyBlock({ title, detail, action }: { title: string; detail: string; action?: ReactNode }) {
  return (
    <div role="status" className="border border-dashed border-line-strong bg-raised px-5 py-8">
      <h2 className="font-serif text-2xl">{title}</h2>
      <p className="mt-2 max-w-xl text-sm leading-6 text-muted">{detail}</p>
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}
