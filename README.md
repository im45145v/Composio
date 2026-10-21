# Field Guide

An OAuth setup library for Composio. It shows the work required to configure a provider app, whether Composio managed auth is enough, what can block a launch, and which steps a person still has to do.

**Hosted app:** https://field-guide-jun3.onrender.com

That address serves the library and the API. Research is on when the host has both API keys. A free Render service sleeps after inactivity, and the first request after that can take a minute.

The library runs with no API key. Research runs only when `MODEL_API_KEY` and `SEARCH_API_KEY` are both set. Without them, an unfamiliar app gets an honest “not configured” response and no guide is stored.

## What was built

- Searchable directory of GitHub, Google Calendar, Slack, and Notion.
- Standalone guide pages at `/guides/github`, `/guides/google-calendar`, `/guides/slack`, and `/guides/notion`.
- Each guide opens with difficulty, hands-on work, approval wait, and a split between what was already collected and what you still do.
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

Open http://127.0.0.1:5173. The dev server listens on that address and proxies `/api` to http://127.0.0.1:8000.

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

The test suite mocks search, page fetches, and the model. It does not call a paid API.

## Demo script

1. Start the backend and frontend with the commands above. Open http://127.0.0.1:5173.
2. Search `calendar`. Only Google Calendar remains. Clear the search. `not-a-provider` shows an empty library.
3. Open GitHub, Google Calendar, and Slack from the list, then load http://127.0.0.1:5173/guides/slack directly. Each page lists sources and marks claims. None of them say Verified.
4. Open Research an app and submit GitHub. The existing guide is returned and is not rewritten.
5. Submit `Linear`, or `https://linear.app`. A documentation URL is optional. With both API keys unset, the page says research is not connected and no guide is stored. `http://127.0.0.1/secret` is rejected and does not start a run.
6. Open Notion. That guide was generated on 22 October 2026 from `https://developers.notion.com`, then saved in `backend/app/generated/notion.json` so a restart still serves it. Its approval wait stays unknown because the pages that run read did not state one. With both API keys set, submit an app that is not in the library, such as Linear. A documentation URL is optional. Wait until the run says the guide was saved, then open the guide URL in a new tab.

## Deploy

The hosted copy is one Docker web service. The image builds the frontend, then runs the API, and the API serves `index.html` for `/guides/*` and `/research`. Health check path: `/api/health`.

```bash
docker build -t field-guide .
docker run --rm -p 8000:8000 -e PORT=8000 field-guide
```

Set the variables from `.env.example` in the host's environment, not in a committed file. On Render the service listens on `0.0.0.0:$PORT`.

SQLite lives on the service disk. A free instance has an ephemeral filesystem, so a spin-down drops guides that were saved only by a live research run. Startup writes the editorial guides again and reloads `backend/app/generated/notion.json`. A research run that was still `queued` or `running` when the process stopped is marked failed, and that app name can be submitted again.

## API

| Method | Path | Behavior |
| --- | --- | --- |
| GET | `/api/health` | `research` is `configured` or `unavailable`. |
| GET | `/api/guides?q=&path=` | Directory. `path` is `managed_or_own` or `own_app_unless_confirmed`. GitHub, Google Calendar, and Slack use `managed_or_own`. Notion uses `own_app_unless_confirmed`. |
| GET | `/api/guides/{slug}` | Full guide. Unknown slugs return 404. |
| POST | `/api/research-requests` | Validates the name or website. An existing guide returns `guide_exists` and is not rewritten. An unsafe URL returns 422. Without API keys, an unknown app returns 503 `research_unavailable`. With keys, a name or website alone returns 202 and a run id. A documentation URL is optional and is included in the four pages that get read. A second submission for the same in-flight app joins that run. |
| POST | `/api/guides/{slug}/recheck` | Reads the docs again for a guide that already exists. Requires `docs_url` when research is configured. Saves a candidate and leaves the live guide unchanged. |
| GET | `/api/guides/{slug}/candidate` | The pending candidate and which fields differ. 404 when nothing is waiting. |
| POST | `/api/guides/{slug}/candidate/promote` | Replaces the live guide with the candidate. A later startup does not overwrite that promoted guide with the seed. |
| POST | `/api/guides/{slug}/candidate/discard` | Drops the candidate. |
| GET | `/api/research-runs/{id}` | Run status, evidence URLs, retrieval timestamps, and the claims each page supports. |
| GET | `/api/research-runs/{id}/events` | Server-Sent Events. `Last-Event-ID` resumes after a disconnect. |

Guide addresses are the frontend routes above. A static host needs to serve `index.html` for those paths; the Vite dev server already does.

## Research

`MODEL_PROVIDER` is `openai` (default model `gpt-4o-mini`), `anthropic` (default model `claude-sonnet-4-5`), `backboard`, or `gemma` (default model `gemma-4-26b-a4b-it` on the Gemini API). `MODEL_NAME` overrides the model id. `SEARCH_PROVIDER` is `tavily` or `brave`.

`backboard` sends `MODEL_API_KEY` as the Backboard `X-API-Key` and calls `https://app.backboard.io/api/threads/messages`. `BACKBOARD_LLM_PROVIDER` chooses the upstream: `openai` (default model `gpt-4.1`) or `google` (default model `gemma-4-26b-a4b-it`). Memory and Backboard web search stay off, so a guide still has to come from pages this app fetched. `gemma` calls the Gemini API directly with a Google AI Studio key and the same default Gemma model. The other hosted Gemma 4 id is `gemma-4-31b-it`.

A run searches, fetches public pages, and asks the model to extract a guide from those pages only. Search snippets are not evidence. A search hit is kept only when its URL or title names the app and the URL looks like documentation or a Composio page. News and marketing URLs are not fetched. After a page is fetched, it is dropped when the title, URL, and opening text still do not name the app, so a page about a different product is not saved under the submitted name. The model output is checked with Pydantic. A fenced JSON object is accepted. Claims that arrive as plain strings, and missing lists, are coerced locally before that check; a second model call is used only when the first result still fails. Documented claims must cite a retrieved page and overlap its text. A documented claim that drops a condition such as "before", "unless", "except", or "only if" is stored as inferred, with the source sentence in the note. Inferred claims that do not overlap the cited page are dropped. URLs and durations must appear in the cited page. If two retrieved pages give different review durations, the wait is stored as unknown and both figures are kept. A guide is saved only when an authentication type, at least one step, and at least one human action survive that check. Each saved claim records the first cited page URL. Output that contains a client secret, API key, or access token is discarded. When the model omits a decision, the saved decision says the pages did not state one, rather than repeating the summary.

The reader keeps at most `MAX_RESEARCH_PAGES` URLs (default 4). Inside that budget it keeps the caller's documentation URL when one was submitted, the highest-scoring on-topic page that is not on `composio.dev`, and one on-topic Composio page. Any slots left go to other provider pages before more Composio pages. HTML and Markdown are read. A body larger than `PAGE_MAX_BYTES` (default 1,200,000) is cut at that limit and the prefix is kept.

Pages are fetched with `trust_env` off, so `HTTP_PROXY` cannot point the reader at an internal service. Schemes other than http and https, embedded credentials, ports other than 80 and 443, localhost, private and link-local addresses, and cloud metadata addresses are rejected. Each request connects to an address from that same public-address check, with the original hostname kept for the Host header and TLS server name. Redirects are checked the same way before they are followed. Response bodies are capped and scripts are stripped, not executed. A rejected search or model key is reported as a configuration failure, and the provider's response body is not stored or shown.

## Evidence

Seeded guides for GitHub, Google Calendar, and Slack were written from the pages in `docs/provider-research.md`, checked on 21 October 2026. Their source list is the citation panel on the guide. Individual seeded sentences are not each tied to one URL. Notion is a researched guide from a run on 22 October 2026 that started with `https://developers.notion.com`. A claim on that guide is stored only after it cites a page fetched for that run, and the guide shows that page's URL on the claim. The run did not establish difficulty, hands-on time, or an approval wait, so those fields stay unknown. Most of the saved steps cite `https://composio.dev/auth/notion`. The research run also stores the page title, retrieval time, and the claim keys that page supports.

**Documented** means the cited page states the claim and this project did not run it. **Inferred** means the wording is a reading of the retrieved pages, not a direct statement. **Unknown** means those pages do not establish it. **Uncertain** is an editorial label or an open question, including difficulty and hands-on duration, which the providers do not publish as a rating or a measured time. **Verified** would mean this project executed the setup. Nothing in the seed or the research pipeline uses it.

Approval waits are quoted only where a retrieved page states one. If two retrieved pages give different review durations, neither figure is chosen. GitHub's approval-wait text says the staff-review wait was not found; the mark is Documented because that absence is what the creation page shows, not because a duration was measured.

## Limitations

- Research does not run an OAuth flow, so it never marks a claim verified.
- JavaScript-only documentation is not executed, so a page that is empty without a browser can come back as unreadable.
- Contradiction detection covers review durations. It does not settle every kind of disagreement.
- The fetch budget is four pages. Reserving a provider page and a Composio page does not guarantee that the provider's registration page is the provider page that ranks highest. A page whose URL and title never name the app is not fetched, even when a search snippet mentions it.
- A page over 1.2 MB is truncated, so a claim can be checked only against the prefix that was stored.
- Overlap checks catch claims that do not share wording with the cited page. A dropped "before", "unless", "except", or "only if" is marked inferred. Other paraphrases can still pass when they share enough words.
- A restart fails an in-flight run and releases that app name. The duplicate lock is still one SQLite row in this process. Two servers writing the same database can race at insert time; the slug unique constraint then keeps the first guide.
- Submitting GitHub, Google Calendar, or Slack through research returns the existing guide and does not rewrite it. Recheck stores a candidate beside that guide. The live text changes only when a person promotes the candidate. A promoted guide is marked researched, and the startup seed leaves it in place. Seeded claims do not carry a per-sentence source URL until that promotion.
- Composio’s managed-OAuth catalog lists those three, and an own OAuth app is optional for them. The live toolkit API was not called, default scopes were not published, and no OAuth flow was executed.
- Google’s current web-client instructions say client secrets are not used for web applications, while Composio’s form asks for a client secret. That disagreement stays uncertain in the seeded Calendar guide.
