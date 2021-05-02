from django.contrib.messages.views import SuccessMessageMixin
from django.urls import include, path
from django.utils.translation import gettext_lazy as _
from dynamic_preferences import views as preferences_views
from dynamic_preferences.forms import preference_form_builder
from dynamic_preferences.registries import global_preferences_registry
from dynamic_preferences.users import views as user_preferences_views
from dynamic_preferences.users.registries import user_preferences_registry

from .forms.forms import PreferencesForm, UserPreferencesForm
from .views import system


# preferences views need a bit of weird treatment, I think we coudl make this code much shorter
def user_get_form_class(self, *args, **kwargs):
    section = self.kwargs.get("section", None)
    return preference_form_builder(
        UserPreferencesForm,
        instance=self.request.user,
        section=section,
        **kwargs,
    )


PreferencesView = type(
    "PreferencesView",
    (SuccessMessageMixin, preferences_views.PreferenceFormView),
    {"success_message": "Preferences updated"},
)


class UserPreferencesView(
    SuccessMessageMixin, user_preferences_views.UserPreferenceFormView
):
    get_form_class = user_get_form_class

    def get_success_message(self, data):
        data.pop("user_interface__navigation_menu_extended")
        if data:
            return _("Preferences updated")
        return None


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
                    path(
                        "user/",
                        UserPreferencesView.as_view(registry=user_preferences_registry),
                        name="user",
                    ),
                    path(
                        "user/<slug:section>",
                        UserPreferencesView.as_view(registry=user_preferences_registry),
                        name="user.section",
                    ),
                ],
                "dynamic_preferences",
            ),
            namespace="preferences",
        ),
    ),
]


urlpatterns = [
    path("auth/", include("django.contrib.auth.urls")),
    path("accounts/login/", system.BreadLoginView.as_view(), name="login"),
    path("accounts/logout/", system.BreadLogoutView.as_view(), name="logout"),
] + external_urlpatterns
