from crispy_forms.utils import TEMPLATE_PACK
from django.conf import settings


def bread_context(request):
    ret = {
        "TEMPLATE_PACK": TEMPLATE_PACK,
        "TEMPLATE_PACK_BASE": f"{TEMPLATE_PACK}/base.html",
    }
    # used for all css classes in the carbon_design templates
    # just want to make it explicit here:
    if TEMPLATE_PACK == "carbon_design":
        ret["prefix"] = "bx"
    return ret


def compress_offline_context():
    yield {"STATIC_URL": settings.STATIC_URL, **bread_context(None)}
