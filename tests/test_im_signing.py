import base64
import json
import unittest

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature

from src.tiktok_bot.im_signing import sign_request


def decode(segment):
    return base64.urlsafe_b64decode(segment + '=' * (-len(segment) % 4))


class SigningTests(unittest.TestCase):
    def test_proof_is_bound_to_request_and_matches_ticket_guard_key(self):
        url = 'https://im-api-sg.tiktok.com/v1/message/send'
        public_key, proof = sign_request(url)
        header, payload, signature = proof.split('.')
        jwk = json.loads(decode(header))['jwk']
        claims = json.loads(decode(payload))
        self.assertEqual(claims['htm'], 'POST')
        self.assertEqual(claims['htu'], url)
        self.assertIsInstance(claims['iat'], int)
        self.assertTrue(claims['jti'])
        point = b'\x04' + decode(jwk['x']) + decode(jwk['y'])
        self.assertEqual(base64.b64decode(public_key), point)
        key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), point)
        raw = decode(signature)
        self.assertEqual(len(raw), 64)
        der = encode_dss_signature(int.from_bytes(raw[:32], 'big'), int.from_bytes(raw[32:], 'big'))
        key.verify(der, f'{header}.{payload}'.encode(), ec.ECDSA(hashes.SHA256()))

    def test_each_proof_has_a_new_key_and_nonce(self):
        first = sign_request('https://im-api-sg.tiktok.com/v1/message/send')
        second = sign_request('https://im-api-sg.tiktok.com/v1/message/send')
        self.assertNotEqual(first[0], second[0])
        self.assertNotEqual(first[1], second[1])
