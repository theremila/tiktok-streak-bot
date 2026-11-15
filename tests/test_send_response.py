import unittest
from unittest.mock import Mock

from src.tiktok_bot.messaging import Inbox, _ld, _pb, _str, _vi


class SendResponseTests(unittest.TestCase):
    def test_empty_and_truncated_keys(self):
        self.assertEqual(_pb(b""), {})
        for content in (b"\x80", b"\x80\x80", _vi(3, 0) + b"\x80"):
            with self.subTest(content=content):
                with self.assertRaisesRegex(ValueError, "truncated protobuf key"):
                    _pb(content)

    def send_response(self, content, status=200):
        auth = Mock(user={"id": "owner"})
        auth.cookies = {}
        auth.base.return_value = {"User-Agent": "test"}
        auth.params.return_value = {}
        auth.client.post.return_value = Mock(status_code=status, content=content)
        inbox = Inbox(auth)
        inbox.context = {"wid": "123", "region": "DE"}
        inbox._conv = Mock(return_value={
            "cid": "conversation", "short": 1, "type": 1, "ticket": "ticket",
        })
        result = inbox.send("peer", "test")
        auth.client.post.assert_called_once()
        return result

    def test_explicit_success(self):
        for code in (0, 200):
            with self.subTest(code=code):
                ack = _ld(6, _ld(100, _str(1, "12345")))
                self.assertTrue(self.send_response(_vi(3, code) + ack)["ok"])
                self.assertFalse(self.send_response(_vi(3, code))["ok"])

    def test_omitted_zero_status_requires_matching_envelope(self):
        self.assertTrue(self.send_response(_ld(6, _ld(100, _str(1, "12345"))))["ok"])
        for content in (_vi(1, 100), _vi(1, 203) + _ld(6, b""), _str(4, "OK"),
                        _vi(1, 100) + _ld(6, _ld(100, b""))):
            with self.subTest(content=content):
                self.assertFalse(self.send_response(content)["ok"])

    def test_numeric_message_id_in_fallback_envelope(self):
        result = self.send_response(_ld(8, _ld(100, _vi(1, 12345))))
        self.assertTrue(result["ok"])
        self.assertEqual(result["message_id"], "12345")

    def test_invalid_acknowledgements_are_not_retried_or_accepted(self):
        for content in (b"", b"<html>OK</html>", b"{}", b"\x18", b"\x18\x80",
                        b"\x22\x05OK", b"\x00", b"\x09", _str(3, "200")):
            with self.subTest(content=content):
                result = self.send_response(content)
                self.assertFalse(result["ok"])
                self.assertEqual(result["code"], -7)
                self.assertEqual(result["response_bytes"], len(content))
                self.assertNotIn("test", result["msg"])

    def test_error_status_is_not_overridden_by_ok_text(self):
        self.assertFalse(self.send_response(_vi(3, 2154) + _str(4, "OK"))["ok"])

    def test_http_error_is_not_overridden_by_protocol_success(self):
        self.assertFalse(self.send_response(_vi(3, 0), status=500)["ok"])


if __name__ == "__main__":
    unittest.main()
