asyncbottle
============

a warper bottle use aiohttp base on Asyncio (PEP-3156)

Quick start
-----------

    from aiobottle import AioBottle
    import aiohttp

    app = AioBottle()

    @app.get('/')
    def example():
        rsp = yield from aiohttp.request('GET', 'http://python.org')
        content = yield from rsp.read()

        return content

    @app.get('/nomal')
    def nomal():
        return 'hello word!'

    def main(host='localhost', port=8080):
        from bottle import run

        run(app, host = host, port = port, server = 'aiobottle:AioServer')

    main()

Requirements
-----------

Python 3.3

asyncio <http://code.google.com/p/tulip>

aiohttp <https://github.com/fafhrd91/aiohttp>

bottle <http://bottlepy.org>
