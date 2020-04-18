from django.url import include, path
from django.views.generic import DeleteView, DetailView, UpdateView

from . import views


class BreadAdmin:
    namespace = None
    app_namespace = None
    model = None
    defaulturl = None

    def __init__(self):
        self.namespace = self.namespace or "bread"
        self.app_namespace = self.app_namespace or self.model._meta.app_label

    def get_views(self):
        return {
            "browse": views.GeneralList.as_view(),
            "read": views.GeneralDetail.as_view(),
            "edit": views.GeneralUpdate.as_view(),
            "add": views.GeneralCreate.as_view(),
            "delete": views.GeneralDelete.as_view(),
        }

    def get_modelname(self):
        """Machine-readable name for the model"""
        return self.model._meta.model_name

    @property
    def urls(self):
        """Urls for inclusion in django urls"""
        urls = []
        for viewname, view in self.get_views():
            url_name = f"{self.modelname}_{viewname}"
            if (
                isinstance(view, UpdateView)
                or isinstance(DetailView)
                or isinstance(DeleteView)
            ):
                urls.append(
                    path(f"{self.modelname}/{viewname}/<int:pk>", view, name=url_name)
                )
            else:
                urls.append(path(f"{self.modelname}/{viewname}", view, name=url_name))
        return include((urls, self.app_namespace), self.namespace)

    # sugar functions

    @property
    def modelname(self):
        """Machine-readable name for the model"""
        return self.get_modelname()

    @property
    def verbose_modelname(self):
        """Shortcut to use in templates"""
        return self.model._meta.verbose_name

    @property
    def verbose_modelname_plural(self):
        """Shortcut to use in templates"""
        return self.model._meta.verbose_name_plural
