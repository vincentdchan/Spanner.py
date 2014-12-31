Spanner
===========

Spanner is a micro web framework written in python for human beings.

It's inspired by Flask & express.js

How to use it
===========

Spanner is very easy to use.

Here is an example

```````````python
  from spanner import Spanner

  app = Spanner()

  @app.route('/')
  def index(req, res):
    res.send("Hello world")

```````````

What's more?

Spanner is very easy to extend.

```````````python
  db = Database()
  @app.before_request('initdb', autoload=False)
  def init_db(req, res):
    req.db = db

  @app.route('/user/{id}')
  def user_info(req, res):
    db = req.db
    # do something with db
    # res.send(something)
```````````



Spanner also provides websocket.(wait to finish)

Required
============
Python 3.4+ for asyncio
