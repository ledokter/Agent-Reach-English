# Sessions and the dedicated browser

Read this when the user wants to log in, log out, switch accounts, or a result returns `NEED_LOGIN`.

## Dedicated browser

- All browser channels share one dedicated browser profile, kept separate from the user's everyday Chrome; the program never closes or modifies the user's everyday browser.
- The core is CloakBrowser by preference; if download or install fails, use the Chrome already installed on this machine and remember that fallback rather than re-downloading every time. Once the network is fixed you can retry with `agent-reach browser setup --retry-cloak`.
- `agent-reach add <channel>` automatically prepares Node, OpenCLI, the core, and extensions. Tools are installed at the versions tested for this release. On Windows when falling back to Chrome, the user may need to click "Add to Chrome" once.
- Headless by default; no windows pop up. Only `agent-reach login <channel>` shows a window; while that window is open, queries use it directly and are not collapsed, and during the user's login you wait until the user says they are done before querying. After the window closes, subsequent queries go back to headless.
- It auto-closes after 10 minutes idle and reopens on the next call; real page interactions and Reach calls reset the timer. During login, sessions are saved periodically, so the user does not need to close the window.
- Concurrency is allowed: at most 2 simultaneous streams per platform and 4 across all platforms combined; extras queue, waiting at most 2 minutes before returning `BUSY` if still unavailable. Two searches on the same platform are spaced at least 10 seconds apart. Opening a login window, logging out, or reinstalling the browser waits for any running query to finish first.
- `agent-reach browser status` shows status, `browser setup` prepares the core and extensions, `browser stop` closes the browser managed by the program.

## Automatic reuse of existing logins

1. The first time a website is used, if the user's Chrome has the OpenCLI extension connected, the program copies that site's login (only that site's cookies) once into the dedicated browser. It does not copy the whole browser directory, other sites, or the password store, and it does not modify the source browser.
2. After a successful copy, the saved session is reused continuously; it is not re-copied on a timer. The presence of cookies does not mean the login is still valid — actual action results are authoritative.
3. When the user's Chrome is not connected to the extension, automatic reuse cannot be promised, nor can you conclude the user is not logged in; in that case use the session Reach has already saved.
4. When multiple browsers on this machine are logged in to the site: `agent-reach browser profiles` lists the sources, and `agent-reach browser use <ID>` selects one — no random switching.
5. `agent-reach login <channel> --import-existing` actively re-copies that site's login once, without opening a window. If no reusable login is found, or OpenCLI Bridge is not running, it returns `NEED_SETUP` and the saved session is unchanged.
6. Once the user has logged in personally in the dedicated window, or has run `logout` / `remove`, automatic copying no longer happens, to avoid reviving a login that was signed out.

## When the user must log in personally

- Only when a result actually returns `NEED_LOGIN` and the remaining task genuinely needs that path do you ask the user to log in. A login button next to the body text does not count as a login requirement.
- `agent-reach login <channel>` opens the dedicated browser to that site's login page; the user completes the login personally. You do not log in for them, do not ask for passwords, and do not output cookies.
- If the returned `next` field lists follow-up steps, follow them; some native-tool channels (e.g. Xueqiu) require running `agent-reach login <channel> --sync` after login.
- Once the user is done, re-run the original action to verify.

## Platform differences

- Boss Zhipin's in-site search goes through OpenCLI and shares the dedicated browser. If a job detail falsely requires login due to an upstream misreport, do not make the user log in repeatedly.
- Bilibili only hands an existing login to Bilibili's official command-line tool when reading subtitles; ordinary search does not prepare the browser.
- Xueqiu community actions require login; sessions expire within a few hours, after which the login steps are repeated.

## Logout and removal

- `agent-reach logout <channel>`: clears that site's login and the channel's own state from the dedicated browser; other sites are kept.
- `agent-reach remove <channel>`: removes the channel and also clears that site's login and storage; other sites are kept. On cleanup failure the channel record is kept and an error is returned, and the user can retry.
- After either, automatic copying of that site's login no longer happens.
