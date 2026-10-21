import { useState, type FormEvent } from "react";
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";

const linkClass = ({ isActive }: { isActive: boolean }) =>
  `text-sm ${isActive ? "text-ink underline decoration-pine underline-offset-4" : "text-muted"}`;

export function Shell() {
  const location = useLocation();
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const showSearch = location.pathname !== "/";

  function onSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = query.trim();
    navigate(trimmed ? `/?q=${encodeURIComponent(trimmed)}` : "/");
  }

  return (
    <div className="min-h-screen">
      <a
        href="#content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-20 focus:bg-raised focus:px-3 focus:py-2"
      >
        Skip to content
      </a>
      <header className="sticky top-0 z-10 border-b border-line bg-paper/95">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-x-6 gap-y-3 px-5 py-3">
          <Link to="/" className="leading-tight">
            <span className="block font-mono text-[11px] uppercase tracking-[0.16em] text-muted">Composio</span>
            <span className="block text-[15px] font-semibold">Field Guide</span>
          </Link>
          <div className="flex flex-wrap items-center gap-x-5 gap-y-2">
            {showSearch ? (
              <form role="search" onSubmit={onSearch} className="flex">
                <label htmlFor="header-search" className="sr-only">
                  Search guides
                </label>
                <input
                  id="header-search"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Search guides"
                  className="w-40 border border-line bg-raised px-2 py-1 text-sm sm:w-52"
                />
              </form>
            ) : null}
            <nav aria-label="Primary" className="flex items-center gap-4">
              <NavLink to="/" end className={linkClass}>
                Library
              </NavLink>
              <NavLink to="/research" className={linkClass}>
                Research an app
              </NavLink>
            </nav>
          </div>
        </div>
      </header>
      <main id="content" className="mx-auto min-w-0 max-w-6xl px-5 py-8 sm:py-10">
        <Outlet />
      </main>
      <footer className="border-t border-line">
        <p className="mx-auto max-w-6xl px-5 py-5 text-sm text-muted">
          Guides cite retrieved pages and say when a claim was not run. Research stays on the server.
        </p>
      </footer>
    </div>
  );
}
