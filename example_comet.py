import spanner
import time
import asyncio

app = spanner.Spanner()

waiter = list()

@app.route("/")
def index(req, res):
    f = asyncio.Future(loop=req._app.loop)
    waiter.append(f)
    msg = yield from f
    res.write(msg)

@app.route("/back")
def back(req, res):
    while True:
        if len(waiter) == 0:
            break
        l = waiter.pop()
        l.set_result("ok")
    res.write("done")

if __name__ == '__main__':
    app.run(debug=True)
