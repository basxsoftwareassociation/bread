"""
The Bread frameworks provides a view special util views to provide special functionality.
"""
import re

from django.apps import apps
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.views.generic import TemplateView
from django_extensions.management.modelviz import ModelGraph, generate_dot

import pygraphviz


class Overview(LoginRequiredMixin, TemplateView):
    """Lists all breadapps which have an index url"""

    template_name = "bread/overview.html"
    adminsite = None

    def __init__(self, adminsite, *args, **kwargs):
        self.adminsite = adminsite
        super().__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["app_urls"] = {}
        for admin in self.adminsite._registry.values():
            if "index" in admin.get_urls():
                app_label = getattr(admin, "app_label", admin.model._meta.app_label)
                if app_label not in context["app_urls"]:
                    context["app_urls"][app_label] = []
                context["app_urls"][app_label].append(
                    (admin.reverse("index"), admin.verbose_modelname)
                )
                for app, admins in context["app_urls"].items():
                    context["app_urls"][app] = sorted(admins, key=lambda a: a[1])

        context["app_urls"] = {k: v for k, v in sorted(context["app_urls"].items())}

        return context


class DataModel(LoginRequiredMixin, TemplateView):
    """Show the datamodel of the whole application"""

    template_name = "bread/datamodel.html"

    def get(self, request, *args, **kwargs):
        if "download" in request.GET:
            response = HttpResponse(
                self._render_svg(request.GET.getlist("app")).encode(),
                content_type="image/svg+xml",
            )
            response["Content-Disposition"] = f'inline; filename="datamodel.svg"'
            return response
        return super().get(request, *args, **kwargs)

    def _render_svg(self, apps=None):
        graph_models = ModelGraph(all_applications=not apps, app_labels=apps)
        graph_models.generate_graph_data()
        return (
            pygraphviz.AGraph(
                generate_dot(
                    graph_models.get_graph_data(),
                    template="django_extensions/graph_models/django2018/digraph.dot",
                )
            )
            .draw(format="svg", prog="dot")
            .decode()
        )

    def get_context_data(self, **kwargs):
        ret = super().get_context_data(**kwargs)
        # force SVG to be match page-layout instead of fixed width and height
        ret["datamodel"] = re.sub(
            'svg width="[0-9]*pt" height="[0-9]*pt"',
            "svg",
            self._render_svg(self.request.GET.getlist("app")),
        )
        ret["apps"] = sorted(
            filter(lambda a: not a.name.startswith("django"), apps.get_app_configs()),
            key=lambda a: a.verbose_name.lower(),
        )
        return ret
