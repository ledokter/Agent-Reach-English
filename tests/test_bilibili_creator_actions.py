"""Read-only uploader (UP主) and leaderboard actions on the bilibili channel."""
import pytest

from agent_reach.channels import bilibili
from agent_reach.channels.bilibili import BilibiliChannel, _uploader
from agent_reach.runtime.result import ReachError


def _capture(monkeypatch, payload):
    calls = []

    def fake(args, timeout):
        calls.append(args)
        return payload

    monkeypatch.setattr(bilibili, "_bili_json", fake)
    return calls


def test_live_samples_are_not_the_removed_video():
    targets = [a.live_test.get("target") for a in BilibiliChannel.actions if a.live_test]
    assert "BV1GJ411x7h7" not in targets
    assert bilibili._LIVE_SAMPLE_BV in targets


def test_every_action_has_a_live_test():
    assert all(a.live_test for a in BilibiliChannel.actions)


def test_no_write_action_is_exposed():
    names = {a.name for a in BilibiliChannel.actions}
    assert names == {"search", "read", "hot", "subtitle", "users", "user", "user_videos", "rank"}
    assert not names & {"like", "coin", "triple", "dynamic-post", "unfollow"}


@pytest.mark.parametrize("target,expected", [
    ("546195", "546195"),
    ("https://space.bilibili.com/546195?spm_id_from=x", "546195"),
    ("老番茄", "老番茄"),
])
def test_uploader_target(target, expected):
    assert _uploader(target) == expected


def test_uploader_rejects_other_links():
    with pytest.raises(ReachError):
        _uploader("https://www.youtube.com/@someone")


def test_users_search(monkeypatch):
    calls = _capture(monkeypatch, [{"id": "546195", "name": "老番茄", "sign": "hi", "fans": 20878692, "videos": 683}])
    [item] = BilibiliChannel()._cli_users(query="老番茄", limit=1, timeout=5)
    assert calls[0][:4] == ["search", "老番茄", "--type", "user"]
    assert item["url"] == "https://space.bilibili.com/546195"
    assert "20878692" in item["text"]


def test_user_profile(monkeypatch):
    _capture(monkeypatch, {"user": {"id": "2", "name": "碧诗", "level": 6, "sign": "bio"},
                           "relation": {"following": 7, "follower": 1000}})
    [item] = BilibiliChannel()._cli_user(target="https://space.bilibili.com/2", timeout=5)
    assert item["title"] == "碧诗"
    assert item["raw"]["follower"] == 1000
    assert "Followers: 1000" in item["text"]


def test_user_videos(monkeypatch):
    calls = _capture(monkeypatch, [{"bvid": "BV1xx411c7mD", "title": "t", "stats": {"view": 9}}] * 3)
    items = BilibiliChannel()._cli_user_videos(target="2", limit=2, timeout=5)
    assert calls[0] == ["user-videos", "2", "-n", "2"]
    assert len(items) == 2 and items[0]["url"].endswith("BV1xx411c7mD")


def test_rank(monkeypatch):
    calls = _capture(monkeypatch, {"items": [{"bvid": "BV1xx411c7mD", "title": "t"}]})
    [item] = BilibiliChannel()._cli_rank(days=7, limit=1, timeout=5)
    assert calls[0] == ["rank", "--day", "7", "-n", "1"]
    assert item["title"] == "t"


def test_rank_rejects_other_periods(monkeypatch):
    _capture(monkeypatch, {})
    with pytest.raises(ReachError):
        BilibiliChannel()._cli_rank(days=30, limit=1, timeout=5)


def test_412_is_reported_as_platform_block_without_html(monkeypatch):
    import json as _json

    from agent_reach.runtime.run import CommandFailed

    body = _json.dumps({"ok": False, "error": {"code": "network_error",
                        "message": "获取视频列表失败: 网络错误，状态码：412 - <!DOCTYPE html><html>…</html>"}})

    def fail(*a, **k):
        raise CommandFailed("UPSTREAM_BROKEN", "bili exited 1", stderr="", stdout=body)

    monkeypatch.setattr(bilibili, "run_cmd", fail)
    with pytest.raises(ReachError) as exc:
        bilibili._bili_json(["user-videos", "2"], 5)
    assert exc.value.code == "PLATFORM_BLOCKED"
    assert "<" not in exc.value.message
    assert "Wait" in exc.value.hint
