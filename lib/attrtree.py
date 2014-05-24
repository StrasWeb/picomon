class AttrTree(object):
    """ A class holding attributes/items, but not allowing to create
    new ones implicitely.  Use .install_attr() instead. """

    def __init__(self):
        object.__setattr__(self, '_attrs', {})

    def install_attr(self, key, default):
        if key in self._attrs:
            raise KeyError('Key "%s" already exists' % key)
        stems = key.split('.', 2)
        if len(stems) < 2:
            self._attrs[key] = default
        elif stems[0] in self._attrs:
            self._attrs[stems[0]].install_attr(stems[1], default)
        else:
            sub = AttrTree()
            sub.install_attr(stems[1], default)
            self._attrs[stems[0]] = sub

    def __getitem__(self, key):
        return self._attrs[key]

    def __setitem__(self, key, value):
        if not key in self._attrs:
            raise KeyError('Key "%s" does not exist' % key)
        elif isinstance(self._attrs[key], AttrTree):
            raise KeyError('Key "%s" is not settable' % key)
        self._attrs[key] = value

    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, value):
        self[key] = value
