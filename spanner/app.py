import asyncio
from .protocol import BaseHttpProtocol
from .response import HttpResponse
from .handlers import (
    CallbackRouteHandler,
    WebSocketHandler,
)
from .routing import (
    CallbackRoute,
    RoutingHttpProcessor,
    Mapper,
    # WebSocketRoute,
)
from .sockjs import SockJsRoute
from .routing import RequestSpec

__all__ = ["Spanner"]


class CallableDict(dict):
    "Dirty hack, so that routes does not stringify the dict"
    def __call__(self):
        pass


class Spanner:
    def __init__(self, name):
        self._name = name
        self._routes = Mapper()
        self._before_request = []
        self._after_request = []

    @asyncio.coroutine
    def _handle_404(self, request, start_response):
        data = 'Not found'.encode('utf-8')
        headers = (
            (b'Content-Type', b'text/plain'),
            (b'Content-Length', str(len(data)).encode('utf-8'))
        )
        start_response(b'404 Not Found', headers)
        return [data]

    def route(self, path, **condition):
    """
    The route method is the key to Spanner
    The route method is a wrapper of a function to an Spanner
    Usage:
        @app.route('/')
        def index(req, res):
            res.send("Hello world!")
    """
        # spec = RequestSpec(path, methods)
        def wrap(func):
            self._routes.connect(path, handler=func, conditions=conditions)
            return func

        return wrap

    def use(self, name=None, autoload=False):
    """
    Load a middleware like one in express.js
    Usage:
        @app.use('load', autoload=False)
        def load(req, res):
            req.name = "Chan"

        @app.route('/', require=['load'])
        def index(req, res):
            rq.send(req.name)   # send "Chan"
    """
        def wrap(func):
            pass

        return wrap

    def before_request(self, autoload=True)
        def wrap(func):
            self._before_request.append(func)
            return func

        return wrap

    def after_request(self, autoload=True)
        def wrap(func):
            self._before_request.append(func)
            return func

        return wrap

    def endpoint(self, *, path, with_sockjs=True):
        spec = RequestSpec(path)

        def wrap(cls):
            if with_sockjs:
                self._routes.append(SockJsRoute(spec, cls))
            else:
                self._routes.append(WebSocketRoute(spec, cls))
            return cls

        return wrap

    def run(self, *, host='0.0.0.0', port=8000, loop=None):
        if loop is None:
            loop = asyncio.get_event_loop()

        def processor_factory(transport, protocol, reader, writer):
            return RoutingHttpProcessor(transport, protocol, reader, writer, routes=self._routes)
        asyncio.async(loop.create_server(lambda: BaseHttpProtocol(processor_factory, loop=loop),
                    host, port))
        print("Listening on http://{0}:{1}".format(host, port))
        loop.run_forever()

    @staticmethod
    def _decorate_callback(callback):
        @asyncio.coroutine
        def handle_normal(request, start_response, **kwargs):

            response = HttpResponse()
            # yield from before_request
            yield from asyncio.coroutine(callback)(request, response, **kwargs)
            # yield from after_request

            # if isinstance(data, HttpResponse):
            #     response = data
            # else:
            #     response = HttpResponse(data)

            return response(start_response)
        return handle_normal
