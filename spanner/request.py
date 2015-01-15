import asyncio

class HttpRequest:
    def __init__(self, reader, app):
        self.reader = reader
        self._app = app

    @asyncio.coroutine
    def parse(self):
        rl = yield from self.reader.readline()
        request_line = rl.decode('utf-8')
        method, path, proto = request_line.split()
        # print("method:{} path:{} proto:{}".format(method,path,proto))
        path = path.split("?", 1)
        if len(path) > 1:
            qs = path[1]
        path = path[0]
        self.method = method
        self.path = path
        self.proto = proto
        self.qs = ""
        self.headers = {}
        while True:
            l = yield from self.reader.readline()
            # TODO: bytes vs str
            l = l.decode()
            if l == "\r\n":
                break
            k, v = l.split(":", 1)
            self.headers[k] = v.strip()

    def read_form_data(self):
        size = int(self.headers["Content-Length"])
        data = yield from self.reader.read(size)
        form = parse_qs(data.decode())
        self.form = form

    def parse_qs(self):
        form = parse_qs(self.qs)
        self.form = form
