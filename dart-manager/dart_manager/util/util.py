class ClassProperty(object):

    def __init__(self, f):
        self.f = f

    def __get__(self, instance, cls=None):
        if cls is None:
            cls = type(instance)

        return self.fget.__get__(instance, cls)()

def classproperty(func):
    if not isinstance(func, (classmethod, staticmethod)):
        func = classmethod(func)

    return ClassProperty(func)

class lazyproperty(object):
    def __init__(self):
        self._value = None

    def __call__(self, func):
        @property
        def wrapped():
            if self._value is None:
                self._value = func()

            return self._value

        return wrapped
