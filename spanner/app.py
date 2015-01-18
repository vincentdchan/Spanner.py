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

def start_response(writer, content_type="text/html", status="200"):
    # yield from writer.write(("HTTP/1.0 %s NA\r\n" % status).encode())
    # yield from writer.write(("Content-Type: %s\r\n" % content_type).encode())
    # yield from writer.write("\r\n".encode())
    writer.write(("HTTP/1.0 %s NA\r\n" % status).encode())
    writer.write(("Content-Type: %s\r\n" % content_type).encode())
    writer.write("\r\n".encode())

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
                    res.write(buf)
        except OSError as e:
            if e.args[0] == errno.ENOENT:
                res.status = 404
                res.headers['content_type'] = "text/plain"
                res.write("Transport failure\r\n")
            else:
                raise

def default_handler_404(req, res):
    res.status = 404
    res.write("404 Page Not Found\r\n")

class Spanner(HttpHandler):

    def __init__(self, routes=None, static_dir="./static/",
                            static_url="/static/{filename:.*?}"):
        if routes:
            self._routes = routes
        else:
            self._routes = Mapper()
        # if static:
        #     self.url_map.append((re.compile("^/static(/.+)"),
        #         lambda req, resp: (yield from sendfile(resp, static + req.url_match.group(1)))))
        self._mounts = Mapper()
        self._middlewares = []
        self._errors_handler = {
            "404": default_handler_404
        }
        self.inited = False
        self._routes.connect(None, static_url, _controller=StaticHandler(static_dir))

    @asyncio.coroutine
    def __call__(self, req, res):
        """
        The sub class of HttpHandler should be a function or a class callable and
        receive (req, res) pair while request come.
        """
        path = req.path
        match = self._routes.match(path)
        if not match:
            res.abort(req, 404)
            return
        controller = match.pop("_controller")
        # TODO: check the conditions
        # conditions = json.loads(match.pop("_conditions"))
        # if "method" in conditions.keys():
        #     if req.method not in conditions['method']:
        #         res.abort(req, 404)
        #         return
        req.vars = match
        yield from controller(req, res)


    # def mount(self, url, app):
    #     "Mount a sub-app at the url of current app."
    #     # Inspired by Bottle. It might seem that dispatching to
    #     # subapps would rather be handled by normal routes, but
    #     # arguably, that's less efficient. Taking into account
    #     # that paradigmatically there's difference between handing
    #     # an action and delegating responisibilities to another
    #     # app, Bottle's way was followed.
    #     app.url = url
    #     self._mounts.connect(None, url, controller=app)

    def route(self, url, **kwargs):
        def route(f):
            self.add_url_rule(url, f, **kwargs)
            return f
        return route

    def add_url_rule(self, url, func, **kwargs):
        if 'method' not in kwargs:
            kwargs['method'] = ['GET', 'POST']
        else:
            kwargs['method'] = [ v.upper() for v in kwargs['method'] ]
        func = asyncio.coroutine(func)
        self._routes.connect(None, url, _controller=func, _conditions=kwargs)

    def use(func=None):
        """
        The use method if design for using middlewares.
        Usage Example:
        @app.use
        def cookie_parse(req, res, handler):
            req.cookie = parseCookie(req)
            yield from handler(res,req)
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

    # def render_template(self, writer, tmpl_name, args=()):
    #     tmpl = self.template_loader.load(tmpl_name)
    #     for s in tmpl(*args):
    #         yield from writer.write(s)
    #

    def init(self):
        """Initialize a web application. This is for overriding by subclasses.
        This is good place to connect to/initialize a database, for example."""
        self.inited = True

    def run(self, host="127.0.0.1", port=8081, debug=False, lazy_init=False):
        self.debug = int(debug)
        self.init()
        # if not lazy_init:
        #     for app in self.mounts:
        #         app.init()
        loop = asyncio.get_event_loop()
        print("* Running on http://%s:%s/" % (host, port))
        # loop.create_task(asyncio.start_server(self._handle, host, port))
        loop.create_task(asyncio.start_server(BaseServerHandler(self), host, port, loop=loop))
        loop.run_forever()
        loop.close()
