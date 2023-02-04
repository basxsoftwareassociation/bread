import django_celery_results.models
from django.apps import apps
from django.contrib.auth.models import Group, User
from django.urls import include, path

from .utils import autopath, default_model_paths
from .views import administration, auth, userprofile, users
from .views.globalpreferences import PreferencesView

urlpatterns = [
    path(
        "accounts/login/",
        auth.LoginView.as_view(),
        name="login",
    ),
    path(
        "accounts/logout/",
        auth.LogoutView.as_view(),
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
        auth.PasswordResetView.as_view(),
        name="password_reset",
    ),
    path(
        "accounts/password_reset/done/",
        auth.PasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "accounts/reset/<uidb64>/<token>/",
        auth.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "accounts/reset/done/",
        auth.PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    path(
        "systeminformation", administration.systeminformation, name="systeminformation"
    ),
    path(
        "admin/maintenance",
        administration.maintenancesettings,
        name="basxbreadadmin.maintenance",
    ),
    path(
        "admin/componentpreview",
        administration.componentpreview,
        name="basxbreadadmin.componentpreview",
    ),
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
    ),
    *default_model_paths(
        django_celery_results.models.TaskResult,
        browseview=administration.TaskResultBrowseView,
    ),
    *default_model_paths(
        User,
        browseview=users.UserBrowseView,
        editview=users.UserEditView,
        readview=users.UserReadView,
        addview=users.UserAddView,
    ),
    *default_model_paths(
        Group,
        browseview=users.GroupBrowseView,
        editview=users.GroupEditView,
    ),
]

for app in apps.get_app_configs():
    if app.name.startswith("basxbread.contrib"):
        urlpatterns.append(path("contrib/", include(f"{app.name}.urls")))
