_registry = {}


# taken from https://stackoverflow.com/questions/2020014/get-fully-qualified-class-name-of-an-object-in-python
def _objectname(o):
    if callable(o):
        return f"{o.__module__}.{o.__name__}"
    module = o.__class__.__module__
    if module is None or module == str.__class__.__module__:
        return o.__class__.__name__
    else:
        return module + "." + o.__class__.__name__


def register(layoutname=None):
    """Decorator to register layout function under a layout name name.
    The layout function does not take any arguments and should return an object of type htmlgenerator.BaseElement
    An existing layout name will always be overwritten if a layout with the same name is added later
    """

    def decorator(func):
        _registry[layoutname or _objectname(func)] = func
        return func

    return decorator


def get_layout(layoutname):
    if layoutname not in _registry:
        layoutlist = "\n  - " + "\n  - ".join(_registry.keys())
        raise RuntimeError(
            f"{layoutname} is not a registered layout name. Registered names are:{layoutlist}"
        )
    return _registry[layoutname]
