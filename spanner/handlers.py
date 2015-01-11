import time
from .request import HttpRequest
from .response import HttpResponse

class BaseServerHandler:
    def __init__(self, app):
        self.app = app

    def __call__(self, reader, writer):
        request_line = yield from reader.readline()
        req = HttpRequest()
        res = HttpResponse(writer)
        # TODO: bytes vs str
        request_line = request_line.decode()
        method, path, proto = request_line.split()
        print('%.3f %s %s "%s %s"' % (time.time(), req, writer, method, path))
        path = path.split("?", 1)
        qs = ""
        if len(path) > 1:
            qs = path[1]
        path = path[0]
        headers = {}
        while True:
            l = yield from reader.readline()
            # TODO: bytes vs str
            l = l.decode()
            if l == "\r\n":
                break
            k, v = l.split(":", 1)
            headers[k] = v.strip()
#        print("================")
#        print(req, writer)
#        print(req, (method, path, qs, proto), headers)

        # Find which mounted subapp (if any) should handle this request
        app = self.app
        while True:
            found = False
            for subapp in app.mounts:
                root = subapp.url
                print(path, "vs", root)
                if path[:len(root)] == root:
                    app = subapp
                    found = True
                    path = path[len(root):]
                    if not path or path[0] != "/":
                        path = "/" + path
                    break
            if not found:
                break

        # We initialize apps on demand, when they really get requests
        if not app.inited:
            app.init()

        # Find handler to serve this request in app's url_map
        handler = None
        for pattern, h, *extra in app.url_map:
            if path == pattern:
                handler = h
                break
            elif not isinstance(pattern, str):
                # Anything which is non-string assumed to be a ducktype
                # pattern matcher, whose .match() method is called. (Note:
                # Django uses .search() instead, but .match() is more
                # efficient and we're not exactly compatible with Django
                # URL matching anyway.)
                m = pattern.match(path)
                if m:
                    req.url_match = m
                    handler = h
                    break
        if handler:
            print("Handler: %s" % handler)
            req.method = method
            req.path = path
            req.qs = qs
            req.headers = headers
            req.reader = reader
            yield from handler(req, res)
        else:
            res.status = 404
            res.write("404\r\n")
        #print(req, "After response write")
        # yield from writer.close()
        writer.close()
        if __debug__ and self.app.debug > 1:
            print(req, "Finished processing request")
