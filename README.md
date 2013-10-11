asyncbottle
============

warper bottle use asynchttp base on  Tulip (PEP-3156)

Quick start
-----------

    from asyncbottle import TulipBottle
    import asynchttp

    app = TulipBottle()

    @app.get('/')
    def example():
        rsp = yield from asynchttp.request('GET', 'http://python.org')
        content = yield from rsp.read()

        return content

    def main(host='localhost', port=8080):
        from bottle import run

        run(app, host = host, port = port, server = 'asyncbottle:TulipServer')
        
    main()

Requirements
-----------

Python 3.3

tulip <http://code.google.com/p/tulip>

asynchttp <https://github.com/fafhrd91/asynchttp>
