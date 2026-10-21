# Field Guide

An OAuth setup library for Composio. It shows the work required to configure a provider app, whether Composio managed auth is enough, what can block a launch, and which steps a person still has to do.

**Hosted app:** https://field-guide-jun3.onrender.com

That address serves the library and the API. Research is on when the host has both API keys. A free Render service sleeps after inactivity, and the first request after that can take a minute.

The library runs with no API key. Research runs only when `MODEL_API_KEY` and `SEARCH_API_KEY` are both set. Without them, an unfamiliar app gets an honest “not configured” response and no guide is stored.

## What was built

- Searchable directory of 32 guides. GitHub, Google Calendar, and Slack are the editorial guides. The other 29, including Notion and Discord, are stored as snapshots in `backend/app/generated/` and loaded on startup.
- Standalone guide pages at `/guides/{slug}`, for example `/guides/github`, `/guides/google-calendar`, `/guides/slack`, and `/guides/notion`.
- Each guide opens with difficulty, hands-on work, approval wait, and a split between what was already collected and what you still do.
- Fields for authentication type, setup path, difficulty, active effort, approval wait, prerequisites, ordered steps, blockers, human actions, sources, confidence, and last-checked date.
- Every factual field is marked **Documented** (a cited page says it; this project did not run it), **Inferred** (a reading of retrieved pages, not a direct statement), **Unknown** (the pages do not establish it), or **Uncertain** (an editorial label or an open question). **Verified** is reserved for a setup this project has actually executed. Neither the seed nor research uses it.
- SQLite schema loaded on startup. Re-running the seed replaces guide text in place.

GitHub, Google Calendar, and Slack were written from official provider and Composio pages checked on 21 October 2026 and reconciled to `docs/provider-research.md`. Difficulty labels and hands-on durations on those three are editorial and marked uncertain, because the providers do not publish a rating or a measured time. Approval waits are quoted only where a page states one. GitHub’s registration wait was not found. Google’s sensitive-scope pages disagree (typically 3–5 business days versus an FAQ figure of 10 business days). Calendar scopes were not on the restricted-scope list, and the Calendar wait is otherwise unknown. Slack’s Marketplace bounds (up to 10 business days preliminary, up to 10 weeks for a new functional review) apply only to Marketplace review.

The other guides were saved from research runs on 21 October 2026 and checked into `backend/app/generated/` so a restart still serves them. Discord is in that folder with origin `editorial`. The rest are `researched`. A researched claim cites a page fetched for that run. Where those pages did not state a callback, a wait, or a difficulty, the field stays unknown.

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
5. Submit `Basecamp`. A documentation URL is optional. With both API keys unset, the page says research is not connected and no guide is stored. `http://127.0.0.1/secret` is rejected and does not start a run. Submitting Linear returns the guide that is already in the library.
6. Open Notion, Jira, and Gmail. Those guides were saved from research runs and are in `backend/app/generated/` so a restart still serves them. Notion’s approval wait stays unknown because the pages that run read did not state one. With both API keys set, submit an app that is not in the library, such as Basecamp. A documentation URL is optional. Wait until the run says the guide was saved, then open the guide URL in a new tab.

## Deploy

The hosted copy is one Docker web service. The image builds the frontend, then runs the API, and the API serves `index.html` for `/guides/*` and `/research`. Health check path: `/api/health`.

```bash
docker build -t field-guide .
docker run --rm -p 8000:8000 -e PORT=8000 field-guide
```

Set variables in the host's environment, not in a committed file. On Render the service listens on `0.0.0.0:$PORT`. Render sets `PORT`. Leave `DATABASE_URL` unset so the app uses `sqlite:///./data/guides.db`. Leave `SEED_ON_STARTUP` unset so it stays `true` and startup reloads the library. Leave `CORS_ORIGINS` unset: the hosted page and the API share one origin.

The library itself needs no API key. Research on the hosted app needs both keys, using the same providers as a local `backend/.env`:

| Variable | Value |
| --- | --- |
| `MODEL_PROVIDER` | `backboard` |
| `BACKBOARD_LLM_PROVIDER` | `openai` |
| `MODEL_NAME` | `gpt-4.1` |
| `MODEL_API_KEY` | the Backboard key from `backend/.env` |
| `SEARCH_PROVIDER` | `tavily` |
| `SEARCH_API_KEY` | the Tavily key from `backend/.env` |

`MODEL_PROVIDER` can instead be `openai`, `anthropic`, or `gemma`, with `SEARCH_PROVIDER` set to `tavily` or `brave`. Copy the keys into the Render Environment tab. Do not commit them. These keys are read when the process starts, so save them and deploy. A rebuild is unnecessary.

SQLite lives on the service disk. A free instance has an ephemeral filesystem, so a spin-down drops a guide that was saved only by a live research run. Startup writes the three editorial guides again and reloads every snapshot in `backend/app/generated/`. A research run that was still `queued` or `running` when the process stopped is marked failed, and that app name can be submitted again.

## API

| Method | Path | Behavior |
| --- | --- | --- |
| GET | `/api/health` | `research` is `configured` or `unavailable`. |
| GET | `/api/guides?q=&path=` | Directory of 32 guides. `path` is `managed_or_own` or `own_app_unless_confirmed`. |
| GET | `/api/guides/{slug}` | Full guide. Unknown slugs return 404. |
| POST | `/api/research-requests` | Validates the name or website. An existing guide returns `guide_exists` and is not rewritten. An unsafe URL returns 422. Without API keys, an unknown app returns 503 `research_unavailable`. With keys, a name or website alone returns 202 and a run id. A documentation URL is optional and is included in the four pages that get read. A second submission for the same in-flight app joins that run. |
| POST | `/api/guides/{slug}/recheck` | Reads the docs again for a guide that already exists. Requires `docs_url` when research is configured. Saves a candidate and leaves the live guide unchanged. |
| GET | `/api/guides/{slug}/candidate` | The pending candidate and which fields differ. 404 when nothing is waiting. |
| POST | `/api/guides/{slug}/candidate/promote` | Replaces the live guide with the candidate. Startup leaves a promoted editorial guide in place. A snapshot in `backend/app/generated/` is written again on startup. |
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

Seeded guides for GitHub, Google Calendar, and Slack were written from the pages in `docs/provider-research.md`, checked on 21 October 2026. Their source list is the citation panel on the guide. Individual seeded sentences are not each tied to one URL. The other 29 guides are snapshots of local research runs, checked in under `backend/app/generated/`. A researched claim is stored only after it cites a page fetched for that run, and the guide shows that page's URL on the claim. Notion’s run did not establish difficulty, hands-on time, or an approval wait, so those fields stay unknown. Most of the saved Notion steps cite `https://composio.dev/auth/notion`.

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
- Submitting an app that is already in the library returns that guide and does not rewrite it. Recheck stores a candidate beside that guide. The live text changes only when a person promotes the candidate. A promoted guide is marked researched. Startup still replaces a guide that has a snapshot in `backend/app/generated/` or an editorial entry in `backend/app/seed_data.py`. Seeded claims do not carry a per-sentence source URL until that promotion.
- Composio’s managed-OAuth catalog lists GitHub, Google Calendar, and Slack, and an own OAuth app is optional for them. The live toolkit API was not called, default scopes were not published, and no OAuth flow was executed.
- Google’s current web-client instructions say client secrets are not used for web applications, while Composio’s form asks for a client secret. That disagreement stays uncertain in the seeded Calendar guide.
