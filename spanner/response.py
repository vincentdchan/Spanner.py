import time
from http.cookies import SimpleCookie
from email.utils import formatdate
from http.server import BaseHTTPRequestHandler

STATUS_MAP = BaseHTTPRequestHandler.responses


def status_line(status):
    line = STATUS_MAP[status][0]
    return "{} {}".format(status, line).encode('ascii')


class HttpResponse:
    def __init__(self, writer, status=200, content_type='text/html'):
        self.status = int(status)
        self.cookies = SimpleCookie()
        self.writer = writer
        self.headers = [
            ('Content-Encoding', 'UTF-8'),
            ('Content-Type', content_type),
            ('Content-Length', str(len(body))),
        ]
        self.content_type = content_type
        self.headers_sent = False

    def __call__(self, start_response):
        status = status_line(self._status)
        start_response(status, self._get_headers())
        return [self._body]

    def send_headers(self, headers=None):
        headers = self._get_headers(headers)
        self.write(headers)
        self.headers_sent = True


    def write(self, chunk):
        """Writes chunk of data to a stream by using different writers.
        writer uses filter to modify chunk of data.
        write_eof() indicates end of stream.
        writer can't be used after write_eof() method being called.
        write() return drain future.
        """
        # check if send header
        self.writer.write(chunk)

    def writelines(self, data_lists):
        self.writer.writelines(data_lists)

    def write_eof(self):
        # do some check
        self.writer.write_eof()


    def set_cookie(self, name, value='', max_age=None, path='/',
                   domain=None, secure=False, httponly=False):
        self.cookies[name] = value
        if max_age is not None:
            self.cookies[name]['max-age'] = max_age
            if not max_age:
                expires_date = 'Thu, 01-Jan-1970 00:00:00 GMT'
            else:
                dt = formatdate(time.time() + max_age)
                expires_date = '%s-%s-%s GMT' % (dt[:7], dt[8:11], dt[12:25])

            self.cookies[name]['expires'] = expires_date


        if path is not None:
            self.cookies[name]['path'] = path
        if domain is not None:
            self.cookies[name]['domain'] = domain
        if secure:
            self.cookies[name]['secure'] = True
        if httponly:
            self.cookies[name]['httponly'] = True

    def delete_cookie(self, key, path='/', domain=None):
        self.set_cookie(key, max_age=0, path=path, domain=domain)

    def _get_headers(self, headers=None):
        if headers == None:
            headers = self.headers
        if isinstance(headers, bytes):
            h = headers
        elif isinstance(headers, str):
            h = headers.encode()
        elif isinstance(headeers, list):
            h = [(x.encode('ascii'), y.encode('ascii')) for x, y in headers]
        for c in self.cookies.values():
            h.append((b'Set-Cookie', c.output(header='').encode('ascii')))
        return h
