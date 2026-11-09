---
name: agent-reach
description: >
  Read-only access to content across platforms: search, read posts, view comments, fetch subtitles, check market quotes and job listings.
  Use when the user mentions or pastes links: Xiaohongshu/RedNote, Bilibili, Twitter/X, Reddit,
  YouTube (subtitles, transcripts), GitHub, V2EX, Xueqiu/stock quotes, LinkedIn/Boss Zhipin job listings,
  Instagram, Facebook, Xiaoyuzhou podcasts; or says "help me search / take a look / read this link" while the built-in web search/read tool is unavailable, failing, or can't get the body text;
  or wants to install, add/remove a platform, log in/out, check status, update, or uninstall Agent Reach.
  Does not: post, comment, like, message, or perform any write operation; does not log in on behalf of the user or ask for passwords.
  Prefer the Agent's built-in tools for public content; Reach fills the gaps.
metadata:
  homepage: https://github.com/ledokter/Agent-Reach-English
  version: "{{VERSION}}"
---

# Agent Reach

One command to read every platform: `agent-reach`. Read-only, outputs one line of JSON by default.

Before acting, say "using the agent-reach skill (X channel)". Once this skill is invoked, the following rules apply throughout.

## Routing

- Try your built-in search/read tools first for public content (you can add `site:domain`). Verify separately whether you've got the body text, comments, and subtitles; if you have enough, answer directly — don't install channels or log in.
- Only use Reach when the built-in tools are unavailable, missing the part the user wants, or the user wants an in-site action declared by the channel. If unsure which actions and parameters exist, run `agent-reach channels` first.
- When a channel is already added (default channel or added via `add`), search/read goes directly through that site's tool; for channels not yet added, search/read first tries the public web without login, and results show `backend: public-web` to indicate the source. `--backend public-web` only queries the public web; `--backend <backend>` specifies an in-site tool.
- The platform name or link is only used to identify the source; it does not automatically trigger installation or login.
- Summaries, page shells, comment counts, and subtitle track listings are not the same as the body text, comments, or subtitles themselves — state each separately. When the user skips login, the public results already obtained are still delivered.

```bash
agent-reach channels                      # actions and parameters for each channel
agent-reach <channel> <action> [params]   # e.g.: agent-reach xiaohongshu search "coffee" --limit 5
agent-reach read <link>                   # auto-select channel by link
```

## Results and Errors

- `ok: true` → content is in `items`, each entry has `title / url / author / published_at / text`, and raw data is in `raw`.
- `ok: false` → check `error.code` and follow `error.hint`:

| error.code | What to do |
|---|---|
| `NEED_SETUP` | Missing dependency or key. Follow the prompt to run `agent-reach add <channel>`; if a key is required, have the user provide it themselves, then run `agent-reach configure <key>` |
| `NEED_LOGIN` | Keep the results already obtained and tell the user login is required; `agent-reach login <channel>` opens a browser for the user to log in themselves — you never log in for them and never ask for passwords |
| `UPSTREAM_BROKEN` | This platform has a temporary problem; `message` is the original error text. Tell the user in plain language which platform is temporarily unavailable and roughly why, without naming the tool; only run `agent-reach update` once after user consent if the error text indicates the tool is outdated; do not retry in a loop |
| `TIMEOUT` | Check the failure stage and channel status (`agent-reach doctor --text`); do not retry repeatedly or reopen windows |
| `RATE_LIMITED` | The platform is rate-limiting; Reach has already paused this channel. Wait per `retry_after_seconds`; do not switch backends |
| `PLATFORM_BLOCKED` | The platform requires verification (captcha / risk control). Stop and ask the user to handle it on the official page; do not switch accounts or backends |
| `BUSY` | The browser was still full after 2 minutes in the queue, or the user has a login window open. Try again after a while, or wait for the user to say login is done; do not close windows or switch configs |
| `NOT_FOUND` | Content does not exist; check the link or ID |
| `BAD_INPUT` | Wrong parameters; run `agent-reach channels` to see usage |

On `PLATFORM_BLOCKED`, `RATE_LIMITED`, `NEED_LOGIN`, or `BUSY`, stop the current attempt — do not switch accounts, backends, or browsers to keep retrying. A network failure or a failure on one machine must not be reported as "the platform requires login".

## Login and the Dedicated Browser

All browser channels share one dedicated browser (CloakBrowser preferred, falling back to the local Chrome if it can't be installed). It runs headless by default with no popup window, auto-closes after 10 minutes idle, and reopens automatically on the next call. Parallel calls are allowed (including sub-agents querying at the same time): at most 2 concurrent calls per platform, 4 total across all platforms — extras queue automatically; two searches on the same platform must be at least 10 seconds apart.

The first time a website is used, if the user's Chrome has the OpenCLI extension connected, the program copies that site's login once into the dedicated browser, then reuses it thereafter; only that site is copied, the original browser is untouched. Only when the login has expired or there is no source to copy from does the program ask the user to run `agent-reach login <channel>` themselves. For details on refresh, source selection, and logout, see [Sessions and the dedicated browser](references/sessions.md): read it when the user wants to log in, log out, switch accounts, or hits `NEED_LOGIN`.

## Platform Notes

- Xiaohongshu read returns only text descriptions; do not claim to have understood images or videos.
- When Boss Zhipin search results have `salary_encoded=true`, never guess salary figures; read the job link to get the readable salary from the details.
- For what each platform can do publicly and what Reach adds, see [Capability boundaries](references/capabilities.md): read it when the user asks "what can you query / is it complete" or to judge result completeness.

## Channels

{{CHANNEL_TABLE}}

`default` channels are installed by default and can also be removed; once removed, updates will not add them back. The `login` column is the auth entry point, not a prerequisite for querying public content.

## When Installation Completes

After `agent-reach setup`, show `result.installation_report.markdown` to the user verbatim — no additions, deletions, reordering, or self-added greetings or tables; the report is generated by the program.

## When the User Wants to Manage Agent Reach

| User says | You run |
|---|---|
| Add a platform | `agent-reach add <channel>`; dependencies install automatically; only tell the user what they must do themselves (log in or provide a key) |
| Remove a platform | `agent-reach remove <channel>` |
| Log in / login expired | `agent-reach login <channel>`; the user logs in themselves in the opened window |
| Log out | `agent-reach logout <channel>` |
| Check status / what's available | `agent-reach doctor --text`; for a live test run `agent-reach check <channel> --text` |
| Upgrade / update | `agent-reach update` |
| Uninstall | First run `agent-reach uninstall --dry-run` to show the user, then after confirmation run `agent-reach uninstall` |
| Let another AI use it too | `agent-reach skill link <that AI's skill directory>`; run `agent-reach skill` to see where it's currently placed |
| An AI should not have a user-level skill (e.g. registered per-project only) | `agent-reach skill unlink <that AI's skill directory>`; afterwards setup and update will not place it back |

For troubleshooting, browser maintenance, and uninstall details, see [Maintenance guide](references/maintenance.md): read it when an update fails, the browser won't start, or you need to uninstall.

## When a New Version Is Available

A `meta.update` in the results means a new version is available. Mention it only once per conversation, in the user's language and plain words:

1. Tell the user a new version is available (`meta.update.latest`).
2. Pick 1 to 3 highlights from `meta.update.notes` and explain what changed.
3. Ask whether to update; only run `agent-reach update` after the user agrees.

## Red Lines

- Read-only. Posting, commenting, liking, and messaging are never done.
- Never log in on behalf of the user; never ask for or output passwords, cookies, or other credentials.
- Ordinary queries do not change dependencies and do not auto-update.
