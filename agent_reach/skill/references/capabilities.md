# Capability scope

Read this when the user asks "what can it fetch, and is it complete?" or when you need to judge how complete a result is. The table below lists declared capabilities — it does not mean every network path, account, and piece of content has been verified in practice.
Read when the user asks what can be fetched or how complete a result is. Declared capabilities, not guaranteed results.

## Three layers explained

- **Public, attemptable**: The Agent's existing web tools, native tools, or public APIs may already satisfy the task; no browser install or login is required. Answer based on the evidence actually obtained.
- **Reach supplement**: Actions declared by the current release, see `agent-reach channels`. When configuration is needed, first reuse a session already saved in the dedicated browser; only have the user log in personally when the chosen path actually requires login.
- **Verified on this machine**: Lists only the specific actions most recently accepted on this machine; a successful install, a saved session, and network reachability do not amount to business acceptance.

## Channels in this release

| Channel | Public path may attempt | Reach supplement and boundary |
|---|---|---|
| GitHub | Public repos, README, Issue/PR | Repo search, reading repo/Issue/PR and returned comments; private permissions judged separately |
| YouTube | Search, titles, descriptions; native tools may obtain some comments and subtitle body text | search/read/subtitle/transcribe; no unified comments action currently; a track list is not the subtitle body text, and transcription without subtitles depends on the relevant tool |
| Bilibili | Search, descriptions; some public APIs can return comments with parent/child IDs | search/read/hot/subtitle/users/user/user_videos/rank; no unified comments action currently; subtitles vary by video and access path |
| Reddit | Search, body text, some comments; some public JSON may contain parent/child IDs | Browser search/read/subreddit; login depends on the chosen path, full comment trees or all replies are not guaranteed; posting comments is not supported |
| X/Twitter | Public single posts hit by search; some official public embeds can return full text | search/profile/tweets/thread; a readable single post does not mean the reply stream is readable, and a full comment tree is not guaranteed |
| Xiaohongshu | Public listings or indexes may have note IDs, authors, titles; empty fields must not be guessed | search/read/comments; text descriptions, top-level comments and already-loaded replies; all comments are not guaranteed, and understanding images/video is not claimed |
| Instagram | Some indexes and shallow homepage info; the HTML app shell does not count as a post | search to find users, profile for the homepage, posts for a given user's post descriptions; no unified comments action, and understanding images/video is not claimed |
| Facebook | Some indexes or HTML summaries; summaries may be truncated | search/profile; no unified detail or comments action, search summaries are not treated as full text |
| LinkedIn | Search public job postings, read public JDs | jobs/read tries the public web page first; only with `opencli` specified does it go directly through the site; all jobs being readable is not guaranteed |
| Boss Zhipin | Job summaries may exist in the search index | search/read for job listings and JDs; numbers must not be guessed from encoded salaries; fallback detail capability follows the channel declaration |
| V2EX | Topics, body text, and public replies | hot/node/read/user; the returned scope is whatever this response yields, hidden or missing replies are not guaranteed |
| Xueqiu | Some public market quotes and index info | quote/search/hot_posts/hot_stocks; market and community paths are accepted separately |
| Web | Agent's built-in search/read | Reach web search/read is an anonymous fallback; summaries, page shells, and verification pages are not treated as full body text |
| Xiaoyuzhou | Episode page titles, descriptions | transcribe for full-episode transcription; requires the user to provide a Groq key (`agent-reach configure groq-key`) |

When describing post-login capability, use "may enable/attempt the browser actions above" — do not say "all comments are supported after login". When the user skips login, deliver the public evidence already on hand.
