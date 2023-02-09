from django.utils import formats
from django.utils.formats import localize
from django.utils.timezone import now
from jinja2.sandbox import SandboxedEnvironment


def jinja_env():
    environment = SandboxedEnvironment()
    environment.filters["map"] = lambda value, map: map.get(value, value)
    environment.filters["localize"] = localize
    environment.filters["date"] = formats.date_format
    environment.filters["time"] = formats.time_format
    environment.globals["now"] = now
    return environment


def jinja_render(template, **kwargs):
    return jinja_env().from_string(template).render(**kwargs)
