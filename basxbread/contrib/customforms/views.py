import htmlgenerator as hg
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from basxbread import layout, utils, views

from . import models


@utils.aslayout
def formview(request, pk):
    form = get_object_or_404(models.CustomForm, pk=pk)
    model = form.model.model_class()
    pk_fields = form.pk_fields.split(",")
    filter_kwargs = {field: request.GET.get(field, None) for field in pk_fields}
    instance = (
        model.objects.filter(**filter_kwargs)
        if form.pk_fields
        else model.objects.none()
    )
    view_kwargs = {}
    view = views.AddView._with(
        model=model, fields=[f.fieldname for f in form.customformfields.all()]
    ).as_view()
    if pk_fields:
        if instance.count() > 1:  # show an error
            return hg.BaseElement(
                layout.notification.InlineNotification(
                    _("More than one instance was selected by the query elements"),
                    kind="error",
                ),
                _("The following arguments were passed to the query:"),
                layout.datatable.DataTable(
                    [
                        layout.datatable.DataTableColumn(
                            _("Query field name"), hg.C("row.0")
                        ),
                        layout.datatable.DataTableColumn(
                            _("Query field value"), hg.C("row.1")
                        ),
                    ],
                    filter_kwargs.items(),
                ).with_toolbar(title=_("Model: ") + model._meta.verbose_name),
                layout.datatable.DataTable.from_queryset(
                    instance, title=_("Produced results (should only produce 1)")
                ),
            )
        if instance.count() == 1:  # show an edit view
            view = views.EditView._with(model=model).as_view()
            view_kwargs["pk"] = instance.pk
    return view(request, **view_kwargs)
