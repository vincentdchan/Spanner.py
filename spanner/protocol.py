import asyncio
from .log import logger
from spanner.http import HttpParser, HttpWriter
from spanner.exceptions import BadRequestException
from spanner.routing import RoutingHttpProcessor

_DEFAULT_KEEP_ALIVE = 20


class BaseProcessor:
    """Base class responsible for processing http requests"""
    def __init__(self, transport, protocol, reader, writer):
        self.transport = transport
        self.protocol = protocol
        self.reader = reader
        self.writer = writer

    @asyncio.coroutine
    def handle_request(self, request):
        self._transport.write(b'HTTP/1.1 404 NOT FOUND\r\nContent-Length: 13\r\n\r\n404 Not Found')

    def on_timeout(self):
        self._transport.close()

    def connection_lost(self, exc):
        pass


class HttpServerProtocol(asyncio.StreamReaderProtocol):
    def __init__(self, app, *, keep_alive=_DEFAULT_KEEP_ALIVE, loop=None):
        self.app = app
        self.routes = app.routes
        self.reader = asyncio.StreamReader(loop=loop)
        self.keep_alive = keep_alive
        super().__init__(self.reader, None, loop)
        self.h_timeout = None

    def connection_made(self, transport):
        self.transport = transport
        self.reader.set_transport(transport)

        self.writer = HttpWriter(transport, self,
                            self.reader,
                            self.loop)

        self.handler = self._build_handler()

        self.task = asyncio.async(self.handle_client())
        self.task.add_done_callback(self._maybe_log_exception)

        self.reset_timeout()

    def connection_lost(self, exc):
        self.task.cancel()
        self.task = None
        handler = self.handler
        self.writer = None
        self.handler = None
        self.stop_timeout()
        try:
            handler.connection_lost(exc)
        finally:
            super().connection_lost(exc)

    def data_received(self, data):
        self._reset_timeout()
        super().data_received(data)

    @asyncio.coroutine
    def handle_client(self):
        while True:
            try:
                req = yield from HttpParser.parse(self.reader)
            except BadRequestException as e:
                self._bad_request(self.writer, e)
                self.writer.close()
                break
            # connection has been closed
            if req is None:
                break

            try:
                yield from self.handler.handle_request(req)
            finally:
                if self._should_close_conn_immediately(req):
                    if self.writer:
                        self.writer.close()
                else:
                    yield from req.body.read()
                    if self.writer is not None:
                        self.writer.restore()

    def _reset_timeout(self):
        self._stop_timeout()

        self.h_timeout = self._loop.call_later(
            self._keep_alive, self._handle_timeout)

    def _stop_timeout(self):
        if self.h_timeout is not None:
            self.h_timeout.cancel()
            self.h_timeout = None

    def _handle_timeout(self):
        if self._handler.on_timeout():
            self._reset_timeout()

    def _build_handler(self):
        # return self.processor_factory(self._transport, self,
        #                     self._reader,
        #                     self._writer)
        return RoutingHttpProcessor(self.transport, self, self.reader, self.writer)

    def _should_close_conn_immediately(self, req):
        if self._keep_alive < 1:
            return True

        should_close = False
        if req.version.lower() == 'http/1.0':
            should_close = True
        conn_header = req['connection']
        if not conn_header:
            return should_close
        if conn_header == 'keep-alive':
            should_close = False
        elif conn_header == 'close':
            should_close = True
        return should_close

    def _maybe_log_exception(self, task):
        try:
            if not task.cancelled():
                task.result()
        except:
            logger.exception("An exception ocurred while serving request")
            if self._writer is not None:
                self._writer.close()


if __name__ == '__main__':  # pragma: no cover
    loop = asyncio.get_event_loop()
    host, port = 'localhost', 3000
    asyncio.async(loop.create_server(lambda: BaseHttpProtocol(loop=loop),
                host, port))
    loop.run_forever()
