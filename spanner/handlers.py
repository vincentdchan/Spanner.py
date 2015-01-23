import time
import abc
import asyncio
from .request import HttpRequest
from .response import HttpResponse

class BaseServerHandler:
    def __init__(self, handler=None):
        self.handler = handler

    def __call__(self, reader, writer):
        # request_line = yield from reader.readline()
        req = HttpRequest(reader, self.handler)
        yield from req.parse()
        res = HttpResponse(writer, self.handler)
#        print("================")
#        print(req, writer)
#        print(req, (method, path, qs, proto), headers)

        # Find which mounted subapp (if any) should handle this request
        # path = req.path
        #
        # app = self.app
        # while True:
        #     found = False
        #     for subapp in app.mounts:
        #         root = subapp.url
        #         print(path, "vs", root)
        #         if path[:len(root)] == root:
        #             app = subapp
        #             found = True
        #             path = path[len(root):]
        #             if not path or path[0] != "/":
        #                 path = "/" + path
        #             break
        #     if not found:
        #         break
        #
        # # We initialize apps on demand, when they really get requests
        # if not app.inited:
        #     app.init()
        #
        # # Find handler to serve this request in app's url_map
        # handler = None
        # for pattern, h, *extra in app.url_map:
        #     if path == pattern:
        #         handler = h
        #         break
        #     elif not isinstance(pattern, str):
        #         # Anything which is non-string assumed to be a ducktype
        #         # pattern matcher, whose .match() method is called. (Note:
        #         # Django uses .search() instead, but .match() is more
        #         # efficient and we're not exactly compatible with Django
        #         # URL matching anyway.)
        #         m = pattern.match(path)
        #         if m:
        #             req.url_match = m
        #             handler = h
        #             break
        if self.handler:
            yield from self.handler(req, res)
        else:
            res.status = 404
            res.write("404 Page Not Found\r\n")
        res.close()
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        print(' {} [{}] "{} {}" {}'.format(now, self.handler.__class__.__name__,
                req.method, req.path, res.status))
        if __debug__ and self.handler.debug > 1:
            print(req, "Finished processing request")

class HttpHandler:
    """
    The Base handler would call a class or a function and pass (res, req) to it.
    The Handler receive (res, req) and do something
    The method should be a couroutine!
    """
    @abc.abstractmethod
    @asyncio.coroutine
    def __call__(self, res, req):
        pass

    @abc.abstractmethod
    @asyncio.coroutine
    def handle_errors(self, code):
        """
        This method should return a method which could receive (res, req) pair
        to deal with errors
        """
        pass
