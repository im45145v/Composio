# OAuth setup research: GitHub, Google Calendar, and Slack

**Date checked:** Wednesday, 21 October 2026.

**Method:** Official provider documentation and current Composio documentation were fetched on that date. Context7 was used as a secondary index into `docs.composio.dev`; material claims below are tied to the page that was fetched, not to the index alone. No OAuth flow was executed against GitHub, Google, Slack, or Composio. No Composio, GitHub, Google, or Slack API was called. Nothing in this note was verified by testing.

**Status labels**

- **documented (not executed):** the cited page says this. It was read, not tried.
- **uncertain:** the pages do not state it, they conflict, or a link target could not be recovered.

"Documented" does not mean tested.

---

## Shared Composio managed auth

Sources in this section are Composio statements unless a provider page is named.

### Availability model

**documented (not executed).** Current page [Managed vs custom auth](https://docs.composio.dev/docs/authentication/custom-app-vs-managed-app) says Composio "registers and maintains OAuth apps for popular toolkits such as GitHub, Gmail, and Slack" and "You do not need to register your own OAuth app" for those managed apps. Managed apps "are the default when they are available." The same page says to use them when building and iterating, when "default scopes cover your needs," and when consent-screen branding does not matter yet. It says users will see "Composio wants to access your account."

**documented (not executed).** [Managed OAuth apps](https://docs.composio.dev/toolkits/managed-auth) says: "Composio can provide the OAuth app that your users authorize when they connect a toolkit. You do not need to register an OAuth app or supply its client ID and client secret." A toolkit is listed as managed "when Composio manages at least one OAuth method." The page also says to confirm with `composio_managed_auth_schemes` on `GET https://backend.composio.dev/api/v3.1/toolkits/{slug}`. That endpoint was **not called**.

On the managed-OAuth list fetched 21 October 2026, these slugs appear under "Composio-managed OAuth available":

| Toolkit | Slug | Toolkit page line (fetched the same day) |
| --- | --- | --- |
| GitHub | `GITHUB` | [GitHub toolkit](https://docs.composio.dev/toolkits/github): "Auth: OAUTH2" and "Composio-managed OAuth available? Yes". Version shown: `20261014_00`. |
| Google Calendar | `GOOGLECALENDAR` | [Google Calendar toolkit](https://docs.composio.dev/toolkits/googlecalendar): "Auth: OAUTH2" and "Composio-managed OAuth available? Yes". Version shown: `20261010_00`. |
| Slack | `SLACK` | [Slack toolkit](https://docs.composio.dev/toolkits/slack): "Auth: OAUTH2" and "Composio-managed OAuth available? Yes". Version shown: `20261020_00`. |

`SLACKBOT` is a separate row on the managed list. This note is about `SLACK`.

**Gap.** The managed-auth list is a catalog statement. The live `composio_managed_auth_schemes` field was not read, so the catalog and the API were not cross-checked.

### When a developer actually needs their own OAuth app

**documented (not executed).** On the current [Managed vs custom auth](https://docs.composio.dev/docs/authentication/custom-app-vs-managed-app) page, own credentials are for these cases, not for making managed OAuth exist:

- Production consent screens should show the developer's app name, not "Composio." The page calls this "the most common reason to switch."
- Custom scopes, with the example "write access to a specific Google API."
- Dedicated quota, because "Managed apps share quota across all Composio users."
- Polling triggers shorter than the managed-auth "15-minute minimum."
- A custom or self-hosted instance.
- Enterprise branding "end-to-end."

The same page says some OAuth toolkits have no managed app and then "register your own OAuth app." GitHub, Google Calendar, and Slack are not in that "bring your own" list; they are in the managed list.

**documented (not executed).** [White-labeling authentication](https://docs.composio.dev/docs/authentication/white-labeling-authentication) (current, not marked legacy) says own OAuth apps are needed only "for OAuth toolkits where users see a provider consent screen and your product needs its own branding, scopes, or quotas." Connect Link logo changes do not change the provider consent screen. It names Google, GitHub, and Slack as consent-screen examples and says the default wording is "Composio wants to connect to your account."

**documented (not executed), legacy page.** [Custom Auth Configs](https://docs.composio.dev/docs/auth-configuration/custom-auth-configs) is marked: "Legacy. This is a point-in-time migration/legacy guide and may describe outdated APIs. For current guidance, see https://docs.composio.dev." It still says "Use your own developer app!" and "We recommend using your own developer app for the OAuth2 scheme as it is more suited for production usage with many users and more granular control over scopes." It also says "getting OAuth approvals takes time, so Composio provides a default developer app." That "approvals take time" sentence does not name GitHub, Google, or Slack and does not give a duration. The current managed-vs-custom page is the page the legacy banner points at, and that current page does not say an own app is required before a managed toolkit can connect.

### Callback URI

**documented (not executed).** Current [Programmatic auth configs](https://docs.composio.dev/docs/authentication/programmatic-auth-configs) tells developers who bring their own OAuth app to set the provider redirect URI to:

`https://backend.composio.dev/api/v3/toolkits/auth/callback`

The same page says: "Some toolkit defaults still use the supported legacy endpoint `https://backend.composio.dev/api/v1/auth-apps/add`. If you omit `oauth_redirect_uri`, register the toolkit's default URL with your provider."

**documented (not executed).** The legacy [Custom Auth Configs](https://docs.composio.dev/docs/auth-configuration/custom-auth-configs) page documents the same v3 URL and says the v1 URL "remains supported." It says a mismatch causes `redirect_uri_mismatch`.

**documented (not executed).** Current white-labeling also documents proxying through the developer's own HTTPS endpoint, which must 302 the browser to the v3 callback. That proxy URL is not a replacement for registering a redirect the provider and the Composio auth config both use.

**documented (not executed), separate Composio how-to site.** Guides on `composio.dev/auth` still show the v1 URL in the click-path for Google and Slack, while the GitHub guide on that site explicitly says the screenshot used v1 and "Current Composio documentation now points to" the v3 URL. See the contradiction section.

### What was not found

**uncertain.** No fetched Composio page publishes the default scope string that managed auth actually requests for GitHub, Google Calendar, or Slack. [Controlling scopes](https://docs.composio.dev/docs/authentication/controlling-scopes) says Composio "requests a sensible set of default scopes" and that most apps never set scopes. The GitHub `repo,read:org` strings on that page are code samples, not a statement of the managed default. The API field `composio_managed_auth.scopes.available` is documented as an available-scope ceiling on [Get toolkit by slug](https://docs.composio.dev/reference/api-reference/toolkits/getToolkitsBySlug). It was not called, and the docs do not say that ceiling is the default request.

---

## GitHub

OAuth Apps are the registration path below. GitHub App permissions are a different model and are not treated as the OAuth scope list.

### 1. Is Composio managed OAuth available, and how was that checked?

**documented (not executed).** Yes, according to Composio's catalog and toolkit page, not according to a live API call.

- [Managed OAuth apps](https://docs.composio.dev/toolkits/managed-auth) lists GitHub / `GITHUB` under "Composio-managed OAuth available."
- [GitHub toolkit](https://docs.composio.dev/toolkits/github) says "Auth: OAUTH2" and "Composio-managed OAuth available? Yes."

**Gap.** That toolkit page does not say whether the managed app is a GitHub OAuth App or a GitHub App. The FAQ on the same page answers "Does Composio support GitHub Apps?" with "Yes. You can bring your own GitHub App" and says "GitHub App permissions come from the app's GitHub settings and installation grant, not from auth config scopes." That is a bring-your-own path. It does not identify the managed app's type. **uncertain** which GitHub product the managed app is.

The page `composio_managed_auth_schemes` check was not run.

### 2. When does a developer need their own OAuth app?

**documented (not executed), Composio.** Not required to start if the managed app is accepted. Own credentials are for branding, custom scopes, quota, faster polling, or enterprise branding, per [Managed vs custom auth](https://docs.composio.dev/docs/authentication/custom-app-vs-managed-app).

**documented (not executed), Composio how-to.** [How to create GitHub OAuth credentials](https://composio.dev/auth/github) says "For production setups, using your own developer credentials is the recommended Composio approach" and later "Managed auth can be convenient for development and quick testing, but using your own developer app is the recommended route for production." That is a recommendation on the how-to site, not a statement that managed auth stops working in production. The current docs page is softer: branding is "the most common reason to switch," not a hard gate.

**documented (not executed), GitHub.** Creating an OAuth app is required only if the developer is registering their own app. GitHub's creation page does not know about Composio.

### 3. Official developer registration page

**documented (not executed).** [Creating an OAuth app](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-an-oauth-app) is the official instruction page. It does not publish a single registration URL. The documented path is: profile picture → **Settings** → **Developer settings** → **OAuth apps** → **New OAuth App** (or **Register a new application** if none exist yet). The app can be owned by a personal account or by an organization the user administers.

### 4. Configuration and callback URI

**documented (not executed), GitHub.** The creation page requires:

1. Application name. Warning: "Only use information in your OAuth app that you consider public."
2. Homepage URL, "the full URL to your app's website."
3. Optional application description.
4. Authorization callback URL. "You can enter up to 10 callback URLs."
5. Optional **Enable Device Flow**.
6. "Expire user access tokens is enabled by default." Uncheck only if the app cannot yet handle short-lived tokens.
7. **Register application.**

A user or organization can own up to 100 OAuth apps.

The same page's note, still present on 21 October 2026: "Consider building a GitHub App instead of an OAuth app." It says both use OAuth 2.0, OAuth apps "can only act on behalf of a user," and GitHub Apps "use fine-grained permissions, give the user more control over which repositories the app can access, and use short-lived tokens." [Differences between GitHub Apps and OAuth apps](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/differences-between-github-apps-and-oauth-apps) repeats: "In general, GitHub Apps are preferred over OAuth apps."

**documented (not executed), GitHub redirect rules.** [Authorizing OAuth apps](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps): if `redirect_uri` is omitted, GitHub uses the first configured callback URL. With wildcard matching disabled, "the redirect URL must exactly match the callback URL." Wildcard matching is optional and GitHub warns it "can expose your app to security risks." "Apps that had a single callback URL enabled prior to August 3, 2026 have wildcard matching enabled for that callback URL." The temporary authorization `code` "will expire after 10 minutes."

**documented (not executed), Composio callback.** If the developer brings their own app, current Composio docs say to register `https://backend.composio.dev/api/v3/toolkits/auth/callback` unless the auth config's `oauth_redirect_uri` is the legacy `https://backend.composio.dev/api/v1/auth-apps/add` or a custom proxy. The two values must match. [Programmatic auth configs](https://docs.composio.dev/docs/authentication/programmatic-auth-configs); legacy [Custom Auth Configs](https://docs.composio.dev/docs/auth-configuration/custom-auth-configs).

**documented (not executed), Composio how-to.** [composio.dev/auth/github](https://composio.dev/auth/github) says a screenshot showed the v1 URL and tells the reader to use "the redirect URI that your current Composio Auth Config shows," naming the v3 URL as what current docs point to.

### 5. Scopes for a minimal connection

**documented (not executed), GitHub.** [Scopes for OAuth apps](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/scopes-for-oauth-apps) says scopes "do not grant any additional permission beyond that which the user already has." The table's first row is `(no scope)`: "Grants read-only access to public information (including user profile info, repository info, and gists)." [Best practices for creating an OAuth app](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/best-practices-for-creating-an-oauth-app) says: "Your OAuth app should only request the scopes that the app needs to perform its intended functionality." GitHub does not name one scope set as the minimum for a generic "basic user-authorized connection." Users can grant fewer scopes than requested.

[Authorizing OAuth apps](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps) says if `scope` is omitted, it "defaults to an empty list for users that have not authorized any scopes for the application." For users who already authorized scopes, a later request that omits `scope` completes with the scopes already granted, and the user is not shown the scope list again.

**Not a product recommendation.** The how-to at [composio.dev/auth/github](https://composio.dev/auth/github) has a "Scope summary from the example" listing `repo`, `user`, `gist`, `notifications`, `project`, `workflow`, and `codespace`. The page labels that as an example and says "Only request the scopes your Composio tools truly need." Those are not GitHub's required minimum and they are not published as Composio's managed default.

**Composio default scopes: not found.** The controlling-scopes samples `repo,read:org` and `repo,read:org,read:user` are examples. **uncertain** what the managed GitHub app requests by default.

GitHub App permission names are not OAuth scopes. The scopes page says: "If you're building a GitHub App, you don't provide scopes in your authorization request."

### 6. Registering, consent, and publishing

Separate these. Do not treat "OAuth exists" as "GitHub must review the app."

**(a) Registering the developer app.** **documented (not executed).** Registration is the Settings → Developer settings → OAuth apps form above. No review step appears on [Creating an OAuth app](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-an-oauth-app).

**(b) End-user consent.** **documented (not executed).** "When setting up an OAuth app on GitHub, requested scopes are displayed to the user on the authorization form." ([Scopes for OAuth apps](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/scopes-for-oauth-apps).) The user authorizes the app to act as that user. Organization owners can revoke OAuth app access. ([Differences between GitHub Apps and OAuth apps](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/differences-between-github-apps-and-oauth-apps).)

**(c) Production publishing / app review.** **documented (not executed) that a general GitHub review queue for OAuth apps was not found.** No fetched GitHub page says a new OAuth app must be submitted for GitHub staff review before its owner, or other users, can authorize it.

**documented (not executed), conditional org approval, not a global review.** [Approving OAuth apps for your organization](https://docs.github.com/en/organizations/managing-oauth-access-to-your-organizations-data/approving-oauth-apps-for-your-organization) applies "When OAuth app access restrictions are enabled." Members must then request approval "before they can authorize an OAuth app that has access to the organization's resources." Owners review under Third-party Access → OAuth app policy and click **Grant access**. That is an organization policy, not GitHub Marketplace review, and it does not apply to every organization. The Composio GitHub how-to describes the same Request button as something that "might" appear. ([composio.dev/auth/github](https://composio.dev/auth/github).)

### 7. Documented blockers and remedies

| Blocker | What the page says | Remedy the page gives |
| --- | --- | --- |
| Callback mismatch | With wildcard matching off, the redirect URL must exactly match the callback URL. ([Authorizing OAuth apps](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps).) Composio names the error `redirect_uri_mismatch` when the provider URI and `oauth_redirect_uri` differ. ([Custom Auth Configs](https://docs.composio.dev/docs/auth-configuration/custom-auth-configs), legacy page, same URL pair as current programmatic docs.) | Register the same URL in GitHub and in the Composio auth config. Current docs' explicit URL is the v3 callback; v1 remains supported if that is the config's default. |
| Old apps and wildcard matching | Apps with a single callback URL from before 3 August 2026 have wildcard matching on. GitHub recommends disabling it if it is not needed. | Disable wildcard matching in the OAuth app settings. |
| Authorization code lifetime | The temporary code expires after 10 minutes. | Send the user through the flow again. Not tested. |
| Expiring tokens on by default | Creation page: expiring user access tokens are enabled by default. Authorizing page: "The access token expires after eight hours, and the refresh token expires after six months without use." | Use the refresh token, or uncheck expiring tokens only until the app supports them. Refresh failure returns `bad_refresh_token`; send the user through the flow again. |
| User grants fewer scopes | Scopes page: users can edit scopes down, including after the flow. | Handle reduced functionality or send the user through the flow again. They can refuse. |
| Organization restrictions | Only when that org has OAuth app access restrictions enabled. | The member requests access; an owner grants it. ([Requesting organization approval](https://docs.github.com/en/account-and-profile/how-tos/organization-membership/requesting-organization-approval-for-oauth-apps).) |
| 100 OAuth apps per owner | Creation page. | Not given, other than the limit itself. |
| GitHub App install is separate | Composio FAQ: installation and repository grant are separate from client id/secret, and Composio "does not currently provide the GitHub App installation link automatically." ([GitHub toolkit](https://docs.composio.dev/toolkits/github).) | Give the user the GitHub App installation link, have them install it, then complete the connection. This applies to bring-your-own GitHub Apps, not to the OAuth scope list. |

No fetched page documented an "unpublished OAuth app can only be installed by its owner" rule of the Slack kind.

### 8. Hands-on work

Duration: **unknown**. GitHub and Composio list human steps and do not state how long they take. The count below is the documented click-path, not a measured time. Label: unverified editorial inventory, not an estimate in minutes.

If managed auth is used, Composio's current page says there is no OAuth app registration. The remaining human step it describes is the end user consenting to the Composio-named app. That consent was not executed.

If the developer registers their own OAuth app, the documented steps are:

1. Open Settings → Developer settings → OAuth apps → New OAuth App. (GitHub.)
2. Enter application name, homepage URL, optional description, and the callback URL that matches the Composio auth config (v3, legacy v1, or a proxy). (GitHub + Composio.)
3. Decide device flow and whether to leave expiring tokens enabled. (GitHub.)
4. Register the application and copy the client id and client secret into a Composio custom auth config, then pass that auth config id on the session. (Composio.)
5. The end user authorizes the requested scopes. (GitHub.)
6. If the target organization has OAuth app access restrictions, a member requests access and an owner grants it. (GitHub; conditional.)

### 9. Approval wait

**unknown** for registering or authorizing a GitHub OAuth app. No credible official figure was found. Organization-owner approval has steps and no published duration.

The legacy Composio sentence "getting OAuth approvals takes time" is not a GitHub timeline. ([Custom Auth Configs](https://docs.composio.dev/docs/auth-configuration/custom-auth-configs).)

### 10. Documented versus tested

Every GitHub claim above is **documented (not executed)** or **uncertain**. No GitHub OAuth app was created, no token was issued, and no Composio GitHub connection was opened.

---

## Google Calendar

This section is the Calendar API, not Gmail and not a generic Google sign-in. Scopes below are Calendar API scope URIs.

### 1. Is Composio managed OAuth available, and how was that checked?

**documented (not executed).** Yes, on Composio's catalog and toolkit page.

- [Managed OAuth apps](https://docs.composio.dev/toolkits/managed-auth) lists Google Calendar / `GOOGLECALENDAR`.
- [Google Calendar toolkit](https://docs.composio.dev/toolkits/googlecalendar) says "Auth: OAUTH2" and "Composio-managed OAuth available? Yes."

**Gap.** `composio_managed_auth_schemes` was not called. The toolkit FAQ points at "How to create OAuth2 credentials for Google Apps" without the destination URL in the markdown fetch. The matching public how-to is [composio.dev/auth/googleapps](https://composio.dev/auth/googleapps). That guide's worked example is Gmail, then says the same client can be reused after enabling other APIs, including Google Calendar API. It is not a Calendar-only page.

### 2. When does a developer need their own Google OAuth client?

**documented (not executed), Composio.** Not required to connect if managed auth is accepted. Own client when the consent screen must show the customer's name, when scopes beyond the managed app are needed, or when quota must be dedicated. ([Managed vs custom auth](https://docs.composio.dev/docs/authentication/custom-app-vs-managed-app); [Google OAuth setup and consent](https://docs.composio.dev/kb/guide/platform-google-oauth).)

The Calendar toolkit FAQ says the consent screen shows "Composio" until the developer creates their own OAuth app. ([Google Calendar toolkit](https://docs.composio.dev/toolkits/googlecalendar).)

**documented (not executed), Google.** Accessing a user's Calendar data with user consent uses an OAuth client ID, not an API key. ([Create access credentials](https://developers.google.com/workspace/guides/create-credentials).) That requirement is Google's, for a developer who is the OAuth client. It does not say a Composio customer must create a client when Composio already supplies one.

### 3. Official developer registration page

**documented (not executed).** There is no separate "Calendar developer signup." The official configuration pages are:

- OAuth consent / branding: [Configure the OAuth consent screen and choose scopes](https://developers.google.com/workspace/guides/configure-oauth-consent). Console path in that page: Menu → **Google Auth platform** → **Branding**.
- OAuth client: [Create access credentials](https://developers.google.com/workspace/guides/create-credentials). Console path: Menu → **Google Auth platform** → **Clients**.
- Calendar scope list: [Choose Google Calendar API scopes](https://developers.google.com/workspace/calendar/api/auth).

The Composio how-to tells the reader to open Google Cloud Console, enable an API from the API Library, then use the OAuth consent screen. ([composio.dev/auth/googleapps](https://composio.dev/auth/googleapps).)

### 4. Configuration and callback URI

**documented (not executed), Google consent screen.** [Configure the OAuth consent screen](https://developers.google.com/workspace/guides/configure-oauth-consent): app name, user support email, audience (user type), developer contact email, agreement to the Google API Services User Data Policy, then Create. If the user type is External, add test users under Audience. For an app used outside the Workspace organization, open Data Access → Add or Remove Scopes. "All apps using OAuth 2.0 require a consent screen configuration, but you only need to list scopes for apps used by people outside your Google Workspace organization." "For apps used only internally by your Google Workspace organization, scopes aren't listed on the consent screen and use of restricted or sensitive scopes doesn't require further review by Google."

**documented (not executed), Google client.** [Create access credentials](https://developers.google.com/workspace/guides/create-credentials), Web application: Create Client → Web application → name → authorized JavaScript origins for browser apps and/or authorized redirect URIs for server-side apps → Create. Optional and irreversible: "If your app is an AI agent that takes actions on behalf of users, select **Use this client for an AI-powered agent**." The page says if the app does both, create separate clients. It does not say a Composio integration must check that box. **uncertain** whether Composio's token exchange expects that flag.

**Contradiction on client secrets.** The same create-credentials page says "Note that client secrets aren't used for Web applications." [Using OAuth 2.0 for Web Server Applications](https://developers.google.com/identity/protocols/oauth2/web-server) still says to download `client_secret.json` and "Your application's client secret will only be shown after you create the client." [composio.dev/auth/googleapps](https://composio.dev/auth/googleapps) says that after the client exists, the developer creates a client secret and pastes client id and client secret into Composio. Composio's custom OAuth docs require `client_id` and `client_secret`. These pages were all fetched on 21 October 2026 and do not agree. This was not executed, so it is unknown which console behavior a new Web client shows today.

**documented (not executed), Composio callback.** Current docs: register `https://backend.composio.dev/api/v3/toolkits/auth/callback` unless the auth config still defaults to `https://backend.composio.dev/api/v1/auth-apps/add`. ([Programmatic auth configs](https://docs.composio.dev/docs/authentication/programmatic-auth-configs).)

**documented (not executed), Composio how-to still shows v1.** [composio.dev/auth/googleapps](https://composio.dev/auth/googleapps) tells the reader to put this exact redirect on the Google client and in the Composio auth config:

`https://backend.composio.dev/api/v1/auth-apps/add`

That how-to is not marked legacy. Current `docs.composio.dev` says v1 remains supported and that some toolkit defaults still use it. A developer who follows only the how-to will register v1; a developer who follows only the current programmatic page will register v3. They must match each other. The how-to also suggests `https://platform.composio.dev` as an authorized JavaScript origin "if you're trying it out on the dashboard." That origin is not the OAuth redirect.

**documented (not executed), enabling the API.** Composio's Calendar FAQ: for custom credentials, "the Google Calendar API must be enabled in the Google Cloud project that owns those credentials," under APIs & Services, then "wait a few minutes, and retry." ([Google Calendar toolkit](https://docs.composio.dev/toolkits/googlecalendar).) The Google how-to says enable Google Calendar API in the API Library and reuse or create an OAuth client. ([composio.dev/auth/googleapps](https://composio.dev/auth/googleapps).) Google's own "few minutes" wait was not found on the Calendar auth page; the wait sentence is Composio's.

### 5. Scopes

**documented (not executed), Google does not name one minimum Calendar scope.** [Choose Google Calendar API scopes](https://developers.google.com/workspace/calendar/api/auth): "Generally, you should choose the most narrowly focused scope possible and avoid requesting scopes that your app doesn't require." The same sentence is on [Configure the OAuth consent screen](https://developers.google.com/workspace/guides/configure-oauth-consent). [OAuth 2.0 Scopes for Google APIs](https://developers.google.com/identity/protocols/oauth2/scopes): "Many scopes overlap, so it's best to use a scope that isn't sensitive." Sensitive scopes "have a sensitive indicator on the Google Cloud Console's OAuth consent screen configuration page." The fetched scope tables do not print that indicator next to each Calendar URI.

Calendar API scopes on the Calendar auth page (wording shortened only by the table's own "Meaning" column):

| Scope | Meaning on the Calendar auth page |
| --- | --- |
| `https://www.googleapis.com/auth/calendar` | See, edit, share, and permanently delete all the calendars you can access using Google Calendar. |
| `https://www.googleapis.com/auth/calendar.readonly` | See and download any calendar you can access using your Calendar. |
| `https://www.googleapis.com/auth/calendar.freebusy` | View your availability in your calendars. |
| `https://www.googleapis.com/auth/calendar.events` | View and edit events on all your calendars. |
| `https://www.googleapis.com/auth/calendar.events.readonly` | View events on all your calendars. |
| `https://www.googleapis.com/auth/calendar.settings.readonly` | View your Calendar settings. |
| `https://www.googleapis.com/auth/calendar.addons.execute` | Run as a Calendar add-on. |
| `https://www.googleapis.com/auth/calendar.addons.current.event.read` | See the events you open in Google Calendar. |
| `https://www.googleapis.com/auth/calendar.addons.current.event.write` | Edit the events you open in Google Calendar. |
| `https://www.googleapis.com/auth/calendar.events.owned` | See, create, change, and delete events on Google calendars you own. |
| `https://www.googleapis.com/auth/calendar.events.owned.readonly` | See the events on Google calendars you own. |
| `https://www.googleapis.com/auth/calendar.events.freebusy` | See the availability on Google calendars you have access to. |
| `https://www.googleapis.com/auth/calendar.app.created` | Make secondary Google calendars, and see, create, change, and delete events on them. |
| `https://www.googleapis.com/auth/calendar.calendarlist` | See, add, and remove Google calendars you're subscribed to. |
| `https://www.googleapis.com/auth/calendar.calendarlist.readonly` | See the list of Google calendars you're subscribed to. |
| `https://www.googleapis.com/auth/calendar.calendars` | See and change the properties of Google calendars you have access to, and create secondary calendars. |
| `https://www.googleapis.com/auth/calendar.calendars.readonly` | See the title, description, default time zone, and other properties of Google calendars you have access to. |
| `https://www.googleapis.com/auth/calendar.acls` | See and change the sharing permissions of Google calendars you own. |
| `https://www.googleapis.com/auth/calendar.acls.readonly` | See the sharing permissions of Google calendars you own. |
| `https://www.googleapis.com/auth/calendar.events.public.readonly` | See the events on public calendars. |

**documented (not executed), one method, not a product scope.** [Events: list](https://developers.google.com/workspace/calendar/api/v3/reference/events/list) says that method "allows authorization with at least one of" `calendar.readonly`, `calendar`, `calendar.events.readonly`, `calendar.events`, `calendar.app.created`, `calendar.events.freebusy`, `calendar.events.owned`, `calendar.events.owned.readonly`, and `calendar.events.public.readonly` (full URIs on the page). That is the accepted set for listing events. It is not Google's instruction to request all of them, and it is not a statement about other Calendar methods. `events.insert` and similar write methods were not fetched, so a write minimum was not taken from a method page.

**documented (not executed), Composio tool requirement, not Google's minimum.** [Google Calendar knowledge base](https://docs.composio.dev/kb/guide/toolkits-google-calendar): "Ensure the connected account has `https://www.googleapis.com/auth/calendar.events` when calling event-list or event-fetch tools that require event access." That is narrower than "Composio's default scopes" and broader than Google's events.list rule, which also accepts `calendar.events.readonly`. Composio's managed default scope list was **not found**.

**Classification, only as current Google pages state it.**

- **Restricted:** [Restricted Scopes](https://support.google.com/cloud/answer/13464325) lists Gmail, Drive, Fit, Chat, Data Portability, Photos Ambient, and Google Health scopes. No `calendar` scope appears on that fetched page. **documented (not executed)** that Calendar scopes are absent from that restricted list. **uncertain** whether a later console label could still mark one as restricted; the static list does not.
- **Sensitive:** [Sensitive scope verification](https://developers.google.com/identity/protocols/oauth2/production-readiness/sensitive-scope-verification) says "Examples of sensitive scopes include reading events stored in Google Calendar" and does not name the URI. The scopes reference says the sensitive indicator is shown in Cloud Console, not in the public table. Per-URI sensitive versus non-sensitive labels for Calendar were **not found**. **uncertain** which Calendar URIs are sensitive.
- Adding scopes in Cloud Console groups them into "non-sensitive, sensitive, or restricted." ([Sensitive scope verification](https://developers.google.com/identity/protocols/oauth2/production-readiness/sensitive-scope-verification).) That grouping was not observed in a project.

[OAuth App Verification Help Center](https://support.google.com/cloud/answer/13463073): "Apps that request access to scopes categorized as sensitive or restricted must complete Google's OAuth app verification before being granted access" when publishing to users beyond the exceptions below. "If your app utilizes only non-sensitive scopes, it is not mandatory for your app to complete the app verification process." Brand verification is still required "if you want your app to display an app name and logo on the OAuth consent screen."

Because the public Calendar tables do not mark each URI, this note does not assign `calendar.events` or `calendar.readonly` to sensitive or non-sensitive.

### 6. Registering, consent, and verification

**(a) Registering the developer app.** **documented (not executed).** Create a Google Cloud project, configure the consent screen, enable Calendar API if using that project's client, create an OAuth client, and add the redirect URI. No Google page said that registration itself is a review queue.

**(b) End-user consent.** **documented (not executed).** "When your app is installed, a user is asked to validate the scopes used by the app." ([Calendar auth](https://developers.google.com/workspace/calendar/api/auth).) In Testing, Google "will display a warning message before allowing a specified test user to authorize scopes." ([Setting up your OAuth consent screen](https://support.google.com/cloud/answer/10311615).) Workspace admins can block the app. ([OAuth app state overview](https://developers.google.com/identity/protocols/oauth2/production-readiness/overview).)

**(c) Publishing / verification.** Verification is not implied by the mere use of OAuth. Google's pages tie it to audience and scope class:

- **Internal** user type, organization-owned project: "Verification is not required." ([OAuth app state overview](https://developers.google.com/identity/protocols/oauth2/production-readiness/overview).) An organization administrator might still have to approve it. ([Sensitive scope verification](https://developers.google.com/identity/protocols/oauth2/production-readiness/sensitive-scope-verification), Internal use only.)
- **External + Testing:** verification is not required. "If your app is in the development, testing, or staging phases, verification isn't required." Publishing status stays **Testing**. Only listed test users can authorize, with the identity-scope exception below. ([Sensitive scope verification](https://developers.google.com/identity/protocols/oauth2/production-readiness/sensitive-scope-verification).)
- **External + Published + sensitive or restricted scopes:** "Required for public apps that request sensitive and restricted scopes." ([OAuth app state overview](https://developers.google.com/identity/protocols/oauth2/production-readiness/overview).) Unverified published apps that request those scopes show "unverified app warnings" and "a hard cap of 100 total users."
- **External + only non-sensitive scopes:** app verification is not mandatory; brand verification is required to show the app name and logo. ([OAuth App Verification Help Center](https://support.google.com/cloud/answer/13463073).)
- **Personal use / few known users:** the sensitive-scope page says you do not need to submit for review and users can pass the unverified screen.
- **Domain-wide installation:** brand verification is not required, but "if your app utilizes restricted or sensitive scopes, app verification is required." ([Sensitive scope verification](https://developers.google.com/identity/protocols/oauth2/production-readiness/sensitive-scope-verification).)

Composio's own page tells customers who add scopes beyond the managed app to "complete Google's required verification before requesting additional scopes." ([Google OAuth setup and consent](https://docs.composio.dev/kb/guide/platform-google-oauth).) That is Composio describing Google's rule for extra scopes on a customer-owned client. It does not say the managed Composio app is unverified.

### 7. Documented blockers and remedies

| Blocker | Source | Remedy stated there |
| --- | --- | --- |
| "App is blocked" / unverified extra scopes | Composio Calendar FAQ: the client is "requesting scopes that Google hasn't verified." Usually "extra scopes beyond the defaults." ([Google Calendar toolkit](https://docs.composio.dev/toolkits/googlecalendar).) | Remove the extra scopes, or submit the scopes on your own OAuth app. |
| Unverified warning while testing | Calendar troubleshooter: if the screen says the app isn't verified and the app uses sensitive scopes, verification is required to remove the warning. "During the development phase, you can continue past this warning by selecting Advanced > Go to {Project Name} (unsafe)." ([Troubleshoot authentication](https://developers.google.com/workspace/calendar/api/troubleshoot-authentication-authorization).) | That click-through, or verification before public launch. |
| Testing audience | External + Testing: "limited to up to 100 test users." "A test user consumes a project's test user quota once added." Authorizations "expire seven days from the time of consent." A refresh token from an offline request "will also expire." ([Setting up your OAuth consent screen](https://support.google.com/cloud/answer/10311615); same text on [Manage App Audience](https://support.google.com/cloud/answer/15549945).) | Add test users, or publish. The 7-day rule's exception is only "name, email address, and user profile" via `userinfo.email`, `userinfo.profile`, `openid`, or their OpenID Connect equivalents. "If your app requests any other OAuth scopes, then this exception does not apply." Calendar API scopes are not in that identity list. |
| Published but unverified, sensitive or restricted | Hard cap of 100 total users and a danger warning. ([OAuth app state overview](https://developers.google.com/identity/protocols/oauth2/production-readiness/overview).) | Complete the verification that matches the scope class. |
| `invalid_scope` | Composio Calendar FAQ: scopes "invalid or incorrectly formatted." | Check values against Google's scope docs. |
| Calendar API not enabled | Composio: "Google Calendar API has not been used in project" when using custom credentials. | Enable the API on that project and wait a few minutes (Composio's wait, not a Google SLA). |
| Redirect mismatch | Composio: provider URI must equal `oauth_redirect_uri`. | Register v3, legacy v1, or the proxy, in both places. |
| Refresh tokens stop working | Google: user revoked access; refresh token unused for six months; password change if the token contains Gmail scopes; "limit of 100 refresh tokens per Google Account per OAuth 2.0 client ID" (oldest is invalidated); admin restricted the service (`admin_policy_enforced`); Testing status issues a refresh token "expiring in 7 days" unless only the identity scopes above were requested. ([Using OAuth 2.0 to Access Google APIs](https://developers.google.com/identity/protocols/oauth2).) | Re-authenticate. Composio's Calendar FAQ says a 401 can also follow revoked access, password or 2FA change, Workspace policy, or "Google's refresh token limit (~50 per account)." The "~50" figure conflicts with Google's "100 ... per OAuth 2.0 client ID." See contradictions. |
| Workspace admin block | Admins can Block any OAuth app. Trusted status can override the 100-user cap and the 7-day testing refresh-token limit for that org's users. ([OAuth app state overview](https://developers.google.com/identity/protocols/oauth2/production-readiness/overview).) | An admin marks the app Trusted, Limited, or Blocked. Not something the OAuth registration form does by itself. |
| HTTPS-only scopes | [Manage App Data Access](https://support.google.com/cloud/answer/15549135): "Certain scopes might be unavailable because usage of these scopes is restricted to projects using HTTPS URLs only." It does not name Calendar. | Remove non-HTTPS URLs from the client. **uncertain** whether any Calendar scope is in that set. |

### 8. Hands-on work

Duration: **unknown**. The pages list steps and do not time them. Unverified editorial inventory:

Managed auth, as Composio describes it: no Google Cloud project. The user consents to Composio's app. Not executed.

Own Google client, documented steps:

1. Create or choose a Google Cloud project. (Composio how-to; Google console.)
2. Configure Branding / consent screen: app name, support email, Internal or External, contact email, policy acknowledgement. (Google.)
3. If External, add test users while status is Testing. (Google.)
4. Enable Google Calendar API on that project if this client will call it. (Composio how-to and Calendar FAQ.)
5. Create a Web OAuth client and add the authorized redirect URI that matches Composio (v3 in current docs, v1 in the how-to). (Google + Composio.)
6. Resolve client id and client secret against the contradictory secret notes, then paste them into a Composio custom auth config. (Composio.) Not executed, so step 6's secret field is **uncertain**.
7. If the app will be public and the requested Calendar scopes are in a class Google marks sensitive or restricted, submit brand verification and the matching scope verification. Whether a given Calendar URI is in that class was not on the public tables.
8. The end user consents.

### 9. Approval wait

Only figures that an official page states. They conflict. None were tested. They apply when verification is actually required (see section 6), not to every OAuth connection.

| Source | What it says |
| --- | --- |
| [Sensitive scope verification](https://developers.google.com/identity/protocols/oauth2/production-readiness/sensitive-scope-verification) | "The sensitive scope verification process typically takes 3-5 business days to complete." Brand review on that page: "The automated review usually completes in a few minutes," then the developer publishes branding. "Compliant verification results are valid for 7 days" if branding is not published. |
| [Restricted scope verification](https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification) | "The restricted scopes verification process can potentially take several weeks to complete." "All apps must complete the brand verification step first, which typically takes 2-3 business days, if branding information has changed since the last approved OAuth consent screen verification." Annual security assessment if restricted-scope data is accessed from or through a third-party server. |
| [OAuth verification FAQ](https://support.google.com/cloud/answer/13463817) | Table of "Expected time of completion": Brand Verification "2-3 Business days"; Sensitive Scope Verification "10 Business days"; Restricted Scope Verification "6 weeks." Footnote: "these estimates are not guaranteed and will vary based on developer responsiveness." |

Calendar scopes were not on the restricted list that was fetched, so the restricted-scope "several weeks" / "6 weeks" figures are **not** applied to Calendar here. The sensitive-scope "3-5 business days" and the FAQ's "10 Business days" both exist and disagree. Which Calendar URIs need that sensitive review was **not found** on the scope tables. The sensitive-scope page's example "reading events stored in Google Calendar" is an example, not a classification of `calendar.events` versus `calendar.events.readonly`.

No official page gave a wait time for enabling the Calendar API or for creating the OAuth client.

### 10. Documented versus tested

Every Google claim above is **documented (not executed)** or **uncertain**. No Cloud project was created, no consent screen was submitted, and no Calendar scope was granted.

---

## Slack

Slack app creation and OAuth v2 are separate from Slack Marketplace review.

### 1. Is Composio managed OAuth available, and how was that checked?

**documented (not executed).** Yes, on Composio's catalog and toolkit page.

- [Managed OAuth apps](https://docs.composio.dev/toolkits/managed-auth) lists Slack / `SLACK` (and separately Slackbot / `SLACKBOT`).
- [Slack toolkit](https://docs.composio.dev/toolkits/slack) says "Auth: OAUTH2" and "Composio-managed OAuth available? Yes."

**documented (not executed).** [How to Set Up Slack OAuth 2.0 with Composio](https://composio.dev/auth/slack) says managed auth "provides the Slack OAuth app" and "there's no need to create your own app or handle credentials," and it calls managed auth "Recommended" for getting started. The dashboard step says "review the scopes" under Composio Managed. The fetched page does not print those default scopes.

**Gap.** `composio_managed_auth_schemes` was not called. Composio says it "is working on Marketplace review for the managed Slack app." ([Slack toolkit FAQ](https://docs.composio.dev/toolkits/slack).) That is a Composio statement about listing, not a statement that managed OAuth is unavailable.

### 2. When does a developer need their own Slack app?

**documented (not executed), Composio.** Not required for a first connection if managed auth is accepted and the workspace allows the install. Own app when:

- The consent screen or Slack app identity must be the developer's. ([White-labeling authentication](https://docs.composio.dev/docs/authentication/white-labeling-authentication).)
- Custom scopes or dedicated quota are required. ([Managed vs custom auth](https://docs.composio.dev/docs/authentication/custom-app-vs-managed-app).)
- The workspace blocks non-Marketplace apps. The toolkit FAQ says the flow "can still work if the workspace allows non-Marketplace apps," and until Composio's Marketplace review finishes, "use the workspace's own Slack OAuth app or ask a workspace admin to approve the app if the warning blocks users."

**documented (not executed), Slack.** A developer who is the app owner must create an app. That is Slack's rule for their own app, not a rule that Composio customers must create one when they use Composio's app.

### 3. Official developer registration page

**documented (not executed).** [https://api.slack.com/apps](https://api.slack.com/apps) is Slack's app dashboard. Fetched 21 October 2026, it says "You'll need to sign in to your Slack account to create an application."

[Creating an app from app settings](https://docs.slack.dev/app-management/quickstart-app-settings): from the apps page, choose a blank app, enter an app name, select the workspace where the app will be developed, and create it. "You'll be able to distribute your app to other workspaces later if you choose."

The Composio how-to says "Go to the Slack API Dashboard and click Create New App," then "from scratch," name, and workspace. ([composio.dev/auth/slack_custom](https://composio.dev/auth/slack_custom).)

### 4. Configuration and callback URI

**documented (not executed), Slack OAuth v2.** [Installing via OAuth](https://docs.slack.dev/authentication/installing-with-oauth):

- Authorize at `https://slack.com/oauth/v2/authorize` (GovSlack uses `https://slack-gov.com/oauth/v2/authorize`).
- `scope` is the bot-user scope list. `user_scope` is the user-token scope list. Either or both may be sent.
- "The `redirect_uri` must use HTTPS." A Redirect URL configured under OAuth & Permissions "must also use HTTPS."
- "Your `redirect_uri` must match or be a subdirectory of a Redirect URL configured under App Management." A Redirect URL cannot contain `#`.
- If several Redirect URLs are configured, the same `redirect_uri` must be sent on authorize and on `oauth.v2.access`, or Slack returns `bad_redirect_uri`. The page also uses the parameter name `redirect_url` in that error sentence. **uncertain** whether that is a second parameter or a wording slip; the examples and the match rule use `redirect_uri`.
- If `redirect_uri` is omitted and several Redirect URLs exist, Slack uses the first listed URL.
- Exchange the code at `https://slack.com/api/oauth.v2.access` with `code`, `client_id`, and `client_secret`. "That's your temporary authorization code, which expires after ten minutes."
- Bot token comes back as `token_type: bot` (prefix `xoxb-` in the example). User token, if requested, is under `authed_user`.

**documented (not executed), Composio.** [Slack knowledge base](https://docs.composio.dev/kb/guide/toolkits-slack): "`scopes` refers to bot-user scopes." User-token permissions go in `user_scopes`. "The short `/api/v3/s/...` URL is not the `redirect_uri` sent to Slack." The redirect URI "is available in the authConfig and must match what is configured in the Slack OAuth app."

Current Composio callback, if not overridden: `https://backend.composio.dev/api/v3/toolkits/auth/callback`. Legacy default that "remains supported": `https://backend.composio.dev/api/v1/auth-apps/add`.

**documented (not executed), Composio how-to still shows v1.** [composio.dev/auth/slack_custom](https://composio.dev/auth/slack_custom) says to add and save this Redirect URL, and to put the same value in the Composio auth config:

`https://backend.composio.dev/api/v1/auth-apps/add`

Slack's HTTPS rule is satisfied by both the v1 and v3 Composio URLs. Exact match with the auth config is still required. Composio's Slack FAQ: on mismatch, "Update the redirect URL in your Slack App under OAuth & Permissions → Redirect URLs."

**documented (not executed), distribution versus owning workspace.** [App lifecycle & distribution](https://docs.slack.dev/app-management/distribution): "By default, a newly built Slack app can only be installed in its associated workspace." Installing elsewhere requires an OAuth flow and then **Activate Public Distribution** under Manage Distribution → Share Your App with Other Workspaces, after the checklist. That activation is "unlisted" distribution. It is not Marketplace listing. OAuth redirect URLs for apps installed by other workspaces must support SSL.

### 5. Scopes

**documented (not executed), Slack does not publish one universal minimum.** [Installing via OAuth](https://docs.slack.dev/authentication/installing-with-oauth): "While developing your app, you'll determine a minimum list of scopes that your app requires to work." Bot scopes and user scopes are different parameters. Scopes already granted are additive. "There is no way to remove scopes from an existing token without revoking it entirely." "OAuth tokens do not expire" unless rotated or revoked. Revocation happens if the app is uninstalled, the user removes their configuration, or the installing user's account is deactivated. Token rotation is optional and exchanges the access token for a refresh token and an expiring access token.

**documented (not executed), tutorial scopes, not a product minimum.** The app-settings quickstart, whose goal is "a basic Slack app that can send messages using webhooks," says to add bot scopes `chat:write` and `channels:read`. It also says `chat:write.public` posts to public channels without joining; otherwise the app needs `conversations.join` or an invite. "In general, you'll add scopes to your bot token, not your user token," with user tokens for acting as a specific user. ([Creating an app from app settings](https://docs.slack.dev/app-management/quickstart-app-settings).) Those two scopes are the tutorial's choices.

**documented (not executed), Composio.** The custom Slack how-to says "Composio typically uses Bot Token Scopes" and gives examples: `channels:history` to read channel messages, `chat:write` to send, `users:read` to read user info, and "if your agent only needs to send messages, `chat:write` alone might be enough." It also prints a long comma-separated list under "Scopes Supported by Composio" (`calls:read` through `links:write`). That heading is "supported," not "requested by default." ([composio.dev/auth/slack_custom](https://composio.dev/auth/slack_custom).)

**Composio default scopes: not found.** The managed-auth how-to says to review scopes in the dashboard and does not list them. The API's `user_scopes.available` ceiling was not called.

Sign in with Slack user scopes cannot be combined with non-SIWS scopes in one OAuth flow. ([Installing via OAuth](https://docs.slack.dev/authentication/installing-with-oauth).)

### 6. Registering, consent, and Marketplace review

**(a) Creating the app.** **documented (not executed).** Create it at [api.slack.com/apps](https://api.slack.com/apps), pick the development workspace, add bot and/or user scopes, add an HTTPS Redirect URL, and install. The quickstart's install is: OAuth & Permissions → **Install to Workspace** → **Allow**. "When you follow this flow, you're playing the part of the installing user." No Marketplace submission is in those steps.

**(b) End-user / installer consent.** **documented (not executed).** OAuth is "requesting scopes," "waiting for a user to approve," and exchanging the code. ([Installing via OAuth](https://docs.slack.dev/authentication/installing-with-oauth).) Some workspaces allow only admins to install, or only Marketplace apps. Workspaces can require admin approval so members request install instead of completing it. ([App lifecycle & distribution](https://docs.slack.dev/app-management/distribution).)

**(c) Distribution and Marketplace review, which are not the same as creating an app.**

- Undistributed: one workspace, the one selected at creation. ([App lifecycle & distribution](https://docs.slack.dev/app-management/distribution).)
- Unlisted public distribution: **Activate Public Distribution** after the checklist. Slack says this is for pilots. "Apps intended for commercial distribution should be submitted and approved for listing in the Slack Marketplace." That sentence is Slack's recommendation for commercial listing, not a rule that an unlisted app cannot be installed on other workspaces after public distribution is activated.
- Marketplace: a separate submission. Prerequisites include a working app, testing on a non-development workspace, and "Your app has been installed on 10 or more active workspaces." ([Slack Marketplace review process](https://docs.slack.dev/slack-marketplace/slack-marketplace-review-guide).)

Composio, not Slack, says its managed Slack app is still in Marketplace review and that non-Marketplace installs can work when the workspace allows them. ([Slack toolkit](https://docs.composio.dev/toolkits/slack).)

### 7. Documented blockers and remedies

| Blocker | Source | Remedy stated there |
| --- | --- | --- |
| `invalid_team_for_non_distributed_app` | "Occurs when attempting to install/authorize an undistributed Slack API app on a team where the app was not created." ([Installing via OAuth](https://docs.slack.dev/authentication/installing-with-oauth).) | Install on the owning workspace, or activate public distribution before installing elsewhere. |
| `bad_redirect_uri` | Multiple redirect values that do not match across authorize and access. Also HTTP, wrong host, wrong port, or a non-subdirectory path in the examples. | HTTPS, exact match or allowed subdirectory, same `redirect_uri` on both steps. |
| Redirect mismatch in Composio's words | Slack FAQ: update OAuth & Permissions → Redirect URLs. The short `/api/v3/s/...` link is not the redirect URI. | Put the auth config's callback (v3, legacy v1, or proxy) on the Slack app. |
| `invalid_scope` | Non-existent scope, or SIWS scopes combined with non-SIWS scopes. | Request a real scope, and split SIWS from other user scopes into separate flows. |
| `unapproved_scope` | "Attempting to install a published app for which the requested scopes aren't approved either because they're still in review for that app, or they weren't yet submitted for review." | Submit and get those scopes approved before requesting them on a published Marketplace app. This does not, on that page, apply to an unpublished app. |
| Authorization code | Expires after ten minutes. | Restart the install. Not tested. |
| "This app isn't listed in the Slack Marketplace" | Composio FAQ: a member installing a non-Marketplace app. Slack distribution page: some workspaces only allow Marketplace apps. | Composio: disable **Require apps from Slack Marketplace** under Settings → Apps & Workflows → App Management Settings, or use an admin approval, or use the workspace's own app. |
| "Require approved apps" | Composio FAQ: Slack asks an admin or owner to approve before install finishes. | Owner approves, or disable that setting, or install as an owner. "When installing non-Marketplace apps, you'll need to be an owner to install directly." A member requests approval. |
| Missing bot scope / insufficient scopes | Composio FAQ. | Add the bot scope under OAuth & Permissions, and configure every scope from the auth config on the Slack app. Reinstall after scope changes. Slack: scope changes require reinstall for existing installs. ([App lifecycle & distribution](https://docs.slack.dev/app-management/distribution).) |
| Org-incompatible scopes | `scope_not_allowed_on_enterprise`. The fetched page starts a list under "Non-Enterprise scopes" and the extract ended at `bot`. The full list was not captured. | **uncertain** beyond the error name. |
| Tokens | Slack says OAuth tokens do not expire. They are revoked on uninstall, user removal, or deactivation of the installing user. | `auth.revoke`, or token rotation if expiring tokens are wanted. |

### 8. Hands-on work

Duration: **unknown**. Steps are listed by Slack and Composio without durations. Unverified editorial inventory:

Managed auth: Composio's Slack how-to steps are add the toolkit, choose Composio Managed, review scopes, create the auth config, and have a user Allow the install on a workspace that permits that app. Not executed. If the workspace requires Marketplace apps or admin approval, those settings or an admin are extra human steps. Composio does not give a date for its own Marketplace review.

Own Slack app, documented steps:

1. Sign in at api.slack.com/apps and create a blank app in a development workspace.
2. Add the minimum bot scopes and, if acting as a user, user scopes. Slack does not name that minimum; the quickstart uses `chat:write` and `channels:read` for its messaging example.
3. Add one HTTPS Redirect URL that matches the Composio auth config.
4. Copy client id and client secret into Composio. The custom how-to also asks for a verification token for triggers.
5. Install to the owning workspace and click Allow.
6. To install on any other workspace, finish Slack's distribution checklist and click Activate Public Distribution.
7. Marketplace submission is a further, optional path with its own prerequisites, including 10 active workspaces.

### 9. Approval wait

**unknown** for creating an app, installing it on the workspace that owns it, or activating unlisted public distribution. No official duration was found for those.

**documented (not executed) for Marketplace review only**, which is not required to create an app. [Slack Marketplace review process](https://docs.slack.dev/slack-marketplace/slack-marketplace-review-guide):

- "The preliminary part of the review takes up to 10 business days to receive feedback."
- "The functional review takes up to 10 weeks for new submissions and 6 weeks for published apps resubmitting changes."
- The same page says turnaround "can vary depending on volume" and "We are unable to skip or accelerate the review process."
- Resubmitting during preliminary review "resets" the place in the queue. After a functional reviewer is assigned, resubmission does not reset the queue.
- The distribution guide's submission chapter uses the same "up to 10 business days" and "up to 10 weeks" wording. ([Distributing your app in the Slack Marketplace](https://docs.slack.dev/slack-marketplace/distributing-your-app-in-the-slack-marketplace/).)

Composio's "working on Marketplace review" sentence has **no** duration. **unknown** when that managed app will be listed.

### 10. Documented versus tested

Every Slack claim above is **documented (not executed)** or **uncertain**. No Slack app was created, no token was exchanged, and no Composio Slack connection was opened.

---

## Contradictions and incomplete evidence

1. **Callback URL, current docs versus how-to site.** `docs.composio.dev` (programmatic auth configs, legacy custom auth configs, current and legacy white-labeling) tells bring-your-own setups to use `https://backend.composio.dev/api/v3/toolkits/auth/callback`, and says `https://backend.composio.dev/api/v1/auth-apps/add` remains supported because some toolkit defaults still use it. [composio.dev/auth/googleapps](https://composio.dev/auth/googleapps) and [composio.dev/auth/slack_custom](https://composio.dev/auth/slack_custom) still instruct the reader to register the v1 URL. [composio.dev/auth/github](https://composio.dev/auth/github) says a screenshot showed v1 and that current docs point at v3. All of these pages were live on 21 October 2026.

2. **Own app: required versus recommended.** The legacy custom-auth page says own developer apps are recommended for production and that Composio supplies a default app because "OAuth approvals take time." The current managed-vs-custom page says managed auth is the default and own credentials are for branding, scopes, quota, polling, custom instances, or enterprise branding. The GitHub how-to says own credentials are the recommended production route. None of these say managed auth is unavailable for GitHub, Google Calendar, or Slack.

3. **Google client secret.** [Create access credentials](https://developers.google.com/workspace/guides/create-credentials) says client secrets are not used for Web applications. [Web server OAuth](https://developers.google.com/identity/protocols/oauth2/web-server) still tells the developer to download `client_secret.json` once. Composio's Google how-to and custom auth config both require a client secret. Not executed.

4. **Google verification duration.** Sensitive-scope developer page: typically 3–5 business days. Verification FAQ: Sensitive Scope Verification expected 10 business days, and the estimate is not guaranteed. Brand verification is "a few minutes" of automated review on the sensitive-scope page, and "2–3 business days" on the restricted-scope page (if branding changed) and in the FAQ. Restricted-scope review is "several weeks" on the developer page and "6 weeks" in the FAQ. Calendar scopes were not on the restricted-scope list, so those restricted figures are not used as a Calendar wait.

5. **Calendar scope class.** The public Calendar scope tables do not label each URI sensitive or restricted. The restricted-scope help page does not list Calendar. The sensitive-scope page's example "reading events stored in Google Calendar" does not name a URI. Console classification was not observed.

6. **Refresh-token cap.** Google documents "100 refresh tokens per Google Account per OAuth 2.0 client ID." Composio's Calendar FAQ says "Google's refresh token limit (~50 per account)." Both were fetched. Neither was tested.

7. **Which Calendar scope is "minimal."** Google events.list accepts several scopes, including read-only event scopes. Composio's Calendar guide says event-list and event-fetch tools that need event access should have `calendar.events`. Those statements answer different questions.

8. **Slack `redirect_url` versus `redirect_uri`.** The OAuth page's error sentence says `redirect_url` values must match, while the parameter it tells developers to send is `redirect_uri`.

9. **Slack non-Enterprise scope list** was truncated in the fetch after the first item `bot`. The error name `scope_not_allowed_on_enterprise` is documented; the full incompatible list was not copied.

10. **Composio default scopes** for all three toolkits were not on the fetched pages. Code samples and "supported scopes" lists are not defaults. The recommend-scopes API is documented as experimental and was not called.

11. **Legacy banners.** [Custom Auth Configs](https://docs.composio.dev/docs/auth-configuration/custom-auth-configs) and [White-labeling (direct execution)](https://docs.composio.dev/docs/auth-configuration/white-labeling) both say they are legacy and point at `https://docs.composio.dev`. The current counterparts that were read are [Managed vs custom auth](https://docs.composio.dev/docs/authentication/custom-app-vs-managed-app) and [White-labeling authentication](https://docs.composio.dev/docs/authentication/white-labeling-authentication). The legacy pages still contain the v3 callback and the "v1 remains supported" note, which the current programmatic page also states.

---

## Unresolved questions

- What scope string Composio managed auth sends for `GITHUB`, `GOOGLECALENDAR`, and `SLACK` today. Not published on the pages fetched, and the toolkit API was not called.
- Whether Composio's managed GitHub app is a GitHub OAuth App or a GitHub App.
- Whether a new Google Web client still shows a client secret, given the conflict between the create-credentials page and the web-server guide.
- Which Calendar API scope URIs Google Cloud Console currently places in non-sensitive, sensitive, or restricted. The public tables do not say, and no project was opened.
- Which of Google's conflicting verification durations applies. They are estimates on the pages, and they were not experienced.
- Whether Composio's Google how-to (v1 callback, Gmail as the worked example) or the current v3 programmatic page is what the dashboard shows for a new Google Calendar auth config.
- The full Slack list of scopes that are not org-compatible.
- When, or whether, Composio will finish Marketplace review for its managed Slack app. Composio says the review is in progress and gives no date.
- Whether GitHub organization OAuth-app restrictions are enabled on any particular org. The docs describe the feature, not a default for every org.

---

## Claim ledger

| Claim | Status | Source |
| --- | --- | --- |
| GitHub, Google Calendar, and Slack are on Composio's managed OAuth list | documented (not executed) | https://docs.composio.dev/toolkits/managed-auth and each toolkit page |
| Live `composio_managed_auth_schemes` contains OAuth for those three | uncertain | Endpoint documented, not called |
| Own OAuth app is optional when managed auth exists | documented (not executed) | https://docs.composio.dev/docs/authentication/custom-app-vs-managed-app |
| Legacy page recommends own app for production and mentions approval time without a number | documented (not executed) | https://docs.composio.dev/docs/auth-configuration/custom-auth-configs |
| v3 callback and supported v1 callback | documented (not executed) | https://docs.composio.dev/docs/authentication/programmatic-auth-configs |
| Google and Slack how-tos still show only the v1 callback | documented (not executed) | https://composio.dev/auth/googleapps and https://composio.dev/auth/slack_custom |
| GitHub prefers GitHub Apps on the OAuth app creation page | documented (not executed) | https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-an-oauth-app |
| GitHub OAuth registration has no published staff-review wait | documented (not executed) that no such wait was found | Creation page and related authorizing docs |
| GitHub `(no scope)` is public read-only; no single product minimum is named | documented (not executed) | https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/scopes-for-oauth-apps |
| Expiring GitHub user tokens default on; 8-hour access token; 6-month idle refresh token | documented (not executed) | Creation page and authorizing page |
| Calendar scope table | documented (not executed) | https://developers.google.com/workspace/calendar/api/auth |
| Calendar scopes absent from the restricted-scope list | documented (not executed) | https://support.google.com/cloud/answer/13464325 |
| Per-URI Calendar sensitive classification | uncertain | Not on the fetched tables |
| Google sensitive review "3–5 business days" and FAQ "10 Business days" | documented (not executed), conflicting | Sensitive-scope page and https://support.google.com/cloud/answer/13463817 |
| External Testing: 100 test users and 7-day authorization expiry, except identity-only scopes | documented (not executed) | https://support.google.com/cloud/answer/10311615 |
| Slack bot `scope` versus user `user_scope`; HTTPS redirect; 10-minute code | documented (not executed) | https://docs.slack.dev/authentication/installing-with-oauth |
| Undistributed Slack app only installs on the owning workspace | documented (not executed) | Same page, error `invalid_team_for_non_distributed_app`, and distribution guide |
| Marketplace review up to 10 business days preliminary and up to 10 weeks functional (6 weeks for published resubmits) | documented (not executed) | https://docs.slack.dev/slack-marketplace/slack-marketplace-review-guide |
| Any of these OAuth flows succeed | not claimed | Not executed |

---

## Sources

### Composio, current docs (`docs.composio.dev`)

- Managed vs custom auth — https://docs.composio.dev/docs/authentication/custom-app-vs-managed-app
- Managed OAuth apps — https://docs.composio.dev/toolkits/managed-auth
- Programmatic auth configs — https://docs.composio.dev/docs/authentication/programmatic-auth-configs
- Controlling scopes — https://docs.composio.dev/docs/authentication/controlling-scopes
- White-labeling authentication — https://docs.composio.dev/docs/authentication/white-labeling-authentication
- Custom Auth Configs (page marked Legacy) — https://docs.composio.dev/docs/auth-configuration/custom-auth-configs
- White-labeling, direct execution (page marked Legacy) — https://docs.composio.dev/docs/auth-configuration/white-labeling
- GitHub toolkit — https://docs.composio.dev/toolkits/github
- Google Calendar toolkit — https://docs.composio.dev/toolkits/googlecalendar
- Slack toolkit — https://docs.composio.dev/toolkits/slack
- Google Calendar knowledge base — https://docs.composio.dev/kb/guide/toolkits-google-calendar
- Slack knowledge base — https://docs.composio.dev/kb/guide/toolkits-slack
- Google OAuth setup and consent — https://docs.composio.dev/kb/guide/platform-google-oauth
- Get toolkit by slug — https://docs.composio.dev/reference/api-reference/toolkits/getToolkitsBySlug

### Composio how-to site (`composio.dev/auth`)

- OAuth2 guide index — https://composio.dev/auth
- GitHub OAuth credentials — https://composio.dev/auth/github
- Google Apps OAuth2 credentials — https://composio.dev/auth/googleapps
- Slack OAuth 2.0 with Composio — https://composio.dev/auth/slack
- Slack custom OAuth credentials — https://composio.dev/auth/slack_custom

### GitHub

- Creating an OAuth app — https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-an-oauth-app
- Scopes for OAuth apps — https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/scopes-for-oauth-apps
- Authorizing OAuth apps — https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps
- Differences between GitHub Apps and OAuth apps — https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/differences-between-github-apps-and-oauth-apps
- Best practices for creating an OAuth app — https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/best-practices-for-creating-an-oauth-app
- Approving OAuth apps for your organization — https://docs.github.com/en/organizations/managing-oauth-access-to-your-organizations-data/approving-oauth-apps-for-your-organization
- Requesting organization approval for OAuth apps — https://docs.github.com/en/account-and-profile/how-tos/organization-membership/requesting-organization-approval-for-oauth-apps

### Google

- Choose Google Calendar API scopes — https://developers.google.com/workspace/calendar/api/auth
- OAuth 2.0 Scopes for Google APIs — https://developers.google.com/identity/protocols/oauth2/scopes
- Events: list — https://developers.google.com/workspace/calendar/api/v3/reference/events/list
- Configure the OAuth consent screen and choose scopes — https://developers.google.com/workspace/guides/configure-oauth-consent
- Create access credentials — https://developers.google.com/workspace/guides/create-credentials
- Using OAuth 2.0 for Web Server Applications — https://developers.google.com/identity/protocols/oauth2/web-server
- Using OAuth 2.0 to Access Google APIs — https://developers.google.com/identity/protocols/oauth2
- Sensitive scope verification — https://developers.google.com/identity/protocols/oauth2/production-readiness/sensitive-scope-verification
- Restricted scope verification — https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification
- OAuth app state overview — https://developers.google.com/identity/protocols/oauth2/production-readiness/overview
- Troubleshoot Calendar authentication and authorization — https://developers.google.com/workspace/calendar/api/troubleshoot-authentication-authorization
- Restricted Scopes (Help) — https://support.google.com/cloud/answer/13464325
- OAuth verification FAQ — https://support.google.com/cloud/answer/13463817
- OAuth App Verification Help Center — https://support.google.com/cloud/answer/13463073
- Setting up your OAuth consent screen — https://support.google.com/cloud/answer/10311615
- Manage App Audience — https://support.google.com/cloud/answer/15549945
- Manage App Data Access — https://support.google.com/cloud/answer/15549135
- Verification requirements — https://support.google.com/cloud/answer/13464321

### Slack

- Your Apps — https://api.slack.com/apps
- Creating an app from app settings — https://docs.slack.dev/app-management/quickstart-app-settings
- Installing via OAuth authorization code flow — https://docs.slack.dev/authentication/installing-with-oauth
- App lifecycle and distribution — https://docs.slack.dev/app-management/distribution
- Distributing your app in the Slack Marketplace — https://docs.slack.dev/slack-marketplace/distributing-your-app-in-the-slack-marketplace
- Slack Marketplace review process — https://docs.slack.dev/slack-marketplace/slack-marketplace-review-guide
