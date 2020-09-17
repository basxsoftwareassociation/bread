from crispy_forms.utils import TEMPLATE_PACK
from django.conf import settings


def bread_context(request):
    return {
        "TEMPLATE_PACK": TEMPLATE_PACK,
        "TEMPLATE_PACK_BASE": f"{TEMPLATE_PACK}/base.html",
    }


def compress_offline_context():
    yield {"STATIC_URL": settings.STATIC_URL, **bread_context(None)}
