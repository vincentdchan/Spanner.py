import asyncio

from collections import OrderedDict

_DEFAULT_EXHAUST = 2**16
DELIMITER = b'\r\n'

_FORM_URLENCODED = 'application/x-www-form-urlencoded'

RESPONSES = {x: "{} {}".format(x, y) for x, y in http_responses.items()}


class HttpParser:
    @staticmethod
    @asyncio.coroutine
    def parse(reader):
        l = yield from reader.readline()
        if not l:
            return
        l = l.rstrip(DELIMITER)

        try:
            method, uri, version = (x.decode('ascii') for x in l.split(b' '))
            if version not in ('HTTP/1.1', 'HTTP/1.0'):
                raise ValueError('Unsupported http version {}'.format(version))
        except ValueError:
            raise BadRequestException()

        peer = reader._transport.get_extra_info('peername')
        sslctx = reader._transport.get_extra_info('sslcontext')
        extra = {
            "peername": peer,
            "sslcontext": sslctx,
        }

        request = HttpRequest(method, uri, version, extra)

        while True:
            l = yield from reader.readline()
            if not l:
                return
            if l == DELIMITER:
                break

            l = l.rstrip(DELIMITER)
            if chr(l[0]) not in (' ', '\t'):
                try:
                    name, value = (x.strip().decode('ascii') for x in l.split(b':', 1))
                except ValueError:
                    raise BadRequestException()
                else:
                    request.add_header(name, value)
            else:
                value = l.strip().decode('ascii')
                request.append_to_last_header(value)

        request.body = reader
        yield from request._maybe_init_post()
        return request
