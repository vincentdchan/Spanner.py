import time
import re
import errno
import asyncio
# import utemplate.source

from .utils import parse_qs
from .response import HttpResponse
from .handlers import BaseServerHandler


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
    import ujson
    yield from start_response(writer, "application/json")
    yield from writer.write(ujson.dumps(dict))

def start_response(writer, content_type="text/html", status="200"):
    # yield from writer.write(("HTTP/1.0 %s NA\r\n" % status).encode())
    # yield from writer.write(("Content-Type: %s\r\n" % content_type).encode())
    # yield from writer.write("\r\n".encode())
    writer.write(("HTTP/1.0 %s NA\r\n" % status).encode())
    writer.write(("Content-Type: %s\r\n" % content_type).encode())
    writer.write("\r\n".encode())


class Spanner:

    def __init__(self, routes=None, static="static"):
        if routes:
            self.url_map = routes
        else:
            self.url_map = []
        if static:
            self.url_map.append((re.compile("^/static(/.+)"),
                lambda req, resp: (yield from sendfile(resp, static + req.url_match.group(1)))))
        self.mounts = []
        self.inited = False
        # self.template_loader = utemplate.source.Loader("templates")

    def mount(self, url, app):
        "Mount a sub-app at the url of current app."
        # Inspired by Bottle. It might seem that dispatching to
        # subapps would rather be handled by normal routes, but
        # arguably, that's less efficient. Taking into account
        # that paradigmatically there's difference between handing
        # an action and delegating responisibilities to another
        # app, Bottle's way was followed.
        app.url = url
        self.mounts.append(app)

    def route(self, url, **kwargs):
        def _route(f):
            self.add_url_rule(url, f, **kwargs)
            # self.url_map.append((url, f, kwargs))
            return f
        return _route

    def add_url_rule(self, url, func, **kwargs):
        # Note: this method skips Flask's "endpoint" argument,
        # because it's alleged bloat.
        func = asyncio.coroutine(func)
        self.url_map.append((url, func, kwargs))

    # def render_template(self, writer, tmpl_name, args=()):
    #     tmpl = self.template_loader.load(tmpl_name)
    #     for s in tmpl(*args):
    #         yield from writer.write(s)
    #
    # def render_str(self, tmpl_name, args=()):
    #     #TODO: bloat
    #     tmpl = self.template_loader.load(tmpl_name)
    #     return ''.join(tmpl(*args))

    def init(self):
        """Initialize a web application. This is for overriding by subclasses.
        This is good place to connect to/initialize a database, for example."""
        self.inited = True

    def run(self, host="127.0.0.1", port=8081, debug=False, lazy_init=False):
        self.debug = int(debug)
        self.init()
        if not lazy_init:
            for app in self.mounts:
                app.init()
        loop = asyncio.get_event_loop()
        print("* Running on http://%s:%s/" % (host, port))
        # loop.create_task(asyncio.start_server(self._handle, host, port))
        loop.create_task(asyncio.start_server(BaseServerHandler(self), host, port, loop=loop))
        loop.run_forever()
        loop.close()
