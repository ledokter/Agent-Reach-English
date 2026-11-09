"""Read-only session discovery and explicit connection choices. Never logs a user in."""
import json
import urllib.request
from datetime import datetime
from urllib.parse import urlsplit

from agent_reach.utils.url import host_matches

from .result import BAD_INPUT, ReachError

# These describe public routes an agent can try, not authenticated Reach readiness.
# A successful sample depends on the tool, network exit, content and platform response.
_PUBLIC_ACCESS = {
    'web': "Use the Agent's existing web search and read first; call Reach only for remaining gaps.",
    'github': 'Public repos, README, Issues/PRs and public comments can be read via web or public APIs first.',
    'youtube': 'Public search and descriptions can be read first; native tools can fetch comments, subtitles and timestamps for some samples.',
    'bilibili': 'Public search, descriptions and stats can be read first; some public APIs expose comments and reply threads.',
    'xiaoyuzhou': 'Podcast transcription requires a Groq Key; installation does not require login.',
    'v2ex': 'Public thread bodies and some replies can be read first; completeness and pagination need separate verification.',
    'reddit': 'Public search, bodies and some comments can be read first; some public JSON samples may include comments and parent_id.',
    'twitter': 'Public search summaries and some full single posts can be tried first; public embeds do not provide comment threads.',
    'xiaohongshu': 'Public discovery pages may expose note IDs and authors; this does not mean bodies or comments are readable.',
    'instagram': 'Public search or profile info can be tried first; HTML may be just an app shell, captions and comments are not uniformly verified.',
    'facebook': 'Public search summaries can be tried first; post bodies and comments depend on the page and access path.',
    'linkedin': 'Public jobs can be searched and read in detail first; login-free job samples were obtained on 2026-10-21, not all jobs are guaranteed readable.',
    'boss': 'Public job indexes and pages can be tried first; no anonymous granular acceptance was done this round.',
    'xueqiu': 'Public stock quotes and name search can be tried first; community content depends on the chosen path.',
}

_CAPABILITY_LIMITS = {
    'youtube': ['read returns metadata and description; no standalone comments action.',
                'Subtitles depend on available tracks; transcription also needs a configured service and quota, login does not guarantee subtitles.'],
    'bilibili': ['read returns metadata and description; no standalone comments action.',
                 'subtitle currently reads subtitles for the first episode; it may require login and does not represent the whole multi-part video.'],
    'reddit': ['read only promises the posts and comments it returns; it does not guarantee a complete comment tree and provides no post-comment action.'],
    'twitter': ['thread only covers the replies actually returned; it does not guarantee a complete comment stream and provides no posting action.'],
    'xiaohongshu': ['Only reports the bodies, loaded comments and replies actually read; no complete export is promised.'],
    'instagram': ['search searches for users; there is no arbitrary post read or standalone comments action.'],
    'facebook': ['Currently only declares search/profile; no standalone post read or comment export is promised.'],
    'linkedin': ['Currently only declares job search and JD read; no contacts or activity feed scraping is promised.'],
    'boss': ['Currently only declares job search and JD read; login does not guarantee the platform always allows access.'],
    'v2ex': ['Whether replies are complete must be verified against pagination and the actual returned count.'],
}


# Public web options and authenticated Reach actions; detailed limits stay in capability_summary.
_QUICK_ACCESS = {
    'xiaoyuzhou': ('🔑 Transcription needs Key', '—'),
    'github': ('✅ Find projects, read docs, see discussions, see comments', '—'),
    'youtube': ('✅ Find videos, read descriptions, read subtitles', '—'),
    'bilibili': ('✅ Find videos, read descriptions', '❌ Read subtitles'),
    'v2ex': ('✅ Read posts, see replies', '—'),
    'web': ('✅ Search the web, read pages', '—'),
    'reddit': ('✅ Search posts, read bodies, see comments', '—'),
    'twitter': ('✅ Search summaries, try reading originals', '❌ Search tweets, see activity, see replies'),
    'xiaohongshu': ('✅ Search summaries, find links', '❌ In-site search, read bodies, see comments'),
    'instagram': ('✅ Search bios', '❌ Find users, see profiles, see posts'),
    'facebook': ('✅ Search summaries', '❌ In-site search, see profiles'),
    'linkedin': ('✅ Find jobs, read public details', '❌ In-site search'),
    'boss': ('✅ Search titles, find links', '❌ In-site search, read details'),
    'xueqiu': ('✅ Find stocks, check quotes', '❌ See hot posts, see hot stocks'),
}

_DISPLAY_NAMES = {
    'xiaoyuzhou': 'Xiaoyuzhou',
    'github': 'GitHub', 'youtube': 'YouTube', 'bilibili': 'Bilibili', 'v2ex': 'V2EX',
    'web': 'Web', 'reddit': 'Reddit', 'twitter': 'X / Twitter', 'facebook': 'Facebook',
    'instagram': 'Instagram', 'xiaohongshu': 'Xiaohongshu (RedNote)', 'linkedin': 'LinkedIn',
    'boss': 'Boss Zhipin', 'xueqiu': 'Xueqiu',
}

_STATUS_LABELS = {
    'not_added': 'Not connected, can add on demand', 'needs_setup': 'Needs setup', 'unverified': 'Connected, unverified',
    'ready': 'Verified', 'search_ready': 'Search verified only',
    'needs_login': 'Tested actions require login', 'cooldown': 'Access paused',
    'needs_user_action': 'Awaiting manual verification', 'broken': 'Path currently broken',
}


def _local_greeting():
    """Use the installing computer's clock and timezone, without a network lookup."""
    hour = datetime.now().hour
    if 5 <= hour < 11:
        return 'Good morning, what would you like to search? ☀️'
    if 11 <= hour < 14:
        return 'Good noon, what would you like to search?'
    if 14 <= hour < 18:
        return 'Good afternoon, what would you like to search?'
    if 18 <= hour < 22:
        return 'Good evening, what would you like to search?'
    return "It's late, what would you like to search? 🌙"

def _upgrade_lines(result):
    """Only for users coming from 1.5: what was kept, what changed, what is left to do."""
    migration = result.get('migration')
    if not migration:
        return []
    lines = ['**This is an upgrade from the old version (1.5):**', '',
             '- Your keys and settings are preserved.',
             '- RSS subscriptions and Exa full-web search are no longer offered separately; use "Web" for all search and page reading.',
             '- Platforms that need login like X/Twitter and Xiaohongshu now use Agent Reach\'s own dedicated browser; the first time it will try to reuse your Chrome login.',
             '- CLI tools you installed separately before (e.g. twitter-cli, bili) are kept as-is, not removed.']
    suggested = [_DISPLAY_NAMES.get(n, n) for n in migration.get('suggested_channels') or []]
    if suggested:
        lines.append('- You previously used ' + ', '.join(suggested) + '; to keep using them just tell me "add XX".')
    old = result.get('old_copies') or {}
    if old.get('removed'):
        lines.append('- The old version has been removed and will no longer conflict with the new one.')
    for item in old.get('failed') or []:
        from .legacy import manual_command
        lines.append(f"- The old version could not be removed; please run: `{manual_command(item)}`")
    return lines + ['']



def installation_report(result):
    """Render one short receipt; keep detailed evidence in the structured summary."""
    def cell(value):
        return str(value).replace('|', r'\|').replace('\n', ' ')

    entries = result['capability_summary']['channels']
    installs = {row['channel']: row for row in result['default_channels']}
    installed = sum(bool(row['ok']) for row in installs.values())
    completed = all(row['ok'] for row in installs.values())
    lines = [
        _local_greeting(), '',
        f"**Agent Reach {result['version']} {'installation complete' if completed else 'installation one step short'}.** "
        f'Default features: {installed}/{len(installs)} ready.', '',
        *_upgrade_lines(result),
        '✅ no login needed; ❌ try after login; 🔑 needs Key; — no extra login.', '',
        '| Platform | What works without login | Try after login |', '|---|---|---|',
    ]
    for entry in sorted(entries, key=lambda item: item['level'] != 'default'):
        name = entry['channel']
        label = _DISPLAY_NAMES.get(name, name)
        item = installs.get(name)
        if entry['level'] == 'default':
            if item and not item['ok']:
                label += '(install failed: ' + item.get('error', {}).get('code', 'UNKNOWN') + ')'
            elif not item:
                label += '(kept user removal)'
        elif entry['reach_status'] in {'needs_setup', 'needs_login', 'cooldown', 'needs_user_action', 'broken'}:
            label += '(' + _STATUS_LABELS[entry['reach_status']] + ')'
        public, login = _QUICK_ACCESS.get(name, (entry['public_access'], '—'))
        lines.append('| ' + ' | '.join(cell(value) for value in (label, public, login)) + ' |')
    verified = [entry for entry in entries if entry['verified_actions']]
    if verified:
        names = '; '.join(_DISPLAY_NAMES.get(entry['channel'], entry['channel']) + ': ' +
                         '/'.join(entry['verified_actions']) for entry in verified)
        lines += ['', 'Verified: ' + names + '. The rest have not been tested online item by item.']
    else:
        lines += ['', 'No item-by-item online testing yet.']
    lines += ['Find summaries, titles and links via search engines first; comments follow what was actually read, subtitles require the video to provide them.', '',
              '**Just say what you want to look up.** It will try to reuse an existing login first; when you genuinely need to log in, a window will open.']
    return '\n'.join(lines) + '\n'



def capability_summary(channels, statuses):
    """Describe public options, declared actions and local evidence without any I/O.

    Management supplies status records so this summary cannot initiate discovery,
    installation, login or a live request. Actions always come from the registry.
    """
    by_name = {entry['channel']: entry for entry in statuses}
    entries = []
    for ch in channels:
        current = by_name.get(ch.name, {})
        names = [action.name for action in ch.actions]
        can_login = bool(ch.login_url or ch.login_argv)
        auth_actions = {'bilibili': ['subtitle'], 'xueqiu': ['hot_posts', 'hot_stocks']}.get(
            ch.name, names if can_login else [])
        entries.append({
            'channel': ch.name,
            'level': ch.level,
            'reach_status': current.get('status', 'unverified'),
            'verified_actions': current.get('verified_actions', []),
            'actions': [{'action': action.name, 'detail': action.help} for action in ch.actions],
            'public_access': _PUBLIC_ACCESS.get(ch.name, "Try the Agent's existing public search and read first."),
            'authentication': {
                'when': 'only_if_required',
                'may_enable_actions': [name for name in auth_actions if name in names],
                'note': 'When the chosen path for a remaining task actually requires auth, reuse the authorized session first, then ask the user to log in; actions still need verification after login.',
            },
            'limits': _CAPABILITY_LIMITS.get(ch.name, []),
        })
    message = ["Use the Agent's existing public search and read first; Reach fills in capabilities on demand, installation does not require logging in to each platform."]
    for entry in entries:
        actions = '/'.join(action['action'] for action in entry['actions'])
        status_label = _STATUS_LABELS.get(entry['reach_status'], entry['reach_status'])
        limits = ' '.join(entry['limits'])
        message.append(f"{entry['channel']}: {entry['public_access']} Reach {actions} ({status_label}). {limits}")
    return {
        'policy': 'public_first; login_only_for_remaining_task_when_required',
        'evidence_note': 'Public path descriptions come from samples and access conditions and cannot replace on-host Reach acceptance; network, 403, timeout or captcha each cannot alone prove login is required.',
        'channels': entries,
        'message': '\n'.join(message),
    }


def cdp_url():
    from .browser import CDP_URL
    return validate_cdp(CDP_URL)


def validate_cdp(value):
    try:
        u = urlsplit(value)
        valid = (u.scheme == 'http' and u.hostname in {'localhost', '127.0.0.1', '::1'}
                 and u.port and not u.username and not u.password and not u.query
                 and not u.fragment and u.path in ('', '/'))
    except (TypeError, ValueError):
        valid = False
    if not valid:
        raise ReachError(BAD_INPUT, 'CDP must be a loopback HTTP address with an explicit port')
    return value.rstrip('/')


def cdp_status():
    url = cdp_url()
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(url + '/json/list', timeout=2) as resp:
            tabs = json.loads(resp.read(1024 * 1024))
        found = isinstance(tabs, list) and any(
            isinstance(t, dict) and t.get('type') == 'page'
            and host_matches(t.get('url', ''), 'zhipin.com') for t in tabs)
        return {'endpoint': url, 'connected': isinstance(tabs, list), 'boss_tab_present': bool(found)}
    except (OSError, ValueError):
        return {'endpoint': url, 'connected': False, 'boss_tab_present': False}


def require_boss_cdp():
    from . import browser, session_reuse
    session_reuse.prepare("boss")
    if not cdp_status()['boss_tab_present']:
        browser.open_url('https://www.zhipin.com/web/geek/jobs')
    browser.touch()
    return browser.CDP_URL
