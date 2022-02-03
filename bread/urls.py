import django_celery_results.models
from django.apps import apps
from django.urls import include, path

from bread.utils import autopath, default_model_paths

from .views import administration, auth, userprofile
from .views.globalpreferences import PreferencesView

external_urlpatterns = [
    path(
        "preferences/",
        include(
            (
                [
                    path("global/", PreferencesView.as_view(), name="global"),
                    path(
                        "global/<slug:section>",
                        PreferencesView.as_view(),
                        name="global.section",
                    ),
                ],
                "dynamic_preferences",
            ),
            namespace="preferences",
        ),
    )
]
urlpatterns = [
    path(
        "accounts/login/",
        auth.BreadLoginView.as_view(),
        name="login",
    ),
    path(
        "accounts/logout/",
        auth.BreadLogoutView.as_view(),
        name="logout",
    ),
    path(
        "accounts/user/",
        userprofile.UserProfileView.as_view(),
        name="userprofile",
    ),
    autopath(
        userprofile.EditPersonalDataView.as_view(), urlname="userprofile.personal"
    ),
    autopath(userprofile.EditLoginView.as_view(), urlname="userprofile.login"),
    autopath(userprofile.password_reset, urlname="userprofile.password_reset"),
    autopath(
        userprofile.EditPermissionsView.as_view(), urlname="userprofile.permissions"
    ),
    autopath(userprofile.set_devmode, urlname="devmode"),
    path(
        "accounts/password_reset/",
        auth.BreadPasswordResetView.as_view(),
        name="password_reset",
    ),
    path(
        "accounts/password_reset/done/",
        auth.BreadPasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "accounts/reset/<uidb64>/<token>/",
        auth.BreadPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "accounts/reset/done/",
        auth.BreadPasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    path(
        "systeminformation", administration.systeminformation, name="systeminformation"
    ),
    path(
        "admin/maintenance",
        administration.maintenancesettings,
        name="breadadmin.maintenance",
    ),
    path(
        "admin/componentpreview",
        administration.componentpreview,
        name="breadadmin.componentpreview",
    ),
    *default_model_paths(
        django_celery_results.models.TaskResult,
        browseview=administration.TaskResultBrowseView,
    ),
] + external_urlpatterns

for app in apps.get_app_configs():
    if app.name.startswith("bread.contrib"):
        urlpatterns.append(path("contrib/", include(f"{app.name}.urls")))
