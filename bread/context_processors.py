def bread_context(request):
    from django.conf import settings

    if hasattr(settings, "PLATFORMNAME"):
        return {"PLATFORMNAME": settings.PLATFORMNAME}
    return {}
