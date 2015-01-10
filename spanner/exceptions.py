############################################################
# HTTP Exceptions
############################################################

class HTTPException(Response, Exception):

    # You should set in subclasses:
    # status = 200

    status_code = None

    def __init__(self, *, headers=None, reason=None,
                 body=None, text=None, content_type=None):
        Response.__init__(self, status=self.status_code,
                          headers=headers, reason=reason,
                          body=body, text=text, content_type=content_type)
        Exception.__init__(self, self.reason)
        if self.body is None:
            self.text = "{}: {}".format(self.status, self.reason)

class BadRequestException(HttpException):
    pass


class HTTPError(HTTPException):
    """Base class for exceptions with status codes in the 400s and 500s."""


class HTTPRedirection(HTTPException):
    """Base class for exceptions with status codes in the 300s."""


class HTTPSuccessful(HTTPException):
    """Base class for exceptions with status codes in the 200s."""


class HTTPOk(HTTPSuccessful):
    status_code = 200


class HTTPCreated(HTTPSuccessful):
    status_code = 201


class HTTPAccepted(HTTPSuccessful):
    status_code = 202


class HTTPNonAuthoritativeInformation(HTTPSuccessful):
    status_code = 203


class HTTPNoContent(HTTPSuccessful):
    status_code = 204


class HTTPResetContent(HTTPSuccessful):
    status_code = 205


class HTTPPartialContent(HTTPSuccessful):
    status_code = 206
