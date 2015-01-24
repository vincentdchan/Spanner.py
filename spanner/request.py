import asyncio
import json
from .utils import MultiDict

class HttpRequest:
    def __init__(self, reader, app):
        self.reader = reader
        self._app = app
        self._read_bytes = None

    @asyncio.coroutine
    def parse(self):
        rl = yield from self.reader.readline()
        request_line = rl.decode('utf-8')
        if rl == bytes():
            # if EOF is received
            # rl will be an empty bytes object
            print("empty begin")
            while True:
                r = yield from self.reader.readline()
                if r == bytes():
                    print("still empty")
                else:
                    print(r.decode())
            return False
        method, path, proto = request_line.split()
        # print("method:{} path:{} proto:{}".format(method,path,proto))
        path = path.split("?", 1)
        if len(path) > 1:
            qs = path[1]
        path = path[0]
        self.method = method
        self.path = path
        self.proto = proto
        self.version = proto.split('/')[-1]
        self.qs = ""
        self.headers = MultiDict()
        while True:
            l = yield from self.reader.readline()
            # TODO: bytes vs str
            l = l.decode()
            if l == "\r\n":
                break
            k, v = l.split(":", 1)
            self.headers.add(k, v.strip())

    def feed_eof(self):
        return self.reader.feed_eof()

    def at_eof(self):
        """Return True if the buffer is empty and feed_eof() was called."""
        return self.reader.at_eof()

    @asyncio.coroutine
    def read(self, n=-1):
        """Read request body if present.
        Returns bytes object with full request content.
        """
        if self._read_bytes is None:
            body = bytearray()
            while True:
                chunk = yield from self.reader.read(n)
                body.extend(chunk)
                if chunk == bytes():
                    break
            self._read_bytes = bytes(body)
        return self._read_bytes

    @asyncio.coroutine
    def text(self):
        """Return BODY as text using encoding from .charset."""
        bytes_body = yield from self.read()
        encoding = self.charset or 'utf-8'
        return bytes_body.decode(encoding)

    @asyncio.coroutine
    def json(self):
        """Return BODY as JSON."""
        body = yield from self.text()
        return json.loads(body)

    # def read_form_data(self):
    #     size = int(self.headers["Content-Length"])
    #     data = yield from self.reader.read(size)
    #     form = parse_qs(data.decode())
    #     self.form = form
    #
    # def parse_qs(self):
    #     form = parse_qs(self.qs)
    #     self.form = form
