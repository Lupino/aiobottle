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
