# Changelog

All notable changes to this project are recorded in this file.

---

## [1.6.2] - 2026-11-09

- YouTube subtitles now come in the video's own language by default (French for a French video), instead of a machine translation into Chinese. Only one subtitle track is downloaded, which avoids most "Too Many Requests" errors.
- Bilibili: new read-only actions to follow uploaders (UP主): `users` (search uploaders), `user` (profile and followers), `user_videos` (latest videos with views) and `rank` (3- or 7-day leaderboard).
- Bilibili no longer shows as "broken" in `doctor`: its test video had been removed from the site.
- Install and `agent-reach update` now use this English fork instead of the Chinese upstream.

Technical details:
- `youtube subtitle --lang` defaults to `auto`: human subtitles in the video language, then its original auto-captions (`<lang>-orig`), then English; auto-caption machine translations are only used when asked for explicitly. The track list comes from one `--dump-json`, then exactly one track is fetched with `--load-info-json`. When nothing matches, the error hint lists the available tracks.
- Bilibili live-test samples: `BV1xx411c7mD` (av2) and UID 2. bili-cli write commands (like, coin, triple, dynamic-post, unfollow) remain unexposed.
- `update_notice.REPO` is `ledokter/Agent-Reach-English`; `docs/install.md` installs with `uv tool install git+https://github.com/ledokter/Agent-Reach-English`.

---

## [1.6.1] - 2026-11-01

- Several 1.6.0 cases where web search, Reddit, Xiaohongshu or Bilibili failed although the content was reachable, or reported success with empty content, are fixed.
- When another program on your computer uses the browser port, Agent Reach can use a different one; you don't have to close that program.
- A login copy that fails now says so instead of reporting success.
- On Windows, Xiaohongshu links with special characters open correctly.

Technical details:
- Web search: every request identifies itself as `agent-reach/<version>`, so Exa's Cloudflare front no longer blocks it (#877).
- Reddit: when the site tool fails transiently (for example it returns HTML instead of data), search and read fall back to the public web (#880).
- Xiaohongshu: OpenCLI 2.0 results are mapped, so read no longer succeeds with empty fields; search and comments no longer return one empty row when there are no results (#861, #895).
- Bilibili: a QR login that saved no usable credential is no longer reported as success, and the hint now says `agent-reach login bilibili` (#866, #883).
- The dedicated browser's port is configurable with `agent-reach configure browser-port <port>`, for when another tool holds 9222 (#848).
- Login reuse: no "copied 0 cookies" record when the browser bridge is down; an explicit `login <channel> --import-existing` that copies nothing now fails clearly (#879).
- Windows: Xiaohongshu note links containing `&` can be read and their comments loaded (#860).

## [1.6.0] - 2026-10-23

- Upgrading from an older version: just send your AI the "update Agent Reach" sentence. Your keys and settings are kept, and the old program is removed for you.
- Adding a platform takes one sentence. Everything it needs is installed for you, with no admin password; you only log in or enter a key.
- Platforms that need a login, such as Xiaohongshu and X, now use Agent Reach's own browser in the background, never yours, and several AIs can search at once.
- RSS and Exa search are now part of "web". When a new version is out, your AI tells you in plain words what changed and updates only if you say yes.

1.6 is a rebuild. Agents call one command, `agent-reach`; everything Agent Reach installs or stores lives under `~/.agent-reach/`.
1.6 is a rebuild: Agents call a single command, `agent-reach`; everything Agent Reach installs or stores lives under `~/.agent-reach/`.

Technical details:
- 28 of 40 actions passed real acceptance before release; these shipped untested with maintainer approval: Reddit (test network blocked), Instagram (rate limited), Bilibili subtitles, LinkedIn, Xueqiu hot posts/stocks (no login), Xiaoyuzhou (no key).
- Browser channels share one profile, close after ten idle minutes and reopen on demand.
- Adding a channel prepares its tools; removal clears only that site's login. Default platforms can be removed and updates won't add them back.
- Updating keeps tools that have a tested version at that version; other tools get the newest version inside their supported range.
- Public content remains public-first, with a compact capability receipt.
- Keep Xiaoyuzhou transcription; remove the extra planner and duplicate site extraction.
- Reuse existing local site sessions read-only; queries default to headless, with a visible window for human login.
- The dedicated browser is identified by the id its extension saves inside its own profile, so the user's own Chrome is never mistaken for it; a query no longer closes an open login window.
- Browser channels run queries in parallel: up to 2 per platform and 4 in total, with the rest queued instead of failing BUSY at once; login windows, logout and browser setup wait for running queries.
- Report NEED_LOGIN instead of UPSTREAM_BROKEN when not logged in: Xueqiu community (error 400016), Bilibili subtitles (no Bilibili login), LinkedIn (no LinkedIn login in the dedicated browser).
- Smoother upgrade from 1.5: install and update share one guide, install.md, which checks the version first (update.md, where 1.5 sends users, points to it); `agent-reach update` moves a pip/pipx install to uv by itself; `setup` removes the old Agent Reach program (only Agent Reach itself) and the install report explains what was kept, what changed and which old channels can be added back. Install URLs always point at the latest release.
- Upstream errors reach the agent unchanged (the original message and help); the agent tells the user which platform is temporarily unavailable, by platform name. Reach no longer replaces them with its own advice (NEED_LOGIN still gives Reach's dedicated-browser login steps).

### ✨ New

- **Unified entry / Unified entry**: `agent-reach <channel> <action>`, `agent-reach read <url>`, `agent-reach channels`. One JSON envelope per call, unified error codes with hints, per-call timeout, automatic fallback to the next backend.
- **Management / Management commands**: `setup`, `add` / `remove <channel>`, `login` / `logout <channel>`, `doctor`, `check`, `skill`, `skill link <dir>`, `update`, `configure`, `uninstall`.
- **One-step setup / One-step setup**: `setup` adds every default channel through the same path as `add` (bili-cli goes into `~/.agent-reach/tools/`) and reports what works, which AIs can read the skill, optional channels and optional logins. / `setup` uses the same logic as `add` to enable all default channels, and reports which work, which AIs can read the skill, optional channels and optional logins.
- **Skill placement / Skill placement**: one real copy at `~/.agents/skills/agent-reach/SKILL.md` (read directly by Codex, OpenCode, Cline, Warp, Zed); a link to it in the skill folder of Claude Code, OpenClaw, Hermes, Cursor, Gemini CLI, GitHub Copilot and Windsurf when installed (a copy where links are not allowed, e.g. Windows). `agent-reach skill link <dir>` covers any other AI. / Only one real file is placed; other AIs' skill folders get a link pointing to it (a link: a shortcut pointing to the original file).
- **Private upstream installs, tested versions / Private upstream installs, tested versions**: tools go into `~/.agent-reach/tools/`; the user's own copies are untouched. Tools with a declared tested version install at that version, and `update` keeps them there; other tools install the newest version inside `floor` and `exclude`, which also define acceptable existing tools. `state.json` records the version actually installed and `doctor` shows it. Single-instance tools (OpenCLI) reuse the user's copy; if it is outside the supported versions, it is upgraded only with `--allow-upgrade`. / Tools with a tested version install that tested version, and `update` keeps them there; other tools use the newest version inside the supported range; doctor shows the actual version.
- **`add` gives a finished result / `add` finishes in one step**: missing prerequisites are installed without an admin password: uv (official script), ffmpeg (`imageio-ffmpeg` in a private venv), Node.js (official release under `~/.agent-reach/tools/node/` when the system has none), CloakBrowser (falling back to installed Chrome on download failure). git is no longer needed (Boss installs from a GitHub archive). The user only logs in or enters a key. / Missing dependencies are installed automatically; the user only logs in or enters a key.
- **Login state under `~/.agent-reach/` / Unified login management**: CLI tool logins in `sessions/`, browser logins in a dedicated Agent Reach browser. The browser opens by itself when a channel needs it and closes after 10 minutes without use. The OpenCLI extension is loaded automatically on each CloakBrowser launch; Windows system-Chrome fallback may need one Web Store click. Only the requested site’s cookies are copied read-only from an existing connected local browser; the source remains unchanged. / The dedicated browser opens automatically on demand and closes after 10 minutes of inactivity; the extension is installed automatically on macOS/Linux.
- **remove cleans up / remove cleans up thoroughly**: deletes the channel's private tools nobody else uses, its CLI session, its login keys and its site cookies in the Agent Reach browser. The shared browser profile is retained for explicit logout/reuse; unused private tools are pruned.
- **Removable default channels / Default channels are removable**: `state.json` records `removed_defaults`; `setup` and `update` never add them back; `add` brings one back.
- **doctor states / doctor states**: not_added, needs_setup, needs_login, unverified, ready, broken; plus `regressed` per channel (passed in the previous check, fails in the latest).
- **update** runs `uv tool install --force` on the latest release, reinstalls every added channel's tools at their declared versions (tested version when set, otherwise the newest version inside `floor`/`exclude`; also when Agent Reach itself has no new release), prunes tools no added channel uses, drops channels no longer in the registry, and refreshes the skill. `result.user_actions` lists in plain sentences what the user must do afterwards. Rollback: `uv tool install --force <previous release zip>`, then `agent-reach update --sync-only`. uv is the only supported installer. 1.5 and earlier installs are migrated on first `setup` / `update`; `config.yaml` keys are kept.
- **Update notice / Update notice**: explicit `update --check` refreshes the release cache. Ordinary queries never start a background version check or update dependencies. Cached newer releases appear in `meta.update`; updating requires the user’s agreement. / A newer version is only announced after an explicit check, and updates only with the user's consent.
- **Release notes / Release notes**: every CHANGELOG version section starts with a plain summary for users in Chinese and English; it becomes the GitHub release body the AI shows users.
- Xueqiu quotes and stock search via Tencent public quotes (no login); Xueqiu community data uses a session synced from the dedicated browser with `agent-reach login xueqiu --sync`.
- YouTube `transcribe`; LinkedIn reuses OpenCLI search and job-detail in the shared dedicated browser.

### 🔄 Changed

- Default channels: web (fallback only), YouTube, GitHub, V2EX, Bilibili. Optional: Xiaohongshu, Reddit, LinkedIn, Boss Zhipin, Xiaoyuzhou, Xueqiu. Experimental: Twitter, Facebook, Instagram.
- The agent skill is generated from the channel list and replaced on every update.

### 🗑️ Removed

- RSS channel (agents read feeds themselves).
- xhs-cli, rdt-cli, twitter-cli backends: they read browser cookies by themselves.
- `configure --from-browser`, `twitter-cookies`, `xhs-cookies`, the old `install --channels`, the old `skill --install`, `format`, `check-update`, MCP server entry.
- `watch` (use `doctor`, which now reports `regressed`), `doctor --live` (use `check`), `browser start` (the browser opens by itself), pipx installs.

### 🐛 Bug Fixes

#### 🔐 Boss Zhipin — login state misjudged (dual credential storage)

- **Root cause:** Boss has two independent login-state stores that do not represent each other — the local `~/.boss-agent/auth/session.enc` and the browser cookies inside the dedicated Chrome profile. `boss status` / `status --live` **only verify the former** (a leftover credential store from the Bridge/httpx era), while searches in the strict CDP mode of `existing-browser` go through the browser cookies. With "local old credentials + browser not logged in", `boss status` reports `logged_in: true`, misleading the Agent into skipping login and searching directly, which then hits `AUTH_EXPIRED`; the old runbook also forbade treating `_security_check` as "not logged in", and the two rules combined pushed the Agent toward the wrong "anti-scrape slider" branch.
- **Fix:** `check()` adds a 4th-layer read-only probe `_cdp_zhipin_login_cookie()`, using a minimal WebSocket client built on the standard library to ask the CDP browser directly (`Storage.getCookies`) whether a zhipin `wt2` cookie exists, **taking the browser as the source of truth**, without new dependencies, without launching a browser, and without running a search. No wt2 → clearly reports "browser not logged in, search will hit AUTH_EXPIRED" and points to "user login + `login --cdp`"; probe failure → reports "login state unknown"; the security-check page prompt also carries the browser cookie status.
- **Runbook correction:** removed the misleading rule "trust only `boss status` for login state", replaced it with doctor's browser cookie probe as the source of truth; after launching the dedicated Chrome, **force a pause for the user to visually confirm** the login state; `AUTH_EXPIRED` is treated as ground truth (go straight to the login flow, do not reinterpret it toward the security-check direction), and `_security_check` is handled as a slider only when there is no `AUTH_EXPIRED`.

### ✨ Features

#### 🎯 Boss Zhipin channel

- New `boss` channel: searches jobs and fetches full JD text via boss-agent-cli + real CDP Chrome.
- `check()` four-layer read-only probe (boss-agent-cli installed → port 9222 reachable → a zhipin tab exists → a `wt2` login cookie is present in the browser).
- Scraping goes through the public API (`search_jobs` + `job_card_browser` + `browser_source="existing-browser"`).
- `agent-reach install --system --channels=boss` installs the upstream boss-agent-cli pinned to a fixed commit (PRs #403–#407 merged into master) as the backend; it switches back to a version constraint once upstream ships an official release.
- The skill and install guide support "help me set up Boss Zhipin": the Agent launches a dedicated Chrome that listens only on the loopback address, the user only logs in manually, and the Agent finally verifies the login state and the CDP link.
- The pinned dependency moves from the fork snapshot `8ff6bd3` to the upstream commit `4c991b7` (PRs #403–#407 merged into master): a logged-in CDP session can be reused directly, and search can disable headless fallback via `--browser-source existing-browser`.
- code 37 is classified by its original wording: environmental anomalies become `ENVIRONMENT_RISK` and stop immediately; only an explicitly expired token/stoken allows a single refresh. The dedicated Chrome profile should be reused long-term and queried at a lower rate.

## [1.3.1] - 2026-03-27

### 🐛 Bug Fixes

#### 📈 Xueqiu — comprehensive fixes

- **Fixed the root cause of 400 errors:** `_ensure_cookies()` only visits the homepage and can only get `acw_tc` (an anti-DDoS token); `xq_a_token` is generated dynamically by Xueqiu's frontend JS and cannot be obtained through a plain HTTP request. Added a three-tier cookie loading strategy: ① read the config file (saved by `--from-browser`) → ② automatically extract from the local Chrome browser (requires browser-cookie3) → ③ homepage fallback
- **Fixed User-Agent:** `"agent-reach/1.0"` was recognized and rejected by Xueqiu's anti-scrape system; switched to a real Chrome UA
- **Fixed the missing `Referer` header:** all API requests now carry `Referer: https://xueqiu.com/`
- **Fixed the `get_hot_posts()` endpoint:** the old endpoint `/statuses/hot/listV3.json` was deprecated (returned an empty body); switched to `/v4/statuses/public_timeline_by_category.json`, correctly parsing the `item.data` JSON string for author/likes/text
- **Fixed `urllib.request.quote` → `urllib.parse.quote`:** explicitly use the correct module
- **Fixed `configure --from-browser` not extracting Xueqiu cookies:** added Xueqiu to `PLATFORM_SPECS`, and save only when `xq_a_token` is detected
- **Corrected misleading docs:** "no configuration needed" / "public API, no login required" in README/SKILL.md → accurately describe the need for browser cookies
- **Improved error messages:** on `check()` failure, prompt `configure --from-browser chrome` instead of "you may need a proxy"

---

## [1.3.0] - 2026-03-12

### 🆕 New Channels

#### 💻 V2EX
- Hot topics, node topics, topic detail + replies, user profile via public JSON API
- Zero config — no auth, no proxy, no API key required
- `get_hot_topics(limit)`, `get_node_topics(node_name, limit)`, `get_topic(id)`, `get_user(username)`
- Fetch hot posts, node posts, topic detail + replies, and user info via the public JSON API
- Zero config — no auth, no proxy, no API key required

### 📈 Improvements

- Channel count: 14 → 15
- Channel count: 14 → 15

---

## [1.1.0] - 2025-02-25

### 🆕 New Channels

#### ~~📷 Instagram~~ (removed — upstream blocked)
- ~~Read public posts and profiles via [instaloader](https://github.com/instaloader/instaloader)~~
- **Removed:** Instagram's aggressive anti-scraping measures broke all available open-source tools (instaloader, etc.). See [instaloader#2585](https://github.com/instaloader/instaloader/issues/2585). Will re-add when upstream recovers.
- **Removed:** Instagram's aggressive anti-scraping measures broke all available open-source tools (instaloader, etc.). Will re-add once upstream recovers.

#### 💼 LinkedIn
- Read person profiles, company pages, and job details via [linkedin-scraper-mcp](https://github.com/stickerdaniel/linkedin-mcp-server)
- Search people and jobs via MCP, with Exa fallback
- Fallback to Jina Reader when MCP is not configured
- Read personal profiles, company pages, and job details via linkedin-scraper-mcp
- Search people and jobs via MCP, with Exa as fallback
- Falls back to Jina Reader when MCP is not configured

#### 🏢 Boss Zhipin
- QR code login via [mcp-bosszp](https://github.com/mucsbr/mcp-bosszp)
- Job search and recruiter greeting via MCP
- Fallback to Jina Reader for reading job pages
- QR code login via mcp-bosszp
- Search jobs and greet recruiters via MCP
- Falls back to Jina Reader for reading job pages

### 📈 Improvements

- Channel count: 9 → 12
- `agent-reach doctor` now detects all 12 channels
- CLI: added `search-linkedin`, `search-bosszhipin` subcommands
- Updated install guide with setup instructions for new channels
- Channel count: 9 → 11
- `agent-reach doctor` now detects all 11 channels
- CLI: added `search-linkedin`, `search-bosszhipin` subcommands
- Install guide adds setup instructions for the new channels

---

## [1.0.0] - 2025-02-24

### 🎉 Initial Release

- 9 channels: Web, Twitter/X, YouTube, Bilibili, GitHub, Reddit, XiaoHongShu, RSS, Exa Search
- CLI with `read`, `search`, `doctor`, `install` commands
- Unified channel interface — each platform is a single pluggable Python file
- Auto-detection of local vs server environments
- Built-in diagnostics via `agent-reach doctor`
- Skill registration for Claude Code / OpenClaw / Cursor
- 9 channels: Web, Twitter/X, YouTube, Bilibili, GitHub, Reddit, Xiaohongshu, RSS, Exa Search
- CLI supports `read`, `search`, `doctor`, `install` commands
- Unified channel interface — each platform is a single pluggable Python file
- Auto-detection of local vs server environments
- Built-in diagnostics via `agent-reach doctor`
- Skill registration support for Claude Code / OpenClaw / Cursor
