import re


qu_re = re.compile(r"%([0-9A-Fa-f]{2})")

def unquote_plus(s):
    def decode(s):
        val = int(s.group(1), 16)
        return chr(val)
    return qu_re.sub(decode, s.replace("+", " "))

def parse_qs(s):
    res = {}
    if s:
        pairs = s.split("&")
        for p in pairs:
            vals = [unquote_plus(x) for x in p.split("=", 1)]
            if len(vals) == 1:
                vals.append(True)
            if vals[0] in res:
                res[vals[0]].append(vals[1])
            else:
                res[vals[0]] = [vals[1]]
    return res

class MultiDict(dict):
    def __getitem__(self, key):
        value = super().__getitem__(key)
        return value[0]

    def __setitem__(self, key, value):
        super().__setitem__(key, [value])

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def getlist(self, key, default=[]):
        return super().get(key, default)

    def items(self):
        for key in self:
            yield key, self[key]

    def values(self):
        for key in self:
            yield self[key]

    def lists(self):
        return super().items()

    def __repr__(self):  # pragma: no cover
        return "<MultiDict {}>".format(super().__repr__())
