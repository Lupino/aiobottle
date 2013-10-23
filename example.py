from asyncbottle import AsyncBottle
import asynchttp

app = AsyncBottle()

@app.get('/')
def example():
    rsp = yield from asynchttp.request('GET', 'http://python.org')
    content = yield from rsp.read()

    return content

def main(host='localhost', port=8080):
    from bottle import run

    run(app, host = host, port = port, server = 'asyncbottle:AsyncServer')

main()
