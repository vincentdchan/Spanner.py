import time
import re
import errno
import asyncio
import json

from routes import Mapper
from .utils import parse_qs
from .response import HttpResponse
from .handlers import HttpHandler, BaseServerHandler


def get_mime_type(fname):
    # Provide minimal detection if important file
    # types to keep browsers happy
    if fname.endswith(".html"):
        return "text/html"
    if fname.endswith(".css"):
        return "text/css"
    return "text/plain"


def sendfd(writer, f):
    while True:
        buf = f.read(512)
        if not buf:
            break
        yield from writer.write(buf)


def sendfile(writer, fname, content_type=None):
    if not content_type:
        content_type = get_mime_type(fname)
    try:
        with open(fname, "rb") as f:
            yield from start_response(writer, content_type)
            yield from sendfd(writer, f)
    except OSError as e:
        if e.args[0] == errno.ENOENT:
            yield from start_response(writer, "text/plain", "404")
        else:
            raise


def jsonify(writer, dict):
    yield from start_response(writer, "application/json")
    yield from writer.write(json.dumps(dict))


def static_handler(req, res):
    path = req.match['filename']
    yield from sendfile()


class StaticHandler(HttpHandler):

    def __init__(self, dir="./static/"):
        self.dir = dir

    def __call__(self, req, res):
        path = req.match['filename']
        content_type = get_mime_type(path)
        try:
            with open(fname, "rb") as f:
                res.headers['content_type'] = content_type
                res.send_headers()
                while True:
                    buf = f.read(512)
                    if not buf:
                        break
                    yield from asyncio.sleep(0)
                    res.write(buf)
        except OSError as e:
            if e.args[0] == errno.ENOENT:
                res.status = 404
                res.headers['content_type'] = "text/plain"
                res.write("Transport failure\r\n")
            else:
                raise


@asyncio.coroutine
def default_handler_404(req, res):
    res.status = 404
    res.write("404 Page Not Found\r\n")


class Spanner(HttpHandler):

    def __init__(self, routes=None, static_dir="./static/",
                 static_url="/static/{filename:.*?}"):
        if routes:
            self.routes = routes
        else:
            self.routes = Mapper()
        # if static:
        #     self.url_map.append((re.compile("^/static(/.+)"),
        #         lambda req, resp: (yield from sendfile(resp, static + req.url
        self._mounts = Mapper()
        self._middlewares = []
        self._errors_handler = {
            "404": default_handler_404,
        }
        self.inited = False
        self.routes.connect(
            None, static_url, _controller=StaticHandler(static_dir))

    @asyncio.coroutine
    def __call__(self, req, res):
        """
        The sub class of HttpHandler should be a function
        or a class callable and receive (req, res) pair
        while request come.
        """
        path = req.path
        match = self.routes.match(path)
        if not match:
            yield from res.abort(req, 404)
            return
        controller = match.pop("_controller")
        # TODO: check the conditions
        conditions = match.pop("_conditions")
        # if "method" in conditions.keys():
        #     if req.method not in conditions['method']:
        #         res.abort(req, 404)
        #         return
        req.params = match
        handle = Next(controller, self._middlewares.copy(), req, res)
        try:
            yield from handle()
        except Exception as e:
            import traceback
            err_info = traceback.format_exc()
            print(err_info)
            res.status = 500
            if self.debug:
                res.write(err_info.replace("\n", "<br>\n"))
            else:
                res.write("An error is occured on the server")
            res.close()

    def route(self, url, **kwargs):
        def route(f):
            self.add_url_rule(url, f, **kwargs)
            return f
        return route

    def add_url_rule(self, url, func, **kwargs):
        if 'method' not in kwargs:
            kwargs['method'] = ['GET', 'POST']
        else:
            kwargs['method'] = [v.upper() for v in kwargs['method']]
        func = asyncio.coroutine(func)
        self.routes.connect(None, url, _controller=func, _conditions=kwargs)

    def use(self, func):
        """
        The use method if design for using middlewares.
        Usage Example:
        @app.use
        def cookie_parse(req, res, handle):
            req.cookie = parseCookie(req)
            yield from handle()
            print("I am using a middleware")
        """
        func = asyncio.coroutine(func)   # make the function a coroutine
        self._middlewares.append(func)

    def handle_errors(self, code):
        def wrapper(f):
            func = asyncio.coroutine(f)
            self._errors_handler.__setitem__(str(code), func)
        return wapper

    def get_errors_handler(self, code):
        try:
            handler = self._errors_handler[str(code)]
        except:
            handler = None
        return handler

    def init(self):
        """Initialize a web application. This is for overriding by subclasses.
        This is good place to connect to/initialize a database, for example."""
        self.inited = True

    def run(self, host="127.0.0.1", port=8080, debug=False):
        self.debug = debug
        self.init()
        loop = asyncio.get_event_loop()
        self.loop = loop
        print("* Running on http://%s:%s/" % (host, port))
        # loop.create_task(asyncio.start_server(self._handle, host, port))
        loop.create_task(
            asyncio.start_server(BaseServerHandler(self),
                                 host, port, loop=loop))
        loop.run_forever()
        loop.close()


class Context(object):

    """
    docstring for Context
    Context is an object contain both request and response

    """

    def __init__(self, req, res):
        super(Context, self).__init__()
        self.req = req
        self.res = res

    # Request method

    def get_data(self):
        pass

    def get_json(self):
        pass

    # Response method

    def write(self, chunk):
        self.res.write(chunk)

    def send_html(self, text):
        pass

    def send_file(self, file):
        pass

    def jsonify(self, json_dict):
        pass

    def render_template(self, name, *args, **kwargs):
        """
        Usage:

        req.render_template("index.html",{
            "name": "Chen",
        })
        """
        pass

    def close(self):
        self.res.close()


class Next:

    """
    This class is designed to deal with the middlewares
    Usage Example:
    @app.use
    def cookie_parse(req, res, handle):
        req.cookie = parseCookie(req)
        yield from handle()
        print("I am using a middleware")
    """

    def __init__(self, handler, middlewares, request, response):
        self.handler = handler
        self.middlewares = middlewares
        self.req = request
        self.res = response

    @asyncio.coroutine
    def __call__(self):
        if len(self.middlewares) > 0:
            middleware = self.middlewares.pop(0)    # pop in order
            yield from middleware(self.req, self.res, self)
        else:
            yield from self.handler(self.req, self.res)
