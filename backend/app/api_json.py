"""One bounded, duplicate-free JSON transport contract for HTTP submissions."""

import json


class JsonRequestRejected(ValueError):
    def __init__(self, status, code, message):
        self.status, self.code, self.message = status, code, message
        super().__init__(code)


async def read_json_request(request, *, max_bytes=4096):
    if type(max_bytes) is not int or not 1 <= max_bytes <= 65536:
        raise ValueError('JSON request bound invalid')
    if request.headers.get('content-type', '').split(';', 1)[0].strip().lower() != 'application/json':
        raise JsonRequestRejected(415, 'unsupported_media_type', 'JSON request required')
    raw = bytearray()
    async for chunk in request.stream():
        if len(raw)+len(chunk) > max_bytes:
            raise JsonRequestRejected(413, 'request_too_large', 'Request too large')
        raw.extend(chunk)
    def unique_pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise ValueError('duplicate request key')
            value[key] = item
        return value
    try:
        return json.loads(raw.decode('utf-8'), object_pairs_hook=unique_pairs,
            parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    except (ValueError, UnicodeError, RecursionError):
        raise JsonRequestRejected(422, 'invalid_request', 'Invalid request') from None
