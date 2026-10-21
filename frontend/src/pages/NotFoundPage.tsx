import { useEffect } from "react";
import { Link } from "react-router-dom";

export function NotFoundPage() {
  useEffect(() => {
    document.title = "Page not found · Field Guide";
  }, []);

  return (
    <div className="max-w-xl">
      <p className="font-mono text-[11px] uppercase tracking-[0.16em] text-muted">Not found</p>
      <h1 className="mt-2 font-serif text-4xl">This page is not part of Field Guide</h1>
      <p className="mt-3 text-sm leading-6 text-muted">
        The library, a guide address, and the research form are the pages that exist.
      </p>
      <Link to="/" className="mt-5 inline-block border border-ink bg-ink px-3 py-2 text-sm text-paper">
        Back to the library
      </Link>
    </div>
  );
}
