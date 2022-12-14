import htmlgenerator as hg
from django import forms
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from guardian.shortcuts import get_objects_for_user

from basxbread import formatters, layout, utils, views

from . import models


def formview_processing(request, form, initial=None):
    model = form.model.model_class()
    pk_fields = [f.strip() for f in form.pk_fields.split(",")]
    GET = request.GET.copy()
    filter_kwargs = {field: GET.pop(field)[0] for field in pk_fields if field in GET}
    instance = (
        get_objects_for_user(
            request.user,
            f"view_{model.__name__.lower()}",
            model.objects.filter(**filter_kwargs),
            with_superuser=True,
        )
        if form.pk_fields and filter_kwargs
        else model.objects.none()
    )
    view_class = views.AddView
    view_kwargs = {}
    if pk_fields:
        if instance.count() > 1:  # show an error
            return hg.BaseElement(
                layout.notification.InlineNotification(
                    _("Error"),
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
            view_class = views.EditView._with(success_url=request.get_full_path())
            view_kwargs["pk"] = instance.first().pk

    request.GET = GET
    initial = initial or {}
    return view_class._with(
        model=model,
        fields=[f.fieldname for f in form.customformfields.all()],
        initial=initial,
    ).as_view()(request, **view_kwargs)


@utils.aslayout
def formview(request, pk):
    form = get_object_or_404(models.CustomForm, pk=pk)
    return formview_processing(request, form=form)


class UploadForm(forms.Form):
    importfile = forms.FileField(required=False)


@utils.aslayout
def pdfimportview(request, pk):
    form = UploadForm()
    pdfimporter = get_object_or_404(models.PDFImport, pk=pk)
    if request.method == "POST":
        uploadform = UploadForm(request.POST, request.FILES)
        if uploadform.is_valid():
            if uploadform.cleaned_data.get("importfile"):
                initial = {}
                defined_formfields = {
                    f.pdf_field_name: f.customform_field.fieldname
                    for f in pdfimporter.fields.all()
                }
                for field, value in models.pdf_fields(
                    uploadform.cleaned_data["importfile"].read()
                ).items():
                    if field in defined_formfields:
                        if "." in defined_formfields[field]:
                            inlinefield, subfield = defined_formfields[field].split(
                                ".", 1
                            )
                            if inlinefield not in initial:
                                initial[inlinefield] = [{}]
                            if subfield in initial[inlinefield][-1]:
                                initial[inlinefield].append({})
                            initial[inlinefield][-1][subfield] = value
                        else:
                            initial[defined_formfields[field]] = value
                request.method = "GET"
                return formview_processing(
                    request, form=pdfimporter.customform, initial=initial
                )
            if "importfile" not in request.POST:
                return formview_processing(request, form=pdfimporter.customform)

    return hg.BaseElement(
        hg.H1(pdfimporter),
        hg.DIV(
            hg.format(
                _("Import filled out version of {}"),
                formatters.as_download(pdfimporter.pdf),
            ),
            style="margin-top: 2rem; margin-bottom: 2rem",
        ),
        layout.forms.Form(
            form,
            layout.forms.FormField("importfile"),
            layout.forms.helpers.Submit(label=_("Import")),
        ),
    )
