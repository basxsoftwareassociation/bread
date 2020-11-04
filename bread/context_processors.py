from django.conf import settings


def bread_context(request):
    ret = {}
    return ret


def compress_offline_context():
    yield {"STATIC_URL": settings.STATIC_URL, **bread_context(None)}
