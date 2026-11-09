"""Subtitle track choice: the video's own language first, one download only."""
import json

import pytest

from agent_reach.channels import youtube
from agent_reach.channels.youtube import YouTubeChannel, pick_subtitle_track
from agent_reach.runtime.result import ReachError

# Auto-caption keys: '<lang>-orig' is the speech recognition, the rest are machine translations.
AUTO_FR = {"fr-orig": [{}], "fr": [{}], "en": [{}], "zh-Hans": [{}], "ja": [{}]}


def test_auto_prefers_human_subtitles_in_video_language():
    assert pick_subtitle_track("auto", "fr", {"fr": [{}], "en": [{}]}, AUTO_FR) == ("fr", "manual")


def test_auto_matches_regional_human_subtitles():
    assert pick_subtitle_track("auto", "fr", {"fr-FR": [{}]}, {}) == ("fr-FR", "manual")


def test_auto_uses_original_auto_captions_of_a_french_video():
    assert pick_subtitle_track("auto", "fr", {}, AUTO_FR) in {("fr", "auto"), ("fr-orig", "auto")}


def test_auto_never_picks_a_machine_translation():
    # A French video with only auto captions must not come back in English or Chinese.
    code, _ = pick_subtitle_track("auto", "fr", {}, AUTO_FR)
    assert code.startswith("fr")


def test_auto_without_known_language_falls_back_to_original_captions():
    assert pick_subtitle_track("auto", None, {}, {"de-orig": [{}], "en": [{}]}) == ("de-orig", "auto")


def test_auto_english_video():
    assert pick_subtitle_track("auto", "en", {}, {"en-orig": [{}], "en": [{}], "fr": [{}]})[0].startswith("en")


def test_explicit_list_is_respected_in_order():
    assert pick_subtitle_track("zh-Hans,en", "fr", {}, AUTO_FR) == ("zh-Hans", "auto")
    assert pick_subtitle_track("es,en", "fr", {}, AUTO_FR) == ("en", "auto")


def test_nothing_available():
    assert pick_subtitle_track("auto", "fr", {}, {}) is None
    assert pick_subtitle_track("es", "fr", {}, AUTO_FR) is None


def test_default_language_is_auto():
    action = next(a for a in YouTubeChannel.actions if a.name == "subtitle")
    lang = next(p for p in action.params if p.name == "lang")
    assert lang.default == "auto"


def _fake_ytdlp(info, calls):
    def run(args, timeout, cwd=None):
        calls.append(args)
        if "--dump-json" in args:
            return json.dumps(info)
        lang = args[args.index("--sub-langs") + 1].replace("\\", "")
        with open(f"{cwd}/{info['id']}.{lang}.vtt", "w", encoding="utf-8") as fh:
            fh.write("WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nBonjour à tous\n")
        return ""
    return run


def test_subtitle_downloads_exactly_one_track(monkeypatch):
    info = {"id": "abcdefghijk", "title": "Vidéo", "language": "fr", "subtitles": {}, "automatic_captions": AUTO_FR}
    calls = []
    monkeypatch.setattr(youtube, "_run_ytdlp", _fake_ytdlp(info, calls))
    [item] = YouTubeChannel()._ytdlp_subtitle(target="abcdefghijk", lang="auto", timeout=5)
    assert item["text"] == "Bonjour à tous"
    assert item["raw"]["video_language"] == "fr"
    download = calls[1]
    assert "--load-info-json" in download and "--write-auto-subs" in download
    assert "," not in download[download.index("--sub-langs") + 1]


def test_subtitle_not_found_lists_tracks(monkeypatch):
    info = {"id": "abcdefghijk", "title": "x", "language": "fr", "subtitles": {}, "automatic_captions": {"fr-orig": [{}]}}
    monkeypatch.setattr(youtube, "_run_ytdlp", _fake_ytdlp(info, []))
    with pytest.raises(ReachError) as exc:
        YouTubeChannel()._ytdlp_subtitle(target="abcdefghijk", lang="es", timeout=5)
    assert exc.value.code == "NOT_FOUND"
    assert "fr-orig" in (exc.value.hint or "")
