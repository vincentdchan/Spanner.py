# This is (almost) the same as test_webapp.py, but uses app.route().
import spanner


app = spanner.Spanner()

@app.route("/")
def index(req, res):
    res.write("Hello world!")

# @app.route("/squares")
# def squares(req, resp):
#     yield from picoweb.start_response(resp)
#     yield from app.render_template(resp, "squares.tpl", (req,))


import logging
logging.basicConfig(level=logging.INFO)

app.run(debug=True)
