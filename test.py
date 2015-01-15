import spanner


app = spanner.Spanner()

@app.route("/")
def index(req, res):
    res.write("Hello world!")

import logging
logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':
    app.run(debug=True)
