# Field Guide

A local OAuth setup library for Composio. It shows the work required to configure a provider app, whether Composio managed auth is enough, what can block a launch, and which steps need a person.

The library runs with no API key. Research runs only when `MODEL_API_KEY` and `SEARCH_API_KEY` are both set. Without them, an unfamiliar app gets an honest “not configured” response and no guide is stored.

## What was built

- Searchable directory of GitHub, Google Calendar, and Slack.
- Standalone guide pages at `/guides/github`, `/guides/google-calendar`, and `/guides/slack`.
- Fields for authentication type, setup path, difficulty, active effort, approval wait, prerequisites, ordered steps, blockers, human actions, sources, confidence, and last-checked date.
- Every factual field is marked **Documented** (a cited page says it; this project did not run it), **Inferred** (a reading of retrieved pages, not a direct statement), **Unknown** (the pages do not establish it), or **Uncertain** (an editorial label or an open question). **Verified** is reserved for a setup this project has actually executed. Neither the seed nor research uses it.
- SQLite schema loaded on startup. Re-running the seed replaces guide text in place.

The three guides were written from official GitHub, Google, Slack, and Composio pages checked on 21 October 2026 and reconciled to `docs/provider-research.md`. Difficulty labels and hands-on durations are editorial and marked uncertain, because the providers do not publish a rating or a measured time. Approval waits are quoted only where a page states one. GitHub’s registration wait was not found. Google’s sensitive-scope pages disagree (typically 3–5 business days versus an FAQ figure of 10 business days). Calendar scopes were not on the restricted-scope list, and the Calendar wait is otherwise unknown. Slack’s Marketplace bounds (up to 10 business days preliminary, up to 10 weeks for a new functional review) apply only to Marketplace review.

## Layout

- `backend/` — FastAPI, SQLAlchemy, SQLite
- `frontend/` — React, Vite, TypeScript, Tailwind CSS

## Run it

Use Python 3.11 through 3.13 and a current Node.js. On this machine `python3` is a 3.15 beta, so the commands below use `python3.13`, which is what the tests ran on.

```bash
cd backend
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The dev server proxies `/api` to http://127.0.0.1:8000.

Copy `.env.example` to `backend/.env` to configure research. Leave the keys blank to run the library only. Never commit a filled-in key.

Reload the guides without starting the server:

```bash
cd backend && python -m app.seed
```

## Tests

```bash
cd backend && .venv/bin/pytest
cd frontend && npm test && npm run build
```

## API

| Method | Path | Behavior |
| --- | --- | --- |
| GET | `/api/health` | `research` is `configured` or `unavailable`. |
| GET | `/api/guides?q=&path=` | Directory. `path` is `managed_or_own` or `own_app_unless_confirmed`. The three seeded guides use `managed_or_own`. |
| GET | `/api/guides/{slug}` | Full guide. Unknown slugs return 404. |
| POST | `/api/research-requests` | Validates the name or website. An existing guide returns `guide_exists` and is not rewritten. An unsafe URL returns 422. Without API keys, an unknown app returns 503 `research_unavailable`. With keys, returns 202 and a run id. A second submission for the same in-flight app joins that run. |
| GET | `/api/research-runs/{id}` | Run status, evidence URLs, retrieval timestamps, and the claims each page supports. |
| GET | `/api/research-runs/{id}/events` | Server-Sent Events. `Last-Event-ID` resumes after a disconnect. |

Guide addresses are the frontend routes above. A static host needs to serve `index.html` for those paths; the Vite dev server already does.

## Research

`MODEL_PROVIDER` is `openai` (default model `gpt-4o-mini`) or `anthropic` (default model `claude-sonnet-4-5`). `SEARCH_PROVIDER` is `tavily` or `brave`. `MODEL_NAME` overrides the model id.

A run searches, fetches public pages, and asks the model to extract a guide from those pages only. Search snippets are not evidence. The model output is checked with Pydantic. Documented claims must cite a retrieved page and overlap its text. URLs and durations must appear in the cited page. If two retrieved pages give different review durations, the wait is stored as unknown and both figures are kept. A guide is saved only when an authentication type and at least one step survive that check. Output that contains a client secret, API key, or access token is discarded.

Pages are fetched with `trust_env` off, so `HTTP_PROXY` cannot point the reader at an internal service. Schemes other than http and https, embedded credentials, ports other than 80 and 443, localhost, private and link-local addresses, and cloud metadata addresses are rejected. Redirects are checked again before they are followed. Response bodies are capped and scripts are stripped, not executed.

## Limitations

- Research does not run an OAuth flow, so it never marks a claim verified.
- JavaScript-only documentation is not executed, so a page that is empty without a browser can come back as unreadable.
- Contradiction detection covers review durations. It does not settle every kind of disagreement.
- HTTPS fetches re-resolve the hostname after the public-address check, so a fast DNS rebinding response is still a residual risk.
- The duplicate lock is a row in SQLite. It covers threads in this process. Two servers writing the same database can still race at insert time; the slug unique constraint then keeps the first guide.
- Seeded GitHub, Google Calendar, and Slack guides are left unchanged by later research.
- Composio’s managed-OAuth catalog lists those three, and an own OAuth app is optional for them. The live toolkit API was not called, default scopes were not published, and no OAuth flow was executed.
- Google’s current web-client instructions say client secrets are not used for web applications, while Composio’s form asks for a client secret. That disagreement stays uncertain in the seeded Calendar guide.
