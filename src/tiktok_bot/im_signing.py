"""Request-bound IM proofs; private keys exist only for the current request."""

import base64
import json
import secrets
import time

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature


def _b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b'=').decode('ascii')


def sign_request(url: str) -> tuple[str, str]:
    key = ec.generate_private_key(ec.SECP256R1())
    public = key.public_key()
    numbers = public.public_numbers()
    header = {
        'alg': 'ES256', 'typ': 'dpop+jwt',
        'jwk': {'kty': 'EC', 'crv': 'P-256',
                'x': _b64url(numbers.x.to_bytes(32, 'big')),
                'y': _b64url(numbers.y.to_bytes(32, 'big'))},
    }
    payload = {'jti': secrets.token_urlsafe(32), 'htm': 'POST',
               'htu': url, 'iat': int(time.time())}
    segments = [_b64url(json.dumps(item, separators=(',', ':')).encode())
                for item in (header, payload)]
    signing_input = '.'.join(segments)
    signature = key.sign(signing_input.encode('ascii'), ec.ECDSA(hashes.SHA256()))
    r, s = decode_dss_signature(signature)
    proof = signing_input + '.' + _b64url(r.to_bytes(32, 'big') + s.to_bytes(32, 'big'))
    point = public.public_bytes(serialization.Encoding.X962,
                               serialization.PublicFormat.UncompressedPoint)
    return base64.b64encode(point).decode('ascii'), proof
