from bottle import Bottle, ServerAdapter, response, request, HTTPResponse\
        , HTTPError, tob, _e, _closeiter, html_escape, DEBUG
from traceback import format_exc

import sys

import logging

import asyncio
from aiohttp.wsgi import WSGIServerHttpProtocol, FileWrapper
import inspect

import itertools

logger = logging.getLogger('asyncbottle')
FORMAT = '%(asctime)-15s - %(message)s'
logger.setLevel(logging.DEBUG)
formater = logging.Formatter(FORMAT)
ch = logging.StreamHandler()
ch.setFormatter(formater)
logger.addHandler(ch)

class AioServer(ServerAdapter):
    def run(self, handler):
        def wsgi_app(env, start):
            def start_response(status_line, headerlist, exc_info=None):
                status_code = status_line.split(' ', 1)[0]
                headerdict = dict(map(lambda x: (x[0].lower(), x[1]), headerlist))
                length = headerdict.get('content-length', 0)
                logger.info('{} {} {} {}'.format(env['REQUEST_METHOD'],
                    env['RAW_URI'], status_code, length))
                return start(status_line, headerlist, exc_info)
            return handler(env, start_response)
        loop = asyncio.get_event_loop()
        f = loop.create_server(
                lambda: WSGIServerHttpProtocol(wsgi_app, loop = loop, readpayload=True),
                self.host, self.port)
        loop.run_until_complete(f)
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass

class AioBottle(Bottle):

    def _cast(self, out, peek=None):
        """ Try to convert the parameter into something WSGI compatible and set
        correct HTTP headers when possible.
        Support: False, str, dict, HTTPResponse, HTTPError, file-like,
        iterable of strings and iterable of strs
        """

        if isinstance(out, asyncio.Future) or inspect.isgenerator(out):
            out = yield from out

        # Empty output is done here
        if not out:
            if 'Content-Length' not in response:
                response['Content-Length'] = 0
            return []
        # Join lists of byte or str strings. Mixed lists are NOT supported
        if isinstance(out, (tuple, list))\
        and isinstance(out[0], (bytes, str)):
            out = out[0][0:0].join(out) # b'abc'[0:0] -> b''
        # Encode str strings
        if isinstance(out, str):
            out = out.encode(response.charset)
        # Byte Strings are just returned
        if isinstance(out, bytes):
            if 'Content-Length' not in response:
                response['Content-Length'] = len(out)
            return [out]
        # HTTPError or HTTPException (recursive, because they may wrap anything)
        # TODO: Handle these explicitly in handle() or make them iterable.
        if isinstance(out, HTTPError):
            out.apply(response)
            out = self.error_handler.get(out.status_code, self.default_error_handler)(out)
            return (yield from self._cast(out))
        if isinstance(out, HTTPResponse):
            out.apply(response)
            return (yield from self._cast(out.body))

        # File-like objects.
        if hasattr(out, 'read'):
            if 'wsgi.file_wrapper' in request.environ:
                return request.environ['wsgi.file_wrapper'](out)
            elif hasattr(out, 'close') or not hasattr(out, '__iter__'):
                return FileWrapper(out)

        # Handle Iterables. We peek into them to detect their inner type.
        try:
            iout = iter(out)
            first = next(iout)
            while not first:
                first = next(iout)
        except StopIteration:
            return (yield from self._cast(''))
        except HTTPResponse:
            first = _e()
        except (KeyboardInterrupt, SystemExit, MemoryError):
            raise
        except Exception:
            if not self.catchall: raise
            first = HTTPError(500, 'Unhandled exception', _e(), format_exc())

        # These are the inner types allowed in iterator or generator objects.
        if isinstance(first, HTTPResponse):
            return (yield from self._cast(first))
        elif isinstance(first, bytes):
            new_iter = itertools.chain([first], iout)
        elif isinstance(first, str):
            encoder = lambda x: x.encode(response.charset)
            new_iter = map(encoder, itertools.chain([first], iout))
        else:
            msg = 'Unsupported response type: %s' % type(first)
            return (yield from self._cast(HTTPError(500, msg)))
        if hasattr(out, 'close'):
            new_iter = _closeiter(new_iter, out.close)
        return new_iter

    def wsgi(self, environ, start_response):
        """ The bottle WSGI-interface. """
        try:
            out = yield from self._cast(self._handle(environ))
            # rfc2616 section 4.3
            if response._status_code in (100, 101, 204, 304)\
            or environ['REQUEST_METHOD'] == 'HEAD':
                if hasattr(out, 'close'): out.close()
                out = []
            start_response(response._status_line, response.headerlist)
            return out
        except (KeyboardInterrupt, SystemExit, MemoryError):
            raise
        except Exception:
            if not self.catchall: raise
            err = '<h1>Critical error while processing request: %s</h1>' \
                  % html_escape(environ.get('PATH_INFO', '/'))
            if DEBUG:
                err += '<h2>Error:</h2>\n<pre>\n%s\n</pre>\n' \
                       '<h2>Traceback:</h2>\n<pre>\n%s\n</pre>\n' \
                       % (html_escape(repr(_e())), html_escape(format_exc()))
            environ['wsgi.errors'].write(err)
            headers = [('Content-Type', 'text/html; charset=UTF-8')]
            start_response('500 INTERNAL SERVER ERROR', headers, sys.exc_info())
            return [tob(err)]

    def __call__(self, environ, start_response):
        ''' Each instance of :class:'Bottle' is a WSGI application. '''
        return (yield from self.wsgi(environ, start_response))
