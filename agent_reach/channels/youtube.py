# -*- coding: utf-8 -*-
"""YouTube — video info, search, subtitles (yt-dlp) and Whisper transcription."""

import html
import json
import os
import re
import shutil
import sys

from agent_reach.runtime.result import (
    BAD_INPUT,
    NOT_FOUND,
    PLATFORM_BLOCKED,
    RATE_LIMITED,
    ReachError,
    make_item,
)
from agent_reach.runtime.run import CommandFailed, run_cmd
from agent_reach.utils.paths import private_temporary_directory

from .base import Action, Channel, Param

_VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
_VTT_TIME_RE = re.compile(
    r"^(?:\d{2,}:)?\d{2}:\d{2}\.\d{3}[ \t]+-->[ \t]+"
    r"(?:\d{2,}:)?\d{2}:\d{2}\.\d{3}(?:[ \t]|$)"
)
_TAG_RE = re.compile(r"<[^>]+>")
_RAW_KEYS = ("id", "duration", "view_count", "like_count", "channel_id", "tags", "categories")


def ytdlp_tls_args() -> list:
    """yt-dlp trusts its bundled certifi and ignores SSL_CERT_FILE; behind a TLS-inspecting
    proxy (corporate, school) every request then fails CERTIFICATE_VERIFY_FAILED."""
    if os.environ.get("SSL_CERT_FILE") or os.environ.get("SSL_CERT_DIR"):
        return ["--compat-options", "no-certifi"]
    return []


def _ytdlp_argv(*args: str) -> list:
    """Run the yt-dlp installed with Agent Reach (one of its dependencies)."""
    runtime = []
    if shutil.which("deno") is None and shutil.which("node"):
        runtime = ["--js-runtimes", "node"]
    return [sys.executable, "-m", "yt_dlp", "--no-warnings", *ytdlp_tls_args(), *runtime, *args]


def _video_url(target: str) -> str:
    from agent_reach.utils.url import host_matches

    t = str(target).strip()
    if _VIDEO_ID_RE.match(t):
        return f"https://www.youtube.com/watch?v={t}"
    candidate = t if "://" in t else f"https://{t}"
    if host_matches(candidate, "youtube.com", "youtu.be"):
        return candidate
    raise ReachError(BAD_INPUT, "target must be a YouTube link or 11-character video id")


def _run_ytdlp(args: list, timeout: float, cwd=None) -> str:
    try:
        return run_cmd(_ytdlp_argv(*args), timeout=timeout, cwd=cwd, label="yt-dlp")
    except CommandFailed as exc:
        err = exc.stderr.lower()
        if any(s in err for s in ("video unavailable", "private video", "has been removed", "does not exist")):
            raise ReachError(NOT_FOUND, exc.message) from None
        if "sign in to confirm" in err or "not a bot" in err:
            raise ReachError(
                PLATFORM_BLOCKED,
                exc.message,
                hint="YouTube returned a verification challenge. Stop this request; this does not establish that the public video requires login.",
            ) from None
        if "429" in err or "too many requests" in err:
            raise ReachError(RATE_LIMITED, exc.message) from None
        raise


def pick_subtitle_track(lang: str, video_lang, manual: dict, auto: dict):
    """(track code, 'manual'|'auto') to download, or None.

    `lang` is 'auto' or a comma-separated preference list. With 'auto' the order is:
    human subtitles in the video's language, its original auto-captions, then
    English, then any human subtitle. Auto-caption keys without '-orig' are
    machine translations, so they are only used when asked for explicitly.
    """
    def find(code: str):
        for pool, source in ((manual, "manual"), (auto, "auto")):
            if code in pool:
                return code, source
        base = code.split("-")[0]
        for key in manual:  # 'fr' also matches 'fr-FR', 'fr-CA'…
            if key.split("-")[0] == base and not key.endswith("-orig"):
                return key, "manual"
        return None

    wanted = [x.strip() for x in str(lang or "auto").split(",") if x.strip()]
    if wanted and wanted != ["auto"]:
        return next((hit for hit in map(find, wanted) if hit), None)
    order = []
    if video_lang:
        base = str(video_lang).split("-")[0]
        order += [video_lang, base, f"{video_lang}-orig", f"{base}-orig"]
    order += ["en", "en-orig"]
    for code in order:
        hit = find(code)
        if hit and (hit[1] == "manual" or code.endswith("-orig") or code == video_lang or code == "en-orig"):
            return hit
    if manual:
        return sorted(manual)[0], "manual"
    origs = sorted(k for k in auto if k.endswith("-orig"))
    return (origs[0], "auto") if origs else None


def _iso_date(yyyymmdd) -> str:
    s = str(yyyymmdd or "")
    return f"{s[:4]}-{s[4:6]}-{s[6:8]}" if len(s) == 8 and s.isdigit() else ""


def vtt_to_text(vtt: str) -> str:
    """Plain text from WebVTT: drop headers, timings, tags; collapse auto-caption repeats."""
    out: list[str] = []
    in_cue = False
    block_start = True
    metadata = False
    for line in vtt.splitlines():
        s = line.strip()
        if not s:
            in_cue, block_start, metadata = False, True, False
            continue
        if block_start:
            block_start = False
            metadata = s in {"NOTE", "STYLE", "REGION"} or s.startswith(("NOTE ", "NOTE\t"))
        if metadata:
            continue
        if _VTT_TIME_RE.match(s):
            in_cue = True
            continue
        if not in_cue:
            # Headers and optional cue identifiers precede the timing line.
            continue
        s = html.unescape(_TAG_RE.sub("", s)).strip()
        if s and (not out or out[-1] != s):
            out.append(s)
    return "\n".join(out)


class YouTubeChannel(Channel):
    name = "youtube"
    description = "YouTube videos and subtitles"

    level = "default"
    #: transcribe re-encodes and chunks audio
    prereqs = ("ffmpeg",)
    actions = (
        Action(
            "read",
            "Video title, channel, date and description",
            (Param("target", "video link or id"),),
            (("yt-dlp", "_ytdlp_read"),),
            live_test={"target": "https://www.youtube.com/watch?v=jNQXAC9IVRw"},
        ),
        Action(
            "search",
            "Search videos",
            (
                Param("query", "what to search for"),
                Param("limit", "max results", required=False, type=int, default=5),
            ),
            (("yt-dlp", "_ytdlp_search"),),
            live_test={"query": "python tutorial", "limit": 2},
        ),
        Action(
            "subtitle",
            "Full subtitle text of a video (manual or auto captions)",
            (
                Param("target", "video link or id"),
                Param("lang", "preferred languages, comma separated; 'auto' = the video's own language, then English", required=False, default="auto"),
            ),
            (("yt-dlp", "_ytdlp_subtitle"),),
            live_test={"target": "https://www.youtube.com/watch?v=jNQXAC9IVRw"},
        ),
        Action(
            "transcribe",
            "Speech-to-text of a video's audio (uses Groq/OpenAI Whisper quota)",
            (Param("target", "video link or id"),),
            (("whisper", "_whisper_transcribe"),),
            timeout=1800,
        ),
    )

    def can_handle(self, url: str) -> bool:
        from agent_reach.utils.url import host_matches

        return host_matches(url, "youtube.com", "youtu.be")

    # ── unified entry backends ──

    def _ytdlp_read(self, *, target: str, timeout: float) -> list:
        out = _run_ytdlp(["--dump-json", "--skip-download", _video_url(target)], timeout)
        info = json.loads(out.splitlines()[-1])
        return [
            make_item(
                title=info.get("title"),
                url=info.get("webpage_url"),
                author=info.get("uploader") or info.get("channel"),
                published_at=_iso_date(info.get("upload_date")),
                text=info.get("description"),
                raw={k: info.get(k) for k in _RAW_KEYS},
            )
        ]

    def _ytdlp_search(self, *, query: str, limit: int, timeout: float) -> list:
        out = _run_ytdlp(["--flat-playlist", "--dump-json", f"ytsearch{limit}:{query}"], timeout)
        items = []
        for line in out.splitlines():
            if not line.strip():
                continue
            info = json.loads(line)
            vid = info.get("id")
            items.append(
                make_item(
                    title=info.get("title"),
                    url=info.get("url") or (f"https://www.youtube.com/watch?v={vid}" if vid else None),
                    author=info.get("channel") or info.get("uploader"),
                    text=info.get("description"),
                    raw={k: info.get(k) for k in _RAW_KEYS},
                )
            )
        return items

    def _ytdlp_subtitle(self, *, target: str, lang: str, timeout: float) -> list:
        url = _video_url(target)
        with private_temporary_directory(prefix="agent-reach-subs-") as tmp:
            # 1 page request for the track list, then exactly 1 subtitle download:
            # asking yt-dlp for several languages at once fetched every one of them
            # and quickly triggered YouTube's HTTP 429.
            info_path = os.path.join(tmp, "info.json")
            out = _run_ytdlp(["--dump-json", "--skip-download", url], timeout)
            info = json.loads(out.splitlines()[-1])
            with open(info_path, "w", encoding="utf-8") as fh:
                json.dump(info, fh)
            manual = info.get("subtitles") or {}
            auto = info.get("automatic_captions") or {}
            choice = pick_subtitle_track(lang, info.get("language"), manual, auto)
            if choice is None:
                tracks = sorted(set(manual) | {k for k in auto if k.endswith("-orig")})
                raise ReachError(
                    NOT_FOUND,
                    f"no subtitles for '{lang}' on this video",
                    hint=f"available tracks: {', '.join(tracks) or 'none'}; pass --lang with one of them",
                )
            code, source = choice
            _run_ytdlp(
                [
                    "--load-info-json", info_path,
                    "--skip-download", "--no-simulate",
                    "--write-subs" if source == "manual" else "--write-auto-subs",
                    "--sub-langs", re.escape(code), "--sub-format", "vtt",
                    "-o", "%(id)s.%(ext)s",
                ],
                timeout,
                cwd=tmp,
            )
            files = [f for f in os.listdir(tmp) if f.endswith(".vtt")]
            if not files:
                raise ReachError(NOT_FOUND, f"subtitle track {code} could not be downloaded")
            with open(os.path.join(tmp, files[0]), encoding="utf-8", errors="replace") as fh:
                text = vtt_to_text(fh.read())
        return [make_item(title=info.get("title"), url=url, text=text,
                          raw={"lang": code, "source": source, "video_language": info.get("language")})]

    def _whisper_transcribe(self, *, target: str, timeout: float) -> list:
        from agent_reach.transcribe import NoProviderConfigured, TranscribeError
        from agent_reach.transcribe import transcribe as _transcribe

        url = _video_url(target)
        try:
            text = _transcribe(url)
        except NoProviderConfigured:
            raise ReachError(
                "NEED_SETUP", "no Whisper API key configured",
                hint="Ask the user for a free key from https://console.groq.com, then run `agent-reach configure groq-key`.",
            ) from None
        except TranscribeError as exc:
            raise ReachError("UPSTREAM_BROKEN", str(exc)[:300]) from None
        return [make_item(url=url, text=text)]
