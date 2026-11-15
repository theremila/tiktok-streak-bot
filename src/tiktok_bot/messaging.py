import json
import re
import time
import uuid
import httpx
from .auth import Auth
from .im_signing import sign_request

API = "https://im-api-sg.tiktok.com"
INIT = f"{API}/v2/message/get_by_user_init"
SEND = f"{API}/v1/message/send"
SKIP = ("rate", "limit", "banned", "forbid", "block", "spam", "risk", "verify")
HDR = {
    "Content-Type": "application/x-protobuf",
    "Accept": "application/x-protobuf",
    "Referer": "https://www.tiktok.com/messages",
}

def _vb(n):
    out = bytearray()
    n = int(n) & ((1 << 64) - 1)
    while True:
        b = n & 0x7F
        n >>= 7
        out.append(b | (0x80 if n else 0))
        if not n:
            return bytes(out)

def _tag(f, w):
    return _vb((f << 3) | w)

def _vi(f, v):
    return _tag(f, 0) + _vb(int(v))

def _ld(f, data):
    data = data if isinstance(data, (bytes, bytearray)) else str(data).encode()
    return _tag(f, 2) + _vb(len(data)) + bytes(data)

def _str(f, s):
    return _ld(f, str(s).encode())

def _kv(f, k, v):
    return _ld(f, _str(1, k) + _str(2, v))

def _pb(buf):
    out = {}
    i = 0
    while i < len(buf):
        key = shift = 0
        b = 0x80
        while i < len(buf):
            b = buf[i]
            i += 1
            key |= (b & 0x7F) << shift
            if not b & 0x80:
                break
            shift += 7
            if shift >= 70:
                raise ValueError("oversized protobuf key")
        if b & 0x80:
            raise ValueError("truncated protobuf key")
        f, w = key >> 3, key & 7
        if f == 0:
            raise ValueError("invalid protobuf field")
        if w == 0:
            val = shift = 0
            b = 0x80
            while i < len(buf):
                b = buf[i]
                i += 1
                val |= (b & 0x7F) << shift
                if not b & 0x80:
                    break
                shift += 7
                if shift >= 70:
                    raise ValueError("oversized protobuf value")
            if b & 0x80:
                raise ValueError("truncated protobuf value")
            out.setdefault(f, []).append(val)
        elif w == 2:
            n = shift = 0
            b = 0x80
            while i < len(buf):
                b = buf[i]
                i += 1
                n |= (b & 0x7F) << shift
                if not b & 0x80:
                    break
                shift += 7
                if shift >= 70:
                    raise ValueError("oversized protobuf length")
            if b & 0x80 or n > len(buf) - i:
                raise ValueError("truncated protobuf field")
            out.setdefault(f, []).append(buf[i : i + n])
            i += n
        elif w == 1:
            i += 8
        elif w == 5:
            i += 4
        else:
            raise ValueError("unsupported protobuf wire type")
        if i > len(buf):
            raise ValueError("truncated protobuf fixed field")
    return out

def _one(d, k, default=None):
    vs = d.get(k) or []
    return vs[0] if vs else default

def _txt(v):
    if isinstance(v, (bytes, bytearray)):
        try:
            return v.decode()
        except Exception:
            return ""
    return "" if v is None else str(v)

class Inbox:
    def __init__(self, auth=None):
        self.auth = auth or Auth()
        self.last = {}
        self.convs = {}
        self.context = {}

    def _context(self):
        if self.context:
            return self.context
        response = self.auth.client.get(
            "https://www.tiktok.com/messages?lang=en",
            headers=self.auth.headers({"Accept": "text/html"}),
        )
        response.raise_for_status()
        match = re.search(
            r'<script[^>]+id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>',
            response.text, re.S,
        )
        if not match:
            raise ValueError("messages page context unavailable")
        context = json.loads(match.group(1)).get("__DEFAULT_SCOPE__", {}).get("webapp.app-context", {})
        wid = context.get("wid")
        if not isinstance(wid, str) or not wid.isascii() or not wid.isdigit():
            raise ValueError("messages page device ID unavailable")
        self.context = context
        return context

    def _params(self):
        params = {"aid": "1988", "version_code": "1.0.0",
                  "app_name": "tiktok_web", "device_platform": "web_pc"}
        if self.auth.cookies.get("msToken"):
            params["msToken"] = self.auth.cookies["msToken"]
        return params

    def resolve_username(self, username: str) -> str:
        username = username.removeprefix("@")
        if not re.fullmatch(r"[A-Za-z0-9._]{1,24}", username):
            raise ValueError("invalid username")
        response = self.auth.client.get(f"https://www.tiktok.com/@{username}")
        response.raise_for_status()
        match = re.search(
            r'<script[^>]+id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>',
            response.text, re.S,
        )
        if not match:
            raise ValueError("profile data unavailable")
        profile = json.loads(match.group(1)).get("__DEFAULT_SCOPE__", {}).get(
            "webapp.user-detail", {}
        ).get("userInfo", {}).get("user", {})
        uid = str(profile.get("id") or "")
        if str(profile.get("uniqueId") or "").casefold() != username.casefold() or not uid.isascii() or not uid.isdigit():
            raise ValueError("profile does not match username")
        return uid

    def _pack(self, cmd, field, body, guard=None):
        context = self._context()
        metadata = self.auth.params()
        metadata.pop("X-Bogus", None)
        metadata.pop("msToken", None)
        metadata.update({"channel": "web", "device_id": context["wid"],
                         "region": str(context.get("region") or ""),
                         "priority_region": str(context.get("region") or ""),
                         "referer": "https://www.tiktok.com/messages",
                         "user_is_login": "true", "from_appID": "1988",
                         "user_agent": self.auth.base()["User-Agent"]})
        if self.auth.cookies.get("msToken"):
            metadata["Web-Sdk-Ms-Token"] = self.auth.cookies["msToken"]
        if guard:
            metadata.update(guard)
        group = cmd == 100 and _one(_pb(body), 2) == 2
        return b"".join(
            [
                _vi(1, cmd),
                _vi(2, (10014 if group else 10009) if cmd == 100 else 10002),
                _str(3, "1.6.0"),
                _str(4, ""),
                _vi(5, 3),
                _vi(6, int(group)),
                _str(7, ""),
                _ld(8, _ld(field, body)),
                _str(9, context["wid"]),
                _str(11, "web"),
                *(_kv(15, k, v) for k, v in metadata.items()),
                _vi(18, 1),
            ]
        )

    def load(self, force=False):
        if self.convs and not force:
            return self.convs
        body = _vi(1, 0)
        r = self.auth.client.post(
            INIT,
            params=self._params(),
            content=self._pack(203, 203, body),
            headers=self.auth.headers(HDR),
        )
        if r.status_code != 200 or not r.content:
            return self.convs
        env = _pb(r.content)
        if _one(env, 3) not in (0, None) and _txt(_one(env, 4)) != "OK":
            return self.convs
        inner = _pb(_one(_pb(_one(env, 6, b"") or b""), 203, b"") or b"")
        out = {}
        for field in (2, 1):
            for chunk in inner.get(field) or []:
                if not isinstance(chunk, (bytes, bytearray)):
                    continue
                c = _pb(chunk)
                cid = _txt(_one(c, 1, b""))
                if not cid or cid in out:
                    continue
                out[cid] = {
                    "cid": cid,
                    "short": int(_one(c, 2 if field == 2 else 5) or 0),
                    "type": int(_one(c, 3 if field == 2 else 2) or 1),
                    "ticket": "deprecated",
                }
        self.convs = out
        return out

    def _conv(self, peer, cid="", ctype=1):
        peer = str(peer or "")
        cid = str(cid or "")
        ctype = int(ctype or 1)
        my = str(self.auth.user.get("id") or "")
        if ctype == 2 and cid:
            self.load()
            if cid in self.convs:
                return self.convs[cid]
            return None
        self.load()
        want = [x for x in (cid, f"0:1:{peer}:{my}", f"0:1:{my}:{peer}") if x]
        for key in want:
            if key in self.convs:
                return self.convs[key]
        self.load(force=True)
        for key in want:
            if key in self.convs:
                return self.convs[key]
        return None

    def send(self, peer, text, conversation_id="", conv_type=1):
        peer = str(peer or "")
        text = str(text or "").strip()
        if not text:
            return {"ok": False, "code": -2, "msg": "empty", "skip": False}
        if not self.auth.user.get("id") and not self.auth.login():
            return {"ok": False, "code": -3, "msg": "login", "skip": False}
        ctype = int(conv_type or 1)
        cid = str(conversation_id or "")
        if ctype == 2 and not cid and peer.isdigit():
            cid = peer
        info = self._conv(peer, cid, ctype)
        if not info:
            return {"ok": False, "code": -4, "msg": "no conv", "skip": False}
        mid = str(uuid.uuid4())
        content = json.dumps(
            {"aweType": 0, "text": text},
            separators=(",", ":"),
        )
        body = b"".join(
            [
                _str(1, info["cid"]),
                _vi(2, info["type"]),
                _vi(3, info["short"]),
                _str(4, content),
                _kv(5, "s:client_message_id", mid),
                _kv(5, "s:mentioned_users", ""),
                _vi(6, 7),
                _str(7, info["ticket"]),
                _str(8, mid),
            ]
        )
        public_key, proof = sign_request(SEND)
        guard = {"tt-ticket-guard-public-key": public_key,
                 "tt-ticket-guard-client-data": "",
                 "tt-ticket-guard-version": "2",
                 "tt-ticket-guard-iteration-version": "0",
                 "tt-ticket-guard-web-version": "1"}
        params = self._params()
        params.update({"ztca-version": "1", "ztca-dpop": proof})
        try:
            r = self.auth.client.post(
                SEND,
                params=params,
                content=self._pack(100, 100, body, guard),
                headers=self.auth.headers({**HDR, **guard}),
                follow_redirects=False,
            )
        except httpx.HTTPError:
            out = {"ok": False, "code": -1, "msg": "network error; delivery unknown", "skip": False}
            self.last[peer or cid] = {"at": int(time.time()), **out, "text": text}
            return out
        if r.status_code in (401, 403):
            out = {"ok": False, "code": -3, "msg": "login", "skip": False}
            self.last[peer or cid] = {"at": int(time.time()), **out, "text": text}
            return out
        response_details = {
            "http_status": r.status_code,
            "response_bytes": len(r.content),
        }
        try:
            if not r.content:
                raise ValueError("empty response")
            env = _pb(r.content)
            raw = _one(env, 3)
            message_id = ""
            for field in (6, 8):
                payload = _one(env, field, b"")
                if not isinstance(payload, bytes):
                    continue
                response_body = _one(_pb(payload), 100, b"")
                if not isinstance(response_body, bytes):
                    continue
                value = _one(_pb(response_body), 1)
                candidate = _txt(value)
                if candidate.isascii() and candidate.isdigit() and int(candidate) > 0:
                    message_id = candidate
                    break
            if raw is None and message_id:
                raw = 0
            if type(raw) is not int:
                raise ValueError("missing or invalid IM status")
            code = raw
        except (TypeError, ValueError):
            out = {
                "ok": False, "code": -7, "msg": "API response invalid",
                "skip": False,
                "reason": "empty_response" if not r.content else "invalid_acknowledgement",
                **response_details,
            }
            self.last[peer or cid] = {"at": int(time.time()), **out, "text": text}
            return out
        msg = _txt(_one(env, 4)) or f"http {r.status_code}"
        skip = any(x in msg.lower() for x in SKIP) or code in (2154, 3002325, 3002282)
        out = {
            "ok": r.status_code == 200 and code in (0, 200) and bool(message_id) and not skip,
            "code": code, "msg": msg, "skip": skip, **response_details,
            "message_id": message_id,
            "reason": "acknowledged" if message_id else "missing_message_id",
        }
        self.last[peer or cid] = {"at": int(time.time()), **out, "text": text}
        return out
