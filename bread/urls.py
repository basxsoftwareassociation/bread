import django_celery_results.models
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import include, path
from dynamic_preferences import views as preferences_views
from dynamic_preferences.registries import global_preferences_registry

from bread.utils import autopath, default_model_paths

from .forms.forms import PreferencesForm
from .views import admin, auth, system, userprofile

PreferencesView = type(
    "PreferencesView",
    (SuccessMessageMixin, preferences_views.PreferenceFormView),
    {"success_message": "Preferences updated"},
)

external_urlpatterns = [
    path("ckeditor/", include("ckeditor_uploader.urls")),
    path(
        "preferences/",
        include(
            (
                [
                    path(
                        "global/",
                        PreferencesView.as_view(
                            registry=global_preferences_registry,
                            form_class=PreferencesForm,
                        ),
                        name="global",
                    ),
                    path(
                        "global/<slug:section>",
                        PreferencesView.as_view(
                            registry=global_preferences_registry,
                            form_class=PreferencesForm,
                        ),
                        name="global.section",
                    ),
                ],
                "dynamic_preferences",
            ),
            namespace="preferences",
        ),
    ),
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
    path("systeminformation", system.systeminformation, name="systeminformation"),
    path("admin/maintenance", admin.maintenancesettings, name="breadadmin.maintenance"),
    path(
        "admin/widgetpreview",
        admin.widgetpreview,
        name="breadadmin.widgetpreview",
    ),
    *default_model_paths(
        django_celery_results.models.TaskResult,
        browseview=admin.TaskResultBrowseView,
    ),
] + external_urlpatterns
