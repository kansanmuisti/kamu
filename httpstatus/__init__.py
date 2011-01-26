from django.http import HttpResponsePermanentRedirect, HttpResponseRedirect, \
    HttpResponseBadRequest, HttpResponseForbidden, HttpResponseNotAllowed, \
    HttpResponseGone


class HTTPStatusException(Exception):
    pass


class Http301(HTTPStatusException):
    def __init__(self, path):
        self.path = path

    def get_response(self):
        return HttpResponsePermanentRedirect(self.path)


class Http302(HTTPStatusException):
    def __init__(self, path):
        self.path = path

    def get_response(self):
        return HttpResponseRedirect(self.path)


class Http400(HTTPStatusException):
    def get_response(self):
        return HttpResponseBadRequest()


class Http403(HTTPStatusException):
    def get_response(self):
        return HttpResponseForbidden()


class Http405(HTTPStatusException):
    def __init__(self, allowed_methods):
        self.allowed_methods = allowed_methods

    def get_response(self):
        return HttpResponseNotAllowed(self.allowed_methods)


class Http410(HTTPStatusException):
    def get_response(self):
        return HttpResponseGone()
