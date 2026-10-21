"""Official-doc seed content checked on 21 October 2026.

Nothing in this module is a tested integration. Status "verified" is intentionally unused.
"""

from __future__ import annotations

from datetime import date

CHECKED = date(2026, 10, 21)

EXECUTION_NOTE = (
    "No step in this guide was carried out for this project. No OAuth app was created, "
    "no consent screen was approved, and no token was exchanged. Documented claims quote "
    "or closely follow the sources. Uncertain claims were not settled by those sources."
)

REDIRECT_URI = "https://backend.composio.dev/api/v3/toolkits/auth/callback"

REDIRECT_NOTE = (
    "Composio says the provider redirect URI and the auth config must match exactly. "
    "The older callback https://backend.composio.dev/api/v1/auth-apps/add remains supported "
    "when that same URL is set in both places. A mismatch is documented as redirect_uri_mismatch."
)

COMPOSIO_PAGE_NOTE = (
    "Current Composio authentication pages and the managed-OAuth catalog were read on "
    "21 October 2026. The legacy custom-auth page is marked legacy and points readers at "
    "current docs. This project did not call the toolkit API and did not open a signed-in "
    "Composio project, so the live composio_managed_auth_schemes field and dashboard button "
    "labels were not confirmed."
)


def _item(title: str, body: str, status: str, note: str | None = None) -> dict:
    return {"title": title, "body": body, "status": status, "note": note}


def _source(title: str, url: str, publisher: str) -> dict:
    return {"title": title, "url": url, "publisher": publisher}


GUIDES: list[dict] = [
    {
        "slug": "github",
        "name": "GitHub",
        "summary": (
            "Composio's managed-OAuth catalog lists GitHub, so registering your own OAuth app is optional. "
            "Own credentials are for consent-screen branding, custom scopes, a quota that is not shared, "
            "polling faster than the managed minimum, or enterprise branding. A Composio how-to recommends "
            "own credentials for production; current docs call branding the most common reason to switch, "
            "not a hard gate. No staff-review wait for creating an OAuth app was found."
        ),
        "auth_type": {
            "value": "OAuth 2.0",
            "status": "documented",
            "note": (
                "The GitHub toolkit page says Auth: OAUTH2. GitHub's OAuth app guide says both OAuth apps and "
                "GitHub Apps use OAuth 2.0. An OAuth app can only act on behalf of a user. GitHub Apps use "
                "fine-grained permissions and short-lived tokens. Creating your own app in this guide follows "
                "GitHub's OAuth app form. The toolkit FAQ says you can bring your own GitHub App, and that "
                "GitHub App permissions come from the app's GitHub settings and installation grant, not from "
                "auth config scopes. That page does not say whether the managed app is an OAuth App or a GitHub App."
            ),
        },
        "setup_path": {
            "value": "managed_or_own",
            "label": "Managed auth or your own app",
            "status": "documented",
            "note": (
                "The managed-OAuth catalog lists GitHub, and the current managed-versus-custom page says managed "
                "apps are the default when they are available. You do not need to register your own OAuth app for "
                "that managed app. Own credentials are for branding, custom scopes, dedicated quota, polling "
                "triggers shorter than the managed 15-minute minimum, a custom or self-hosted instance, or "
                "enterprise branding. The composio.dev GitHub how-to recommends own developer credentials for "
                "production. That is a recommendation, not a statement that managed auth stops working in production."
            ),
        },
        "difficulty": {
            "value": "Contained",
            "status": "uncertain",
            "note": (
                "Editorial label only. GitHub publishes no difficulty rating. The label reflects one registration "
                "form on the own-app path and no staff-review step in the creation guide. An organization can still "
                "require its own approval when OAuth app access restrictions are enabled. It is not a measured result."
            ),
        },
        "active_effort": {
            "value": (
                "Managed auth is the end user consenting to the Composio-named app, with no registration form. "
                "Your own OAuth app is one creation form, then copying the client ID and client secret into a custom "
                "auth config, then the user's authorization. GitHub and Composio do not say how long either path takes. "
                "Organization-owner approval, when that org has access restrictions enabled, has steps and no published duration."
            ),
            "status": "uncertain",
            "note": "Unverified editorial inventory of the documented click-path. No minute estimate is given.",
        },
        "approval_wait": {
            "value": (
                "No staff-review wait was found. The creation guide ends at Register application, and no fetched "
                "GitHub page gives a duration before the owner, or other users, can authorize a new OAuth app. "
                "When an organization has OAuth app access restrictions enabled, a member requests approval and an "
                "owner grants access. That organization step has no published duration, and it does not apply to every "
                "organization. The legacy Composio sentence that getting OAuth approvals takes time does not name "
                "GitHub and does not give a duration."
            ),
            "status": "documented",
            "note": "Documented absence of a staff-review figure. The conditional organization step was not timed.",
        },
        "confidence": {
            "value": "High",
            "status": "uncertain",
            "note": (
                "Editorial judgment. The registration and token steps follow two GitHub documents directly. "
                "High does not mean the flow was executed."
            ),
        },
        "managed": {
            "value": (
                "Composio's managed-OAuth catalog lists GitHub (slug GITHUB), and the GitHub toolkit page says "
                "Auth: OAUTH2 and Composio-managed OAuth available? Yes. You do not need to register an OAuth app "
                "or supply a client ID and client secret. Users see Composio on the consent screen, including the "
                "line that Composio wants to access your account, until you supply your own credentials. Managed "
                "apps are the default when they are available."
            ),
            "status": "documented",
            "note": (
                COMPOSIO_PAGE_NOTE
                + " Which GitHub product the managed app is, an OAuth App or a GitHub App, was not stated. "
                "No fetched page publishes the default scopes that managed auth requests. Sample strings such as "
                "repo,read:org are code samples, not that default."
            ),
        },
        "byo": {
            "value": (
                "Create a GitHub OAuth app only when you are registering your own app. Set the callback to the "
                "redirect URI on the Composio auth config, and enter the client ID and client secret in a custom "
                "auth config. Own credentials are for branding, custom scopes, dedicated quota, polling shorter than "
                "the managed 15-minute minimum, a custom or self-hosted instance, or enterprise branding. They are "
                "not required to make managed OAuth exist."
            ),
            "status": "documented",
            "note": (
                "The composio.dev GitHub how-to recommends own developer credentials for production. Current "
                "managed-versus-custom docs call branding the most common reason to switch, not a hard gate. "
                "GitHub's creation page does not know about Composio."
            ),
        },
        "redirect": {
            "value": REDIRECT_URI,
            "status": "documented",
            "note": (
                REDIRECT_NOTE
                + " With wildcard matching disabled, GitHub requires the redirect URL to exactly match the callback "
                "URL. The composio.dev GitHub how-to says a screenshot showed the v1 URL and that current Composio "
                "documentation points to the v3 URL. Register the redirect URI the auth config shows."
            ),
        },
        "decision": (
            "Use Composio managed auth for GitHub. It is listed, and an own OAuth app is not a prerequisite. "
            "Bring your own OAuth app when the consent screen should show your product, or when you need custom "
            "scopes, dedicated quota, faster polling, or enterprise branding. A how-to recommends own credentials "
            "for production. Current docs do not say managed auth stops working there."
        ),
        "execution_note": EXECUTION_NOTE,
        "tested": False,
        "last_checked": CHECKED,
        "prerequisites": [
            _item(
                "A GitHub account that can own the app",
                "You can register an OAuth app on your personal account or on an organization you have administrative access to. A user or organization can own up to 100 OAuth apps.",
                "documented",
            ),
            _item(
                "A public homepage URL",
                "GitHub asks for the full URL of the app's website and warns you to use only information you consider public. Avoid internal URLs and other sensitive data in the OAuth app record.",
                "documented",
            ),
            _item(
                "The callback URL you will actually use",
                "The form requires an authorization callback URL. You can enter up to 10. For a Composio custom auth config, one of them must be the Composio callback below.",
                "documented",
            ),
        ],
        "steps": [
            _item(
                "Decide that an OAuth app is the credential you are creating",
                "GitHub tells you to consider a GitHub App instead. OAuth apps act only as a user. GitHub Apps can act as the user or on their own, with finer repository access and short-lived tokens. Continue with an OAuth app when you are filling Composio's client ID and client secret fields.",
                "documented",
            ),
            _item(
                "Open the new OAuth app form",
                "From your profile picture, open Settings, then Developer settings, then OAuth apps. Choose New OAuth App. If you have never created one, GitHub labels that button Register a new application.",
                "documented",
            ),
            _item(
                "Enter the public application details",
                "Fill in the application name and homepage URL. The description is optional and is shown to users. Enter the authorization callback URL. Add more callback URLs only if you need them, up to 10.",
                "documented",
            ),
            _item(
                "Set device flow and token expiration on purpose",
                "Enable device flow only if the app will identify users that way. Expiring user access tokens is on by default. GitHub says to uncheck it only until the app's authentication code can handle short-lived tokens.",
                "documented",
                "The cited Composio pages do not say whether Composio's GitHub connection expects expiring user tokens to stay enabled.",
            ),
            _item(
                "Register the application",
                "Click Register application. The creation document stops at that click. It does not describe a review queue or an approval wait before the app exists.",
                "documented",
            ),
            _item(
                "Keep the client ID and client secret",
                "After Register application, copy the client ID and client secret into a Composio custom auth config only if you are using your own app. Keep the secret out of the repository. Managed auth does not need those values.",
                "documented",
            ),
            _item(
                "Send the user through GitHub's authorization screen",
                "Registering the app does not connect a user. GitHub's web flow sends the user to authorize the requested scopes, returns a temporary code to the callback, and exchanges that code with the client secret. The user has to approve the app. GitHub does not name one scope set as the minimum for a basic connection. The scopes table's first row, no scope, grants read-only access to public information. Users can grant fewer scopes than requested. Composio's managed default was not published.",
                "documented",
            ),
        ],
        "blockers": [
            _item(
                "An OAuth app cannot act without a user",
                "If the integration must act independently of a signed-in person, GitHub's own comparison says that is a GitHub App behavior, not an OAuth app behavior.",
                "documented",
            ),
            _item(
                "The 100-app ownership cap",
                "A user or organization can own up to 100 OAuth apps. Hitting that cap blocks another registration on the same owner.",
                "documented",
            ),
            _item(
                "Callback and Composio redirect must match",
                "With wildcard matching disabled, GitHub requires the redirect URL to exactly match the callback URL. Apps that had a single callback URL before 3 August 2026 have wildcard matching enabled for that URL. GitHub recommends disabling it if it is not needed. Composio names redirect_uri_mismatch when the provider URI and oauth_redirect_uri differ. Register the same URL in both places. Current docs name the v3 callback. The v1 callback remains supported when that is the config's default. GitHub allows up to 10 callback URLs. If redirect_uri is omitted, GitHub uses the first configured callback URL.",
                "documented",
            ),
            _item(
                "The authorization code expires after 10 minutes",
                "GitHub says the temporary authorization code expires after 10 minutes. The documented remedy is to send the user through the flow again. That expiry was not timed in this project.",
                "documented",
            ),
            _item(
                "Expiring user tokens are on by default",
                "The creation page says expiring user access tokens are enabled by default. The authorizing page says the access token expires after eight hours, and the refresh token expires after six months without use. Use the refresh token, or uncheck expiring tokens only until the app can handle short-lived tokens. A refresh failure returns bad_refresh_token, and the user goes through the flow again.",
                "documented",
            ),
            _item(
                "Organization restrictions are conditional",
                "Only when that organization has OAuth app access restrictions enabled, members request approval before they can authorize an OAuth app for the organization's resources. An owner grants access under Third-party Access. That is an organization policy, not a GitHub staff review, and it does not apply to every organization. No duration is published.",
                "documented",
            ),
            _item(
                "Managed auth shows Composio on the consent screen",
                "White-labeling the Connect Link logo does not change the GitHub consent screen. Composio says removing Composio from that screen for GitHub requires your own OAuth credentials.",
                "documented",
            ),
            _item(
                "The shared app shares quota",
                "Composio says its default OAuth app shares quota across users, and that your own app gets a dedicated quota. A launch that depends on that quota cannot stay on managed auth.",
                "documented",
            ),
        ],
        "human_actions": [
            _item(
                "Someone with admin rights submits the form",
                "Creating the app is a signed-in GitHub settings flow on a personal account or an organization the person administers. The creation guide does not offer an unattended API for that form.",
                "documented",
            ),
            _item(
                "Someone chooses the expiration checkbox",
                "A person has to leave expiring user access tokens on, or uncheck it because the app cannot handle short-lived tokens yet. That is a product decision in the form, not an inferred default from Composio.",
                "documented",
            ),
            _item(
                "The authorizing user approves the scopes",
                "GitHub's authorization screen is a human approval. Registering the OAuth app does not grant access to anyone's repositories by itself.",
                "documented",
            ),
            _item(
                "An organization owner may have to grant access",
                "Only when that organization has OAuth app access restrictions enabled. The member requests access and an owner grants it. The creation form itself has no review step, and no duration is published for the owner's decision.",
                "documented",
            ),
            _item(
                "Someone copies the client secret into Composio",
                "When you are using your own app, copy the client ID and client secret into a Composio custom auth config and pass that auth config id on the session. Keep the secret out of the repository. The authorizing user still has to approve the requested scopes.",
                "documented",
            ),
        ],
        "sources": [
            _source(
                "Creating an OAuth app",
                "https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-an-oauth-app",
                "GitHub Docs",
            ),
            _source(
                "Authorizing OAuth apps",
                "https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps",
                "GitHub Docs",
            ),
            _source(
                "Scopes for OAuth apps",
                "https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/scopes-for-oauth-apps",
                "GitHub Docs",
            ),
            _source(
                "Controlling scopes",
                "https://docs.composio.dev/docs/authentication/controlling-scopes",
                "Composio",
            ),
            _source(
                "Custom auth configs (legacy page)",
                "https://docs.composio.dev/docs/auth-configuration/custom-auth-configs",
                "Composio",
            ),
            _source(
                "White-labeling authentication",
                "https://docs.composio.dev/docs/authentication/white-labeling-authentication",
                "Composio",
            ),
            _source(
                "Managed OAuth apps",
                "https://docs.composio.dev/toolkits/managed-auth",
                "Composio",
            ),
            _source(
                "GitHub toolkit",
                "https://docs.composio.dev/toolkits/github",
                "Composio",
            ),
            _source(
                "Managed vs custom auth",
                "https://docs.composio.dev/docs/authentication/custom-app-vs-managed-app",
                "Composio",
            ),
            _source(
                "Programmatic auth configs",
                "https://docs.composio.dev/docs/authentication/programmatic-auth-configs",
                "Composio",
            ),
            _source(
                "How to create GitHub OAuth credentials",
                "https://composio.dev/auth/github",
                "Composio",
            ),
            _source(
                "Differences between GitHub Apps and OAuth apps",
                "https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/differences-between-github-apps-and-oauth-apps",
                "GitHub Docs",
            ),
            _source(
                "Approving OAuth apps for your organization",
                "https://docs.github.com/en/organizations/managing-oauth-access-to-your-organizations-data/approving-oauth-apps-for-your-organization",
                "GitHub Docs",
            ),
        ],
    },
    {
        "slug": "slack",
        "name": "Slack",
        "summary": (
            "Composio's managed-OAuth catalog lists Slack. Creating your own app is not required for a first connection "
            "when the workspace allows the install. Own app when you need your own Slack identity, custom scopes, a "
            "quota that is not shared, or the workspace blocks non-Marketplace apps. Creating an app and installing it "
            "on the owning workspace have no published wait. Marketplace review publishes its own upper bounds, and "
            "those bounds are only for that review."
        ),
        "auth_type": {
            "value": "OAuth 2.0",
            "status": "documented",
            "note": (
                "Slack installs apps with its v2 OAuth 2.0 code flow. Bot scopes are requested with the scope parameter "
                "and user scopes with user_scope. Sign in with Slack user scopes cannot be combined with other user scopes "
                "in the same flow."
            ),
        },
        "setup_path": {
            "value": "managed_or_own",
            "label": "Managed auth or your own app",
            "status": "documented",
            "note": (
                "The managed-OAuth catalog and the Slack toolkit page list Composio-managed OAuth for Slack. The Slack "
                "how-to calls managed auth recommended for getting started and says there is no need to create your own "
                "app or handle credentials. Own app when the consent screen must be yours, when you need custom scopes "
                "or dedicated quota, or when the workspace blocks non-Marketplace apps. Composio says Marketplace review "
                "of the managed Slack app is in progress. That is a listing statement, not a statement that managed OAuth "
                "is unavailable."
            ),
        },
        "difficulty": {
            "value": "Two install modes",
            "status": "uncertain",
            "note": (
                "Editorial label only. Slack publishes no difficulty rating. One workspace can use the dashboard install. "
                "Any other workspace adds OAuth and distribution. The label is not a timed result."
            ),
        },
        "active_effort": {
            "value": (
                "One workspace is a dashboard install. Any other workspace adds OAuth and public distribution. "
                "Only Marketplace review has a published bound, and that review is optional. Slack and Composio do "
                "not time app creation, the install on the owning workspace, or unlisted public distribution."
            ),
            "status": "uncertain",
            "note": (
                "Unverified editorial inventory. Marketplace figures are not a duration for creating the app or installing "
                "it on the owning workspace. Composio gives no date for its own managed-app Marketplace review."
            ),
        },
        "approval_wait": {
            "value": (
                "Marketplace review is optional. When you submit, Slack's bound is up to 10 business days to receive "
                "feedback, and the functional review takes up to 10 weeks for new submissions and 6 weeks for published "
                "apps resubmitting changes. Marketplace review is not required to create an app or to install it on the "
                "owning workspace. No official duration was found for creating a Slack app, installing it on the owning "
                "workspace, or activating unlisted public distribution. Slack says it cannot skip or accelerate review. "
                "Composio's statement that it is working on Marketplace review for the managed Slack app has no duration."
            ),
            "status": "documented",
            "note": (
                "The 10 business day, 10 week, and 6 week figures are Slack's Marketplace review bounds. They were not "
                "tested. They do not apply to app creation or to an install on the owning workspace."
            ),
        },
        "confidence": {
            "value": "High",
            "status": "uncertain",
            "note": (
                "Editorial judgment. Workspace install, OAuth, and distribution come from Slack's own app-management docs. "
                "The guide was not executed."
            ),
        },
        "managed": {
            "value": (
                "Composio's managed-OAuth catalog lists Slack (slug SLACK), and the Slack toolkit page says Auth: OAUTH2 "
                "and Composio-managed OAuth available? Yes. The Slack how-to says managed auth provides the Slack OAuth "
                "app, there is no need to create your own app or handle credentials, and managed auth is recommended for "
                "getting started. The consent screen then says Composio wants to access your account. White-labeling "
                "Composio's hosted page does not change that Slack screen. Composio says it is working on Marketplace "
                "review for the managed Slack app. That does not say managed OAuth is unavailable. Non-Marketplace "
                "installs can still work when the workspace allows them."
            ),
            "status": "documented",
            "note": (
                COMPOSIO_PAGE_NOTE
                + " The managed-auth how-to says to review scopes in the dashboard and does not print those default "
                "scopes. SLACKBOT is a separate catalog row. This guide is about SLACK. No date is given for the "
                "managed app's Marketplace review."
            ),
        },
        "byo": {
            "value": (
                "Create your own Slack app when the consent screen or Slack app identity must be yours, when you need "
                "custom scopes or dedicated quota, or when the workspace blocks non-Marketplace apps. Slack requires the "
                "owner of an app to create it. That is not a rule that Composio customers must create an app when they "
                "use Composio's app. Set an HTTPS redirect to the callback on the Composio auth config, and store the "
                "client ID and client secret in a custom OAuth2 auth config. Installing that app on any workspace other "
                "than the one selected at creation requires Activate Public Distribution. Marketplace submission is a "
                "further optional path."
            ),
            "status": "documented",
            "note": (
                "The custom Slack how-to also asks for a verification token for triggers. This guide does not treat "
                "that token as part of the OAuth install itself."
            ),
        },
        "redirect": {
            "value": REDIRECT_URI,
            "status": "documented",
            "note": (
                REDIRECT_NOTE
                + " Slack requires the redirect to use HTTPS, and it cannot contain an anchor. Both the v1 and v3 "
                "Composio URLs are HTTPS. The composio.dev Slack custom how-to still tells the reader to register the "
                "v1 URL. Current docs name the v3 URL and say some toolkit defaults still use v1. The auth config and "
                "the Slack app must use the same value. The short /api/v3/s/... URL is not the redirect URI sent to "
                "Slack. Slack's error sentence also says redirect_url values must match, while the parameter it tells "
                "developers to send is redirect_uri. Whether that is a second parameter or a wording slip is unresolved."
            ),
        },
        "decision": (
            "Use Composio managed auth for Slack when the workspace allows that install. Creating your own Slack app "
            "is not required to start. Bring your own app for your own Slack identity, custom scopes, dedicated quota, "
            "or a workspace that blocks non-Marketplace apps. Marketplace review times apply only if you submit a "
            "Marketplace listing. They are not the wait to create an app or to install it on the owning workspace."
        ),
        "execution_note": EXECUTION_NOTE,
        "tested": False,
        "last_checked": CHECKED,
        "prerequisites": [
            _item(
                "A Slack workspace for development",
                "Creating your own Slack app starts at api.slack.com/apps. You sign in, choose a blank app, enter an app name, and select the workspace where the app will be developed. By default a newly built app can only be installed in that associated workspace. Installing elsewhere requires an OAuth flow and then Activate Public Distribution. Managed auth does not require you to create that app.",
                "documented",
            ),
            _item(
                "An HTTPS redirect that matches the auth config",
                "Slack requires the redirect_uri to use HTTPS. A Redirect URL under OAuth and Permissions must also use HTTPS, and it cannot contain an anchor. For a Composio custom auth config, register the callback the auth config uses. Current docs name the v3 URL. The Slack custom how-to still shows the v1 URL. They must match each other. The short /api/v3/s/... link is not that redirect.",
                "documented",
            ),
            _item(
                "No single minimum scope list is published",
                "Slack says that while developing you determine the scopes the app requires. Bot scopes go in scope and user scopes in user_scope. The app-settings quickstart, for a basic app that sends messages with webhooks, adds bot scopes chat:write and channels:read. Those are the tutorial's choices, not a product minimum. Composio's custom how-to says chat:write alone might be enough when the agent only sends messages, and its longer list is labeled supported, not requested by default. Managed default scopes were not printed.",
                "documented",
            ),
        ],
        "steps": [
            _item(
                "Create the app in a development workspace",
                "From api.slack.com/apps, create a blank app, enter the app name, and select the development workspace. Slack says you can distribute the app to other workspaces later if you choose. No Marketplace submission is part of creating the app.",
                "documented",
            ),
            _item(
                "Install it on the owning workspace",
                "The quickstart install is OAuth and Permissions, then Install to Workspace, then Allow. Slack says that when you follow this flow you are playing the part of the installing user. An undistributed app cannot be installed on a different workspace. Other workspaces need the OAuth flow and Activate Public Distribution. Creating the app and this owning-workspace install have no published approval wait.",
                "documented",
            ),
            _item(
                "Configure the redirect under OAuth and Permissions",
                "Add a redirect URL that matches the service receiving the code. It must be HTTPS, it cannot contain an anchor, and it must match a configured redirect URL or a subdirectory of one. When several redirect URLs exist, send the same redirect_uri on the authorize request and on the token exchange.",
                "documented",
            ),
            _item(
                "Request bot scopes and user scopes separately",
                "Send users to https://slack.com/oauth/v2/authorize with the client ID. Put bot scopes in scope and user scopes in user_scope. Request Sign in with Slack scopes in their own flow. GovSlack uses https://slack-gov.com/oauth/v2/authorize instead.",
                "documented",
            ),
            _item(
                "Wait for a person to approve the scopes",
                "OAuth is requesting scopes, waiting for a user to approve, and exchanging the code. Some workspaces allow only admins to install, or only Marketplace apps. A workspace can require admin approval so a member requests the install instead of completing it. That human approval is not Marketplace review, and no duration is published for it.",
                "documented",
            ),
            _item(
                "Exchange the code before it expires",
                "Slack redirects back with a temporary code that expires after ten minutes. Exchange it at https://slack.com/api/oauth.v2.access with the code, client ID, and client secret. If several Redirect URLs are configured, send the same redirect_uri on authorize and on the token exchange, or Slack returns bad_redirect_uri. The bot token comes back as token_type bot. A user token, if requested, is under authed_user. Slack says OAuth tokens do not expire unless they are rotated or revoked.",
                "documented",
            ),
            _item(
                "Activate public distribution only for other workspaces",
                "Installing on a workspace other than the one selected at creation requires an OAuth flow and then Activate Public Distribution, under Manage Distribution, Share Your App with Other Workspaces, after the checklist. That activation is unlisted distribution. It is not a Marketplace listing. The fetched distribution page names the checklist and does not list its items, so this guide does not invent them. No duration is published for this activation.",
                "documented",
            ),
            _item(
                "Submit to the Marketplace only if you want a listing",
                "Marketplace submission is separate from creating an app, from installing it on the owning workspace, and from Activate Public Distribution. Slack recommends Marketplace listing for apps intended for commercial distribution. That is a recommendation, not a rule that an unlisted app cannot be installed elsewhere after public distribution is activated. Prerequisites named on the review guide include a working app, testing on a non-development workspace, and installation on 10 or more active workspaces. For that review only, preliminary feedback takes up to 10 business days, and functional review takes up to 10 weeks for new submissions and 6 weeks for published apps resubmitting changes.",
                "documented",
            ),
        ],
        "blockers": [
            _item(
                "An undistributed app cannot move workspaces",
                "Slack returns invalid_team_for_non_distributed_app when someone tries to install an undistributed app on a team other than the one where it was created.",
                "documented",
            ),
            _item(
                "Redirect mismatches fail the install",
                "Slack returns bad_redirect_uri when redirect values do not match across authorize and access, and its examples include HTTP, the wrong host, the wrong port, or a path that is not a subdirectory of a configured Redirect URL. Composio's Slack FAQ says to update OAuth and Permissions, Redirect URLs. The short /api/v3/s/... link is not the redirect. Put the auth config's callback, v3 or legacy v1, on the Slack app. The error sentence says redirect_url, while the parameter to send is redirect_uri. That naming clash was not resolved.",
                "documented",
                "The redirect_url versus redirect_uri wording is uncertain. The match rule and the examples use redirect_uri.",
            ),
            _item(
                "Workspace policy can block the install",
                "Some workspaces allow only administrators to install apps, or only Slack Marketplace apps. Others make members request an install that an administrator approves. Composio says its managed Slack app is still in Marketplace review and gives no date. The install can still work if the workspace allows non-Marketplace apps. If a warning blocks users, use the workspace's own Slack app or ask an admin to approve. Composio says that when installing non-Marketplace apps you need to be an owner to install directly.",
                "documented",
            ),
            _item(
                "The authorization code lasts ten minutes",
                "If the exchange does not finish in that window, the code is no longer usable. A person may have to approve the app again.",
                "documented",
            ),
            _item(
                "Granted scopes are sticky",
                "Scopes already granted are additive. Slack says there is no way to remove scopes from an existing token without revoking it entirely. Scope changes require a reinstall for existing installs. OAuth tokens do not expire unless they are rotated or revoked. Revocation happens if the app is uninstalled, the user removes their configuration, or the installing user's account is deactivated.",
                "documented",
            ),
            _item(
                "Published Marketplace apps can reject unapproved scopes",
                "Slack returns unapproved_scope when a published app is installed with scopes that are still in review or were not submitted. The installing-with-OAuth page does not apply that error to an unpublished app. Creating an app and installing it on the owning workspace are not that review.",
                "documented",
            ),
            _item(
                "Managed auth keeps Composio on the consent screen",
                "Until you use your own Slack app, the consent screen shows Composio. Own credentials are how you change that identity, request custom scopes, or leave the shared quota. They are not required for a first connection when the workspace allows the managed app.",
                "documented",
            ),
        ],
        "human_actions": [
            _item(
                "A person creates the app and picks the workspace",
                "App creation and the development-workspace choice happen in Slack's signed-in dashboard.",
                "documented",
            ),
            _item(
                "A member or an admin approves the install",
                "The OAuth flow waits for a person to approve scopes. If the workspace requires admin approval, that person is an administrator rather than any member.",
                "documented",
            ),
            _item(
                "Someone finishes the distribution checklist",
                "Activate Public Distribution stays unavailable until the checklist in Manage Distribution is complete. The items are shown in Slack's UI. They were not reproduced here because the guide page does not list them.",
                "documented",
            ),
            _item(
                "Marketplace listing is a separate submission",
                "A person submits the app for Marketplace review only if a listing is the goal. That review is not required to create the app or to install it on the owning workspace. Slack's upper bounds for that review are up to 10 business days for preliminary feedback and up to 10 weeks for a new functional review, or 6 weeks when a published app resubmits changes. Composio gives no date for its managed app's review.",
                "documented",
            ),
            _item(
                "Existing workspaces reinstall after scope changes",
                "A person in each installed workspace has to approve the new scopes. Updating the manifest does not rewrite tokens that were already issued.",
                "documented",
            ),
            _item(
                "Someone enters the client credentials in Composio",
                "For your own app, a person creates the OAuth2 auth config, turns on your own developer credentials, and pastes the client ID, client secret, and redirect URI. Slack also says to store application credentials and user tokens with care.",
                "documented",
            ),
        ],
        "sources": [
            _source(
                "Your Apps",
                "https://api.slack.com/apps",
                "Slack",
            ),
            _source(
                "Creating an app from app settings",
                "https://docs.slack.dev/app-management/quickstart-app-settings",
                "Slack",
            ),
            _source(
                "Installing with OAuth",
                "https://docs.slack.dev/authentication/installing-with-oauth",
                "Slack",
            ),
            _source(
                "App lifecycle and distribution",
                "https://docs.slack.dev/app-management/distribution",
                "Slack",
            ),
            _source(
                "Distributing your app in the Slack Marketplace",
                "https://docs.slack.dev/slack-marketplace/distributing-your-app-in-the-slack-marketplace",
                "Slack",
            ),
            _source(
                "Slack Marketplace review process",
                "https://docs.slack.dev/slack-marketplace/slack-marketplace-review-guide",
                "Slack",
            ),
            _source(
                "Managed OAuth apps",
                "https://docs.composio.dev/toolkits/managed-auth",
                "Composio",
            ),
            _source(
                "Slack toolkit",
                "https://docs.composio.dev/toolkits/slack",
                "Composio",
            ),
            _source(
                "Managed vs custom auth",
                "https://docs.composio.dev/docs/authentication/custom-app-vs-managed-app",
                "Composio",
            ),
            _source(
                "Programmatic auth configs",
                "https://docs.composio.dev/docs/authentication/programmatic-auth-configs",
                "Composio",
            ),
            _source(
                "White-labeling authentication",
                "https://docs.composio.dev/docs/authentication/white-labeling-authentication",
                "Composio",
            ),
            _source(
                "Slack OAuth 2.0 with Composio",
                "https://composio.dev/auth/slack",
                "Composio",
            ),
            _source(
                "Slack custom OAuth credentials",
                "https://composio.dev/auth/slack_custom",
                "Composio",
            ),
            _source(
                "Slack knowledge base",
                "https://docs.composio.dev/kb/guide/toolkits-slack",
                "Composio",
            ),
            _source(
                "Custom auth configs (legacy page)",
                "https://docs.composio.dev/docs/auth-configuration/custom-auth-configs",
                "Composio",
            ),
        ],
    },
    {
        "slug": "google-calendar",
        "name": "Google Calendar",
        "summary": (
            "Composio's managed-OAuth catalog lists Google Calendar, and the toolkit page says managed OAuth is available. "
            "An own OAuth client is optional, for branding, scopes beyond the managed app, or a quota that is not shared. "
            "Default scopes were not published. Current docs name the v3 callback, while the Google how-to still shows the "
            "v1 callback. Official pages disagree on sensitive-scope review timing, and the Calendar wait is otherwise unknown."
        ),
        "auth_type": {
            "value": "OAuth 2.0",
            "status": "documented",
            "note": (
                "The Google Calendar toolkit page says Auth: OAUTH2. Accessing a user's Calendar data with user consent "
                "uses an OAuth client ID, not an API key. That is Google's rule for a developer who is the OAuth client. "
                "It does not say a Composio customer must create a client when Composio already supplies one."
            ),
        },
        "setup_path": {
            "value": "managed_or_own",
            "label": "Managed auth or your own app",
            "status": "documented",
            "note": (
                "The managed-OAuth catalog lists Google Calendar (slug GOOGLECALENDAR), and the toolkit page says "
                "Composio-managed OAuth available? Yes. An own OAuth app is optional. Use it for branding, custom scopes, "
                "or dedicated quota. It is not a prerequisite. Remaining uncertainty: the live composio_managed_auth_schemes "
                "field was not called, the default scopes were not published, and the Google how-to still shows the v1 "
                "callback while current docs name the v3 callback."
            ),
        },
        "difficulty": {
            "value": "Path dependent",
            "status": "uncertain",
            "note": (
                "Editorial label only. Google publishes no difficulty rating. Managed auth, as Composio describes it, "
                "has no Google Cloud project. An own client adds a project, a consent screen, the Calendar API, and a "
                "web client. Verification applies only for some audiences and scope classes. This is not a measured result."
            ),
        },
        "active_effort": {
            "value": (
                "Managed auth needs no Google Cloud project. The user consents to Composio's app. An own client adds "
                "a Cloud project, consent-screen branding, the Calendar API on that project, a web client, and a "
                "redirect that matches Composio. The pages list those steps and do not time them."
            ),
            "status": "uncertain",
            "note": "Unverified editorial inventory of the documented steps. No minute estimate is given.",
        },
        "approval_wait": {
            "value": (
                "Verification is not always required. When sensitive-scope review applies, the sensitive-scope page "
                "says the process typically takes 3-5 business days, and the OAuth verification FAQ lists Sensitive "
                "Scope Verification as 10 business days. The estimates are not guaranteed. Which Calendar scope URIs "
                "need that review was not found on the public scope tables. Calendar scopes were absent from the "
                "restricted-scope list that was fetched, so restricted-scope review durations are not used as a "
                "Calendar wait. No official page gave a wait for enabling the Calendar API or for creating the OAuth "
                "client. The applicable Calendar wait is otherwise unknown. None of these figures was tested, and "
                "none of them is a duration that Calendar verification always takes."
            ),
            "status": "uncertain",
            "note": (
                "Documented contradictory evidence: 3-5 business days on the sensitive-scope page versus 10 business "
                "days in the verification FAQ. The applicable Calendar wait was not settled."
            ),
        },
        "confidence": {
            "value": "Medium",
            "status": "uncertain",
            "note": (
                "Editorial judgment. The catalog listing and the conflicting review figures were read and were not run. "
                "Medium reflects open questions: default managed scopes, which callback a new Calendar auth config shows, "
                "whether a new web client shows a client secret, and which sensitive-review figure would apply."
            ),
        },
        "managed": {
            "value": (
                "Composio's managed-OAuth catalog lists Google Calendar under slug GOOGLECALENDAR, and the Google "
                "Calendar toolkit page says Auth: OAUTH2 and Composio-managed OAuth available? Yes. You do not need to "
                "register an OAuth app or supply a client ID and client secret for that managed app. The Calendar "
                "toolkit FAQ says the consent screen shows Composio until you create your own OAuth app. Managed auth "
                "is the default when it is available."
            ),
            "status": "documented",
            "note": (
                COMPOSIO_PAGE_NOTE
                + " The catalog and the live composio_managed_auth_schemes field were not cross-checked, because that "
                "API was not called. No fetched page publishes the default Calendar scopes the managed app requests. "
                "The googleapps how-to is a Gmail example that says the same client can be reused after enabling the "
                "Calendar API. It is not a Calendar-only page."
            ),
        },
        "byo": {
            "value": (
                "An own Google OAuth client is optional. Use it when the consent screen must show your name, when you "
                "need scopes beyond the managed app, or when quota must be dedicated. Composio tells customers who add "
                "scopes beyond the managed app to complete Google's required verification before requesting those "
                "additional scopes. That describes a customer-owned client. It does not say the managed Composio app "
                "is unverified, and it does not require you to bring your own app for Calendar."
            ),
            "status": "documented",
            "note": (
                "Whether a new Web client still shows a client secret is unresolved. The create-credentials page says "
                "client secrets are not used for Web applications. The web-server guide still says to download "
                "client_secret.json. Composio's Google how-to and custom auth config both require a client secret. "
                "This was not executed."
            ),
        },
        "redirect": {
            "value": REDIRECT_URI,
            "status": "documented",
            "note": (
                REDIRECT_NOTE
                + " On a Google web client this value is an authorized redirect URI. The googleapps how-to is not "
                "marked legacy and still tells the reader to register https://backend.composio.dev/api/v1/auth-apps/add. "
                "Current docs name the v3 URL and say some toolkit defaults still use v1. The provider and the auth "
                "config must match each other. The how-to also suggests https://platform.composio.dev as an authorized "
                "JavaScript origin for the dashboard. That origin is not the OAuth redirect."
            ),
        },
        "decision": (
            "Use Composio managed auth for Google Calendar. The catalog lists it, and an own OAuth client is not a "
            "prerequisite. Bring your own client when the consent screen should show your name, when you need scopes "
            "beyond the managed app, or when you need dedicated quota. Register the callback the auth config actually "
            "uses. Current docs name the v3 URL, and the Google how-to still shows the v1 URL."
        ),
        "execution_note": EXECUTION_NOTE,
        "tested": False,
        "last_checked": CHECKED,
        "prerequisites": [
            _item(
                "Managed auth does not start with a Cloud project",
                "Composio's managed-OAuth catalog lists Google Calendar, and current docs say you do not register an OAuth app or supply a client ID and client secret for a managed app. Managed auth, as Composio describes it, needs no Google Cloud project. The live composio_managed_auth_schemes field was not called.",
                "documented",
                "The catalog was read. The toolkit API was not called, so the catalog and the API were not cross-checked.",
            ),
            _item(
                "An own client needs a Google Cloud project",
                "Bring your own client only for branding, scopes beyond the managed app, or dedicated quota. That path starts by creating or choosing a Google Cloud project, then configuring the OAuth consent screen. There is no separate Calendar developer signup.",
                "documented",
            ),
            _item(
                "One redirect URI, shared by Google and Composio",
                "If you create a web client, its authorized redirect URI has to be the same value as the Composio auth config. Current docs name the v3 callback. The Google how-to still shows the v1 callback. Following only one of those pages registers a different URI.",
                "documented",
            ),
            _item(
                "Default scopes and sensitivity labels were not published",
                "No fetched Composio page publishes the default scope string managed auth requests for Google Calendar. Google does not name one minimum Calendar scope. The public Calendar tables do not mark each URI sensitive or restricted, and Calendar scopes were absent from the restricted-scope list that was fetched.",
                "uncertain",
            ),
        ],
        "steps": [
            _item(
                "Start with managed auth unless you need your own client",
                "Composio lists Google Calendar as a managed OAuth toolkit. Using that app means no Google Cloud project and a user consent to Composio's app. Create your own client only when the consent screen must show your name, when you need scopes beyond the managed app, or when quota must be dedicated. That consent was not executed.",
                "documented",
            ),
            _item(
                "Configure branding and audience on your own client",
                "There is no separate Calendar developer signup. The consent-screen path is Menu, Google Auth platform, Branding: app name, user support email, audience, developer contact email, and agreement to the Google API Services User Data Policy. Internal use does not require verification, though an organization administrator might still approve it. External apps used outside the Workspace organization add scopes under Data Access. Apps used only inside the organization do not list scopes on the consent screen, and sensitive or restricted scopes then do not require further Google review.",
                "documented",
            ),
            _item(
                "Request the narrowest Calendar scope you can justify",
                "Google says to choose the most narrowly focused scope and avoid scopes the app does not require. It does not name one minimum Calendar scope. The events.list method allows authorization with at least one of several scopes, including calendar.readonly, calendar, calendar.events.readonly, and calendar.events. That set is for listing events. It is not an instruction to request all of them. Composio's Calendar guide says event-list and event-fetch tools that need event access should have https://www.googleapis.com/auth/calendar.events. That is a Composio tool requirement, not Google's minimum, and it is not a published managed default.",
                "documented",
                "Per-URI sensitive versus non-sensitive labels were not on the public tables. The sensitive-scope page's example, reading events stored in Google Calendar, does not name a URI.",
            ),
            _item(
                "Add test users while an external app stays in Testing",
                "If the user type is External, add test users under Audience while Publishing status stays Testing. Verification is not required for development, testing, or staging. Only listed test users can authorize, aside from an identity-scope exception that does not include Calendar API scopes. Testing is limited to up to 100 test users, and authorizations expire seven days from consent when any other OAuth scope is requested.",
                "documented",
            ),
            _item(
                "Enable the Calendar API and create a web client",
                "For custom credentials, Composio's Calendar FAQ says the Google Calendar API must be enabled on the Google Cloud project that owns those credentials, then to wait a few minutes and retry. That wait is Composio's sentence, not a Google SLA found on the Calendar auth page. Create a Web application client and add the authorized redirect URI that matches the Composio auth config: v3 in current docs, v1 in the Google how-to.",
                "documented",
                "The client form has an optional irreversible setting, Use this client for an AI-powered agent. Google does not say a Composio integration must check it. Whether Composio's token exchange expects the flag was not found. If the app does both agent and ordinary user features, Google says to create separate clients.",
            ),
            _item(
                "Resolve the client id and client secret before pasting them",
                "Composio's custom auth config requires a client ID and a client secret. The create-credentials page says client secrets are not used for Web applications. The web-server guide still says the client secret is shown only after you create the client, and to download client_secret.json. These pages were fetched on the same day and do not agree. Paste values into Composio only after comparing them with the screen you actually get.",
                "uncertain",
            ),
            _item(
                "Submit verification only when audience and scope class require it",
                "Verification is not implied by using OAuth. It is not required for an internal organization-owned app, for External plus Testing, for personal use, or for only non-sensitive scopes. App verification is required for a public app that requests sensitive or restricted scopes. Brand verification is still required to display an app name and logo. Which Calendar URI is sensitive was not on the public tables, so this guide does not say Calendar verification always applies or how long it takes.",
                "documented",
            ),
            _item(
                "Have the user consent",
                "When the app is installed, Google asks the user to validate the scopes. In Testing, Google displays a warning before a listed test user can authorize. A Workspace admin can block the app. Creating a client, or choosing managed auth, does not by itself connect a calendar. This consent was not executed.",
                "documented",
            ),
        ],
        "blockers": [
            _item(
                "Managed default Calendar scopes were not published",
                "No fetched page states the scope string Composio managed auth sends for GOOGLECALENDAR. Controlling-scopes says Composio requests a sensible set of default scopes. That is not a Calendar scope list. The API field for available scopes was not called, and the docs do not say that ceiling is the default request.",
                "uncertain",
            ),
            _item(
                "The Google how-to and current docs name different callbacks",
                "Current programmatic docs say to register https://backend.composio.dev/api/v3/toolkits/auth/callback unless the auth config still defaults to https://backend.composio.dev/api/v1/auth-apps/add. The googleapps how-to still says to put the v1 URL on the Google client and in the Composio auth config. A mismatch is documented as redirect_uri_mismatch. The two sides must use the same URL. Which URL a new Calendar auth config shows was not opened in the dashboard.",
                "documented",
            ),
            _item(
                "Extra unverified scopes can block the app",
                "Composio's Calendar FAQ says the app is blocked when the client requests scopes Google has not verified, usually extra scopes beyond the defaults. The stated remedy is to remove the extra scopes, or submit those scopes on your own OAuth app. That does not say the managed app is unverified.",
                "documented",
            ),
            _item(
                "External Testing is a closed 100-user, seven-day list",
                "An External app in Testing is limited to up to 100 test users. A test user consumes that quota once added. Authorizations expire seven days from consent, and a refresh token from an offline request expires too, unless the only scopes are the identity scopes userinfo.email, userinfo.profile, openid, or their OpenID Connect equivalents. Calendar API scopes are not in that identity list. During development, the Calendar troubleshooter says you can continue past an unverified warning with Advanced, then Go to the project name (unsafe).",
                "documented",
            ),
            _item(
                "Web client secret versus Composio's form",
                "The create-credentials page says client secrets are not used for Web applications. The web-server OAuth guide still says to download client_secret.json, and that the secret is shown only after the client is created. Composio requires client_id and client_secret. This project did not create a web client, so it does not know which value the console shows today.",
                "uncertain",
            ),
            _item(
                "No single verification duration applies to Calendar",
                "Sensitive-scope review is typically 3-5 business days on the developer page and 10 business days in the OAuth verification FAQ. Those pages disagree, the estimates are not guaranteed, and which Calendar URI needs that review was not found. Calendar scopes were absent from the restricted-scope list, so restricted-scope review durations are not used here as a Calendar wait. The wait is otherwise unknown. Do not read any of these figures as the time Calendar verification always takes.",
                "uncertain",
            ),
            _item(
                "Refresh-token limits disagree",
                "Google documents a limit of 100 refresh tokens per Google Account per OAuth 2.0 client ID, and the oldest is invalidated. Composio's Calendar FAQ says a 401 can follow Google's refresh token limit of about 50 per account. Both pages were fetched. Neither was tested, so this guide does not pick a number.",
                "uncertain",
            ),
            _item(
                "A Workspace admin can block the app",
                "Admins can block any OAuth app. Trusted status can override the 100-user cap and the seven-day testing refresh-token limit for that organization's users. An admin marks the app Trusted, Limited, or Blocked. The OAuth registration form does not do that by itself.",
                "documented",
            ),
        ],
        "human_actions": [
            _item(
                "The end user consents",
                "Managed auth, as Composio describes it, still needs a person to consent to Composio's app. An own client ends on the same kind of provider consent screen. Neither consent was executed.",
                "documented",
            ),
            _item(
                "Someone creates the Cloud project only for an own client",
                "Creating or choosing a project, finishing branding, enabling the Calendar API, and creating the web client are signed-in console steps. They apply when you bring your own client. They are not the managed-auth path.",
                "documented",
            ),
            _item(
                "Someone chooses Internal or External",
                "Audience is a human choice. Internal covers the organization and does not require verification. External is the setting that leads toward test users and, for some scope classes, verification. This guide does not tell you which audience to pick.",
                "documented",
            ),
            _item(
                "Someone sets the AI-agent checkbox before Create",
                "If you create a client, the optional Use this client for an AI-powered agent setting cannot be edited later. A wrong choice means creating another client. Whether Composio expects that flag was not found.",
                "uncertain",
            ),
            _item(
                "Someone maintains the test-user list",
                "While an External app stays in Testing, a person adds every Google account that should be able to grant access, up to the documented cap of 100 test users.",
                "documented",
            ),
            _item(
                "Verification, when it applies, is a human submission",
                "A person submits brand verification and the matching scope verification only when the audience and the scope class require it. Which Calendar URI is sensitive or restricted was not on the public tables. The sensitive-review pages disagree on duration, and the wait is otherwise unknown. This project did not submit a consent screen.",
                "uncertain",
            ),
        ],
        "sources": [
            _source(
                "Managed OAuth apps",
                "https://docs.composio.dev/toolkits/managed-auth",
                "Composio",
            ),
            _source(
                "Google Calendar toolkit",
                "https://docs.composio.dev/toolkits/googlecalendar",
                "Composio",
            ),
            _source(
                "Managed vs custom auth",
                "https://docs.composio.dev/docs/authentication/custom-app-vs-managed-app",
                "Composio",
            ),
            _source(
                "Programmatic auth configs",
                "https://docs.composio.dev/docs/authentication/programmatic-auth-configs",
                "Composio",
            ),
            _source(
                "Google Apps OAuth2 credentials",
                "https://composio.dev/auth/googleapps",
                "Composio",
            ),
            _source(
                "Google OAuth setup and consent",
                "https://docs.composio.dev/kb/guide/platform-google-oauth",
                "Composio",
            ),
            _source(
                "Google Calendar knowledge base",
                "https://docs.composio.dev/kb/guide/toolkits-google-calendar",
                "Composio",
            ),
            _source(
                "Create access credentials",
                "https://developers.google.com/workspace/guides/create-credentials",
                "Google",
            ),
            _source(
                "Configure the OAuth consent screen",
                "https://developers.google.com/workspace/guides/configure-oauth-consent",
                "Google",
            ),
            _source(
                "Choose Google Calendar API scopes",
                "https://developers.google.com/workspace/calendar/api/auth",
                "Google",
            ),
            _source(
                "Events: list",
                "https://developers.google.com/workspace/calendar/api/v3/reference/events/list",
                "Google",
            ),
            _source(
                "Sensitive scope verification",
                "https://developers.google.com/identity/protocols/oauth2/production-readiness/sensitive-scope-verification",
                "Google",
            ),
            _source(
                "Restricted Scopes",
                "https://support.google.com/cloud/answer/13464325",
                "Google",
            ),
            _source(
                "OAuth verification FAQ",
                "https://support.google.com/cloud/answer/13463817",
                "Google",
            ),
            _source(
                "OAuth App Verification Help Center",
                "https://support.google.com/cloud/answer/13463073",
                "Google",
            ),
            _source(
                "Setting up your OAuth consent screen",
                "https://support.google.com/cloud/answer/10311615",
                "Google",
            ),
            _source(
                "Using OAuth 2.0 for Web Server Applications",
                "https://developers.google.com/identity/protocols/oauth2/web-server",
                "Google",
            ),
            _source(
                "Using OAuth 2.0 to Access Google APIs",
                "https://developers.google.com/identity/protocols/oauth2",
                "Google",
            ),
            _source(
                "OAuth app state overview",
                "https://developers.google.com/identity/protocols/oauth2/production-readiness/overview",
                "Google",
            ),
            _source(
                "Troubleshoot Calendar authentication",
                "https://developers.google.com/workspace/calendar/api/troubleshoot-authentication-authorization",
                "Google",
            ),
            _source(
                "Custom auth configs (legacy page)",
                "https://docs.composio.dev/docs/auth-configuration/custom-auth-configs",
                "Composio",
            ),
        ],
    },
]
