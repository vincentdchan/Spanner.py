import spanner
import time

app = spanner.Spanner()

@app.route("/")
def index(req, res):
    res.write("Hello world!\n")

@app.use
def mid(req, res, handle):
    early = time.time()
    yield from handle()
    late = time.time()
    info = "<br>This connection use {:.8f} seconds".format(late - early)
    res.write(info)


import logging
logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':
    app.run(debug=True)
