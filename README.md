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

The method will be decorated to be a coroutine ***automatically***, so you ***do not*** need to decorate the function with ```@asyncio.coroutine```

# What's more?

Spanner is very easy to extend.

## Middlewares

```````````python
  app = spanner.Spanner()

  @app.route("/")
  def index(req, res):
    res.write("Hello world!\n")

  @app.use
  def mid(req, res, handle):
    early = time.time()
    yield from handle()
    late = time.time()
    info = "<br>This connection use {:.5f} seconds".format(late - early)
    res.write(info)
```````````
The method will be decorated to be a coroutine ***automatically***, so you ***do not*** need to decorate the function with ```@asyncio.coroutine```

The code will export
```
Hello world!
This connection use 0.00000000 seconds
```


## Sub-app(Not Finish yet)

`````````python
subapp = Spanner()
app.mount('/sub/', subapp)
`````````


# Required

 - Python 3.3+ (asyncio)
 - routes


# Note

ready to release
