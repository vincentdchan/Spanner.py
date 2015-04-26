from webspanner import Spanner
import time
import logging

app = Spanner()


@app.route("/")
def index(req, res):
    res.write("Hello world!\n")


@app.route("/user/{id}")
def show_id(req, res):
    id = req.params['id']
    res.write("ID: {}".format(id))


@app.use
def mid(req, res, handle):
    early = time.time()
    yield from handle()
    late = time.time()
    info = "<br>This connection use {:.8f} seconds".format(late - early)
    res.write(info)


logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':
    app.run(debug=True)
