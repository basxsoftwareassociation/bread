import os
import signal

from django.http import HttpResponseRedirect

from .export import *  # noqa
from .jinja2 import *  # noqa
from .links import *  # noqa
from .model_helpers import *  # noqa
from .urls import *  # noqa


def get_all_subclasses(cls):
    return set(cls.__subclasses__()).union(
        [s for c in cls.__subclasses__() for s in get_all_subclasses(c)]
    )


# helper class to restart server after response has been sent
class HttpResponseRestartUWSGIServer(HttpResponseRedirect):
    def close(self):
        super().close()
        restart_uwsgi_appserver()


def restart_uwsgi_appserver():
    os.kill(os.getpid(), signal.SIGHUP)
