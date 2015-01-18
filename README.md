# Spanner

Spanner is a micro web framework written in python for human beings.

It's inspired by Flask & express.js

# How to use it

Spanner is very easy to use.

Here is an example

```````````python
  from spanner import Spanner

  app = Spanner()

  @app.route('/')
  def index(req, res):
    res.write("Hello world")

```````````

What's more?

Spanner is very easy to extend.

# Middlewares(Not Finish yet)

```````````python
  db = Database()
  @app.use
  def load_database(req, res, next):
    db.load()
    req.db = db
    yield from next()
    db.close()
```````````


# Sub-app(Not Finish yet)

`````````python
subapp = Spanner()
app.mount('/sub/', subapp)
`````````


# Required

 - Python 3.3+ (asyncio)
 - routes


# Note

ready to release
