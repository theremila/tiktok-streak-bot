import unittest
from unittest.mock import Mock

from src.tiktok_bot.messaging import Inbox, _ld, _str, _vi


def conversation(cid, conv_type=1, short=0):
    return _ld(2, _str(1, cid) + _vi(2, short) + _vi(3, conv_type))


def init_page(conversations, next_cursor, has_more):
    inner = b"".join(conversations) + _vi(4, next_cursor) + _vi(5, int(has_more))
    return Mock(status_code=200, content=_vi(3, 0) + _ld(6, _ld(203, inner)))


class ConversationPagingTests(unittest.TestCase):
    def inbox(self, *pages):
        auth = Mock(user={"id": "owner"})
        auth.cookies = {}
        auth.base.return_value = {"User-Agent": "test"}
        auth.params.return_value = {}
        auth.client.post.side_effect = list(pages)
        inbox = Inbox(auth)
        inbox.context = {"wid": "123", "region": "US"}
        return inbox

    def test_load_follows_cursor_until_has_more_is_false(self):
        inbox = self.inbox(
            init_page([conversation("0:1:owner:a"), conversation("0:1:owner:b")], 10, True),
            init_page([conversation("7000000000000000001", conv_type=2)], 11, False),
        )

        convs = inbox.load()

        self.assertEqual(set(convs), {"0:1:owner:a", "0:1:owner:b", "7000000000000000001"})
        self.assertEqual(convs["7000000000000000001"]["type"], 2)
        self.assertEqual(inbox.auth.client.post.call_count, 2)
        second_request = inbox.auth.client.post.call_args_list[1].kwargs["content"]
        self.assertIn(_ld(8, _ld(203, _vi(1, 10))), second_request)

    def test_group_on_later_page_is_resolved(self):
        inbox = self.inbox(
            init_page([conversation("0:1:owner:a")], 10, True),
            init_page([conversation("7000000000000000001", conv_type=2, short=42)], 11, False),
        )

        info = inbox._conv("", "7000000000000000001", 2)

        self.assertEqual(info["cid"], "7000000000000000001")
        self.assertEqual(info["short"], 42)

    def test_load_stops_when_cursor_does_not_advance(self):
        inbox = self.inbox(
            init_page([conversation("0:1:owner:a")], 0, True),
        )

        self.assertEqual(set(inbox.load()), {"0:1:owner:a"})
        self.assertEqual(inbox.auth.client.post.call_count, 1)


if __name__ == "__main__":
    unittest.main()
