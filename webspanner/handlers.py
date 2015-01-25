import time
import abc
import asyncio
from .request import HttpRequest
from .response import HttpResponse

class BaseServerHandler:
    """
    This class is callable
    The __call__ method will receive a (reader, writer) pair
        StreamReader and StreamWriter

    Then the method will create HttpRequest and HttpRespone objects
    and pass to the next handler
    """
    def __init__(self, handler=None):
        self.handler = handler

    def __call__(self, reader, writer):
        # request_line = yield from reader.readline()
        req = HttpRequest(reader, self.handler)
        if (yield from req.parse()) == False:
            print("empty received")
            writer.close()
            return
        res = HttpResponse(writer, self.handler)
        if self.handler:
            yield from self.handler(req, res)
        else:
            res.status = 404
            res.write("404 Page Not Found\r\n")

        if not req.at_eof():
            req.feed_eof()
        res.write_eof()
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        print('{} [{}] "{} {}" {}'.format(now, self.handler.__class__.__name__,
                req.method, req.path, res.status))

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
