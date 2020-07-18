from bread.admin import site as breadsite
from django.urls import path

urlpatterns = [
    path("", breadsite.urls),
]
