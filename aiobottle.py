from bottle import Bottle, ServerAdapter, response, request, HTTPResponse\
        , HTTPError, tob, _e, html_escape, DEBUG, RouteReset
from traceback import format_exc

import sys

import logging

import asyncio
from aiohttp.wsgi import WSGIServerHttpProtocol
import inspect
from aiohttp.worker import AsyncGunicornWorker as _AsyncGunicornWorker

logger = logging.getLogger('asyncbottle')
FORMAT = '%(asctime)-15s - %(message)s'
logger.setLevel(logging.DEBUG)
formater = logging.Formatter(FORMAT)
ch = logging.StreamHandler()
ch.setFormatter(formater)
logger.addHandler(ch)

class AsyncServer(ServerAdapter):
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

class AsyncBottle(Bottle):

    def _handle(self, environ):
        try:
            environ['bottle.app'] = self
            request.bind(environ)
            response.bind()
            route, args = self.router.match(environ)
            environ['route.handle'] = route
            environ['bottle.route'] = route
            environ['route.url_args'] = args
            out = route.call(**args)
            if isinstance(out, asyncio.Future) or inspect.isgenerator(out):
                out = yield from out
            return out
        except HTTPResponse:
            return _e()
        except RouteReset:
            route.reset()
            return (yield from self._handle(environ))
        except (KeyboardInterrupt, SystemExit, MemoryError):
            raise
        except Exception:
            if not self.catchall: raise
            stacktrace = format_exc()
            environ['wsgi.errors'].write(stacktrace)
            return HTTPError(500, "Internal Server Error", _e(), stacktrace)

    def wsgi(self, environ, start_response):
        """ The bottle WSGI-interface. """
        try:
            out = yield from self._cast((yield from self._handle(environ)))
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

class AsyncGunicornWorker(_AsyncGunicornWorker):

    def factory(self, wsgi, host, port):
        proto = WSGIServerHttpProtocol(
            wsgi, loop=self.loop,
            log=self.log,
            access_log=self.log.access_log,
            access_log_format=self.cfg.access_log_format,
            readpayload=True)
        return self.wrap_protocol(proto)
