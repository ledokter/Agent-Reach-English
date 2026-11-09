# Maintenance

Read this when an update fails, the browser won't start, a channel errors out, or the user wants to uninstall.

- Update: `agent-reach update` upgrades Agent Reach, the tools for added channels, and the skill; `agent-reach update --check` only checks whether a new version is available. Run only after the user agrees.
- Status: `agent-reach doctor --text` reads local state without going online; `agent-reach check <channel> --text` runs one live online test (`--search` tests only search/jobs). A successful install does not mean a live test passed.
- Browser: `agent-reach browser status` shows status, `browser setup` prepares the core and extensions, `browser stop` shuts it down; after a CloakBrowser download fails and the network is fixed, run `browser setup --retry-cloak`.
- Distinguish the failure stage: dependency download, browser connection, login, page load, and platform rate-limiting are each separate; a network timeout must not be reported as a login failure.
- Upstream tool errors: record the error and version, then run `agent-reach update` once with the user's consent; do not modify the upstream tool's install files, and do not retry in a loop.
- `PLATFORM_BLOCKED`, `RATE_LIMITED`, `NEED_LOGIN`, `BUSY`: stop the current attempt and wait for the user to handle it before continuing; do not repeatedly open windows.
- Keys and proxy: `agent-reach configure groq-key | openai-key | proxy | github-token`; values are provided by the user personally.
- Port conflict (`Port <n> belongs to an unmanaged browser`): another program is occupying the dedicated browser port (default 9222). Do not close the user's program; after the user agrees, run `agent-reach configure browser-port <free-port>`.
- Uninstall: first run `agent-reach uninstall --dry-run` to show the user the scope, then `agent-reach uninstall` after confirmation. Only items Reach installed itself are removed; the user's other files and browsers are kept.
