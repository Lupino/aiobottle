asyncbottle
============

warper bottle use asynchttp base on  Asyncio (PEP-3156)

Quick start
-----------

    from asyncbottle import AsyncBottle
    import asynchttp

    app = AsyncBottle()

    @app.get('/')
    def example():
        rsp = yield from asynchttp.request('GET', 'http://python.org')
        content = yield from rsp.read()

        return content

    @app.get('/nomal')
    def nomal():
        return 'hello word!'

    def main(host='localhost', port=8080):
        from bottle import run

        run(app, host = host, port = port, server = 'asyncbottle:AsyncServer')

    main()

Requirements
-----------

Python 3.3

asyncio <http://code.google.com/p/tulip>

asynchttp <https://github.com/fafhrd91/asynchttp>

bottle <http://bottlepy.org>
