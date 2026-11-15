import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, call, patch

from src.tiktok_bot.bot import StreakBot
from src.tiktok_bot.config import BotConfig
from src.tiktok_bot.messaging import Inbox, _ld, _str, _vi


class TargetTests(unittest.TestCase):
    def test_configured_targets_ignore_streak_status(self):
        auth = Mock(user={"username": "owner"})
        bot = StreakBot(BotConfig(target_users=("alice", "bob"), message_to_send="test"), auth)
        bot.inbox = Mock()
        bot.inbox.resolve_username.side_effect = ["123", "456"]
        bot.inbox.send.return_value = {"ok": True}
        bot.streaks = Mock()
        with patch("src.tiktok_bot.bot.time.sleep"):
            self.assertEqual(bot.run_oneshot(note=Mock()), 2)
        self.assertEqual(bot.inbox.send.call_args_list, [call("123", "test"), call("456", "test")])
        bot.streaks.fetch.assert_not_called()

    def test_unresolved_target_is_not_sent(self):
        bot = StreakBot(BotConfig(target_users=("alice",)), Mock(user={"username": "owner"}))
        bot.inbox = Mock()
        bot.inbox.resolve_username.side_effect = ValueError("profile mismatch")
        with patch("src.tiktok_bot.bot.time.sleep"):
            self.assertEqual(bot.run_oneshot(note=Mock()), 0)
        bot.inbox.send.assert_not_called()

    def test_platform_restriction_stops_dispatch(self):
        bot = StreakBot(BotConfig(target_users=("alice", "bob")), Mock(user={"username": "owner"}))
        bot.inbox = Mock()
        bot.inbox.resolve_username.return_value = "123"
        bot.inbox.send.return_value = {"ok": False, "skip": True, "code": 2154}
        with patch("src.tiktok_bot.bot.time.sleep"):
            self.assertEqual(bot.run_oneshot(note=Mock()), 0)
        self.assertEqual(bot.inbox.send.call_count, 1)

    def profile(self, username, uid):
        payload = {"__DEFAULT_SCOPE__": {"webapp.user-detail": {"userInfo": {"user": {"uniqueId": username, "id": uid}}}}}
        response = Mock(text='<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__">' + json.dumps(payload) + '</script>')
        return Inbox(SimpleNamespace(client=Mock(get=Mock(return_value=response))))

    def test_exact_username_resolution(self):
        self.assertEqual(self.profile("Alice", "123").resolve_username("@alice"), "123")

    def test_mismatched_profile_rejected(self):
        with self.assertRaises(ValueError):
            self.profile("other", "123").resolve_username("alice")

    def test_invalid_username_rejected_without_request(self):
        inbox = self.profile("alice", "123")
        with self.assertRaises(ValueError):
            inbox.resolve_username("../alice")
        inbox.auth.client.get.assert_not_called()

    def test_protobuf_http_success_code_is_accepted(self):
        response = Mock(status_code=200, content=_vi(3, 200) + _ld(6, _ld(100, _str(1, "12345"))))
        auth = Mock(user={"id": "owner"})
        auth.cookies = {}
        auth.base.return_value = {"User-Agent": "test"}
        auth.params.return_value = {}
        auth.client.post.return_value = response
        inbox = Inbox(auth)
        inbox.context = {"wid": "123", "region": "DE"}
        inbox._conv = Mock(return_value={"cid": "conversation", "short": 0, "type": 1, "ticket": "ticket"})

        result = inbox.send("peer", "test")

        self.assertTrue(result["ok"])
        self.assertEqual(result["code"], 200)


if __name__ == "__main__":
    unittest.main()
