import json
import unittest
from unittest.mock import Mock

import httpx

from src.tiktok_bot.auth import Auth
from src.tiktok_bot.messaging import Inbox, _ld, _one, _pb, _str, _txt, _vi


class ProtocolTests(unittest.TestCase):
    def test_context_inbox_and_signed_send_flow(self):
        sent = []
        cid = '0:1:123:456'

        def respond(request):
            if request.url.path == '/messages':
                context = {'__DEFAULT_SCOPE__': {'webapp.app-context': {'wid': '987', 'region': 'DE'}}}
                return httpx.Response(200, text='<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__">' + json.dumps(context) + '</script>')
            envelope = _pb(request.content)
            self.assertEqual(_txt(_one(envelope, 9)), '987')
            self.assertEqual(_one(envelope, 5), 3)
            self.assertEqual(_one(envelope, 18), 1)
            if request.url.path.endswith('get_by_user_init'):
                entry = _str(1, cid) + _vi(2, 1) + _vi(5, 123456)
                return httpx.Response(200, content=_vi(3, 0) + _ld(6, _ld(203, _ld(1, entry))))
            self.assertEqual(request.url.host, 'im-api-sg.tiktok.com')
            self.assertEqual(request.url.path, '/v1/message/send')
            self.assertIn('ztca-dpop', request.url.params)
            self.assertNotIn('X-Bogus', request.url.params)
            self.assertEqual(_one(envelope, 2), 10009)
            metadata = {_txt(_one(_pb(kv), 1)): _txt(_one(_pb(kv), 2)) for kv in envelope[15]}
            self.assertEqual(metadata['tt-ticket-guard-public-key'], request.headers['tt-ticket-guard-public-key'])
            body = _pb(_one(_pb(_one(envelope, 8)), 100))
            self.assertEqual(_txt(_one(body, 1)), cid)
            self.assertEqual(_one(body, 3), 123456)
            self.assertEqual(json.loads(_one(body, 4)), {'aweType': 0, 'text': 'test'})
            sent.append(request)
            return httpx.Response(200, content=_vi(3, 0) + _ld(6, _ld(100, _str(1, '999'))))

        auth = Auth(cookies={'sessionid': 'test'})
        auth.client.close()
        auth.client = httpx.Client(transport=httpx.MockTransport(respond))
        auth.user = {'id': '456'}
        try:
            result = Inbox(auth).send('123', 'test')
        finally:
            auth.client.close()
        self.assertTrue(result['ok'])
        self.assertEqual(result['message_id'], '999')
        self.assertEqual(len(sent), 1)

    def test_missing_conversation_is_not_fabricated_or_sent(self):
        auth = Mock(user={'id': '456'})
        inbox = Inbox(auth)
        inbox.load = Mock(return_value={})
        result = inbox.send('123', 'test')
        self.assertFalse(result['ok'])
        self.assertEqual(result['code'], -4)
        auth.client.post.assert_not_called()
