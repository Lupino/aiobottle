from aiobottle import AsyncBottle
import aiohttp

app = AsyncBottle()

@app.get('/')
def example():
    rsp = yield from aiohttp.request('GET', 'http://python.org')
    content = yield from rsp.read()

    return bytes(content)

@app.get('/nomal')
def nomal():
    return 'hello word!'

def main(host='localhost', port=8080):
    from bottle import run

    run(app, host = host, port = port, server = 'aiobottle:AsyncServer')

if __name__ == '__main__':
    main()
