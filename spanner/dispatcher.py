class Dispatcher(object):
    def __init__(self):
        self._list = []

    def connect(self, path, controller, **kwargs):
        item = (path, dict(kwargs))
        self._list.append(item)
        return item

    def match(self, path):
    """
    match method return a dict or None
        {
            func: The handler function
            params: params in the path
            condition: **conditon args
        }
    params work like this:
        if the path is
            "/user/{username}" -> "/user/Chan"
        Then:
            params = {
                "username": "Chan"
            }
    """
        pass
