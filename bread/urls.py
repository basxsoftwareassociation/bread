import pkg_resources

from django.http import HttpResponse
from django.urls import include, path, reverse_lazy
from django.views.generic import RedirectView

from . import views as breadviews


def protectedMedia(request, path):
    if request.user.is_staff:
        response = HttpResponse(status=200)
        del response["Content-Type"]
        response["X-Accel-Redirect"] = f"/protected/{path}"
        return response
    else:
        return HttpResponse(status=404)


urlpatterns = []

breadapp_urls = []
for entrypoint in pkg_resources.iter_entry_points(group="breadapp", name="appname"):
    fullappname = entrypoint.load()
    appname = fullappname.split(".")[-1]
    breadapp_urls.append(
        path(f"{appname}/", include(f"{fullappname}.urls", namespace=appname))
    )


urlpatterns = [
    path("bread/", breadviews.Overview.as_view(), name="bread_overview"),
    path("bread/", include((breadapp_urls, "bread"), namespace="bread")),
    path("preferences/", include("dynamic_preferences.urls", namespace="preferences")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("ckeditor/", include("ckeditor_uploader.urls")),
    path("", RedirectView.as_view(url=reverse_lazy("bread_overview"))),
]
