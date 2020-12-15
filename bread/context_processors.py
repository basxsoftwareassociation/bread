from django.conf import settings


def bread_context(request):
    ret = {
        "branding": getattr(settings, "BRANDING", {}),
        "OVERRIDE_STYLESHEET": getattr(settings, "OVERRIDE_STYLESHEET", None),
    }
    return ret


def compress_offline_context():
    yield {"STATIC_URL": settings.STATIC_URL, **bread_context(None)}
