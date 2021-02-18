from django.urls import path

from bread.admin import site as breadsite

urlpatterns = [
    path("", breadsite.urls),
]
