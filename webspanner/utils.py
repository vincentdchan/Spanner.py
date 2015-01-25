import re
from collections import abc


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

_marker = object()

class _Base:

    __slots__ = ('_items',)

    def getall(self, key, default=_marker):
        """
        Return a list of all values matching the key (may be an empty list)
        """
        res = [v for k, v in self._items if k == key]
        if res:
            return res
        if not res and default is not _marker:
            return default
        raise KeyError('Key not found: %r' % key)

    def getone(self, key, default=_marker):
        """
        Get first value matching the key
        """
        for k, v in self._items:
            if k == key:
                return v
        if default is not _marker:
            return default
        raise KeyError('Key not found: %r' % key)

    # Mapping interface #

    def __getitem__(self, key):
        return self.getone(key, _marker)

    def get(self, key, default=None):
        return self.getone(key, default)

    def __iter__(self):
        return iter(self.keys())

    def __len__(self):
        return len(self._items)

    def keys(self):
        return _KeysView(self._items)

    def items(self):
        return _ItemsView(self._items)

    def values(self):
        return _ValuesView(self._items)

    def __eq__(self, other):
        if not isinstance(other, abc.Mapping):
            return NotImplemented
        if isinstance(other, _Base):
            return self._items == other._items
        for k, v in self.items():
            nv = other.get(k, _marker)
            if v != nv:
                return False
        return True

    def __contains__(self, key):
        for k, v in self._items:
            if k == key:
                return True
        return False

    def __repr__(self):
        body = ', '.join("'{}': {!r}".format(k, v) for k, v in self.items())
        return '<{} {{{}}}>'.format(self.__class__.__name__, body)


class _CIBase(_Base):

    def getall(self, key, default=_marker):
        return super().getall(key.upper(), default)

    def getone(self, key, default=_marker):
        return super().getone(key.upper(), default)

    def get(self, key, default=None):
        return super().get(key.upper(), default)

    def __getitem__(self, key):
        return super().__getitem__(key.upper())

    def __contains__(self, key):
        return super().__contains__(key.upper())


class MultiDict(_Base, abc.MutableMapping):

    def __init__(self, *args, **kwargs):
        self._items = []

        self._extend(args, kwargs, self.__class__.__name__, self.add)

    def add(self, key, value):
        """
        Add the key and value, not overwriting any previous value.
        """
        self._items.append((key, value))

    def copy(self):
        """Returns a copy itself."""
        cls = self.__class__
        return cls(self.items())

    def extend(self, *args, **kwargs):
        """Extends current MultiDict with more values.
        This method must be used instead of update.
        """
        self._extend(args, kwargs, 'extend', self.add)

    def _extend(self, args, kwargs, name, method):
        if len(args) > 1:
            raise TypeError("{} takes at most 1 positional argument"
                            " ({} given)".format(name, len(args)))
        if args:
            arg = args[0]
            if isinstance(args[0], MultiDictProxy):
                items = arg._items
            elif isinstance(args[0], MultiDict):
                items = arg._items
            elif hasattr(arg, 'items'):
                items = arg.items()
            else:
                for item in arg:
                    if not len(item) == 2:
                        raise TypeError(
                            "{} takes either dict or list of (key, value) "
                            "tuples".format(name))
                items = arg

            for key, value in items:
                method(key, value)

        for key, value in kwargs.items():
            method(key, value)

    def clear(self):
        """Remove all items from MultiDict"""
        self._items.clear()

    # Mapping interface #

    def __setitem__(self, key, value):
        self._replace(key, value)

    def __delitem__(self, key):
        items = self._items
        found = False
        for i in range(len(items) - 1, -1, -1):
            if items[i][0] == key:
                del items[i]
                found = True
        if not found:
            raise KeyError(key)

    def setdefault(self, key, default=None):
        for k, v in self._items:
            if k == key:
                return v
        self._items.append((key, default))
        return default

    def pop(self, key, default=_marker):
        value = None
        found = False
        for i in range(len(self._items) - 1, -1, -1):
            if self._items[i][0] == key:
                value = self._items[i][1]
                del self._items[i]
                found = True
        if not found:
            if default is _marker:
                raise KeyError(key)
            else:
                return default
        else:
            return value

    def popitem(self):
        if self._items:
            return self._items.pop(0)
        else:
            raise KeyError("empty multidict")

    def update(self, *args, **kwargs):
        self._extend(args, kwargs, 'update', self._replace)

    def _replace(self, key, value):
        if key in self:
            del self[key]
        self.add(key, value)

class CIMultiDict(_CIBase, MultiDict):

    def add(self, key, value):
        super().add(key.upper(), value)

    def __setitem__(self, key, value):
        super().__setitem__(key.upper(), value)

    def __delitem__(self, key):
        super().__delitem__(key.upper())

    def _replace(self, key, value):
        super()._replace(key.upper(), value)

    def setdefault(self, key, default=None):
        key = key.upper()
        return super().setdefault(key, default)

class MultiDictProxy(_Base, abc.Mapping):

    def __init__(self, arg):
        if not isinstance(arg, MultiDict):
            raise TypeError(
                'MultiDictProxy requires MultiDict instance, not {}'.format(
                    type(arg)))

        self._items = arg._items

    def copy(self):
        """Returns a copy itself."""
        return MultiDict(self.items())

class CIMultiDictProxy(_CIBase, MultiDictProxy):

    def __init__(self, arg):
        if not isinstance(arg, CIMultiDict):
            raise TypeError(
                'CIMultiDictProxy requires CIMultiDict instance, not {}'
                .format(type(arg)))

        self._items = arg._items

    def copy(self):
        """Returns a copy itself."""
        return CIMultiDict(self.items())

class _ViewBase:

    __slots__ = ('_keys', '_items')

    def __init__(self, items):
        self._items = items

    def __len__(self):
        return len(self._items)

class _ItemsView(_ViewBase, abc.ItemsView):

    def __contains__(self, item):
        assert isinstance(item, tuple) or isinstance(item, list)
        assert len(item) == 2
        return item in self._items

    def __iter__(self):
        yield from self._items


class _ValuesView(_ViewBase, abc.ValuesView):

    def __contains__(self, value):
        for item in self._items:
            if item[1] == value:
                return True
        return False

    def __iter__(self):
        for item in self._items:
            yield item[1]


class _KeysView(_ViewBase, abc.KeysView):

    def __contains__(self, key):
        for item in self._items:
            if item[0] == key:
                return True
        return False

    def __iter__(self):
        for item in self._items:
            yield item[0]
