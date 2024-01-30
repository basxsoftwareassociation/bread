import base64

import fitz
import htmlgenerator as hg
from django import forms
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from guardian.shortcuts import get_objects_for_user

from basxbread import formatters, layout, utils, views

from . import models


def formview_processing(request, form, initial=None, custom_layout=None):
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
    formlayoutfields = []
    for f in form.customformfields.all():
        if "." in f.fieldname:
            formlayoutfields.append(f.fieldname)
        else:
            formlayoutfields.append(
                hg.DIV(layout.forms.FormField(f.fieldname), style="margin-top: 2rem")
            )

    def custom_layout_func(s):
        ret = super(view_class, s).get_layout()
        if custom_layout:
            ret = custom_layout(ret)
        return ret

    return view_class._with(
        model=model,
        fields=formlayoutfields,
        initial=initial,
        extra=3,
        get_layout=custom_layout_func,
    ).as_view()(request, **view_kwargs)


@utils.aslayout
def formview(request, pk):
    form = get_object_or_404(models.CustomForm, pk=pk)
    return formview_processing(request, form=form)


def remove_pdf_password(pdf_content, password):
    pdf = fitz.Document(stream=pdf_content)
    pdf.authenticate(password)
    ret = pdf.tobytes()
    pdf.close()
    return ret


@utils.aslayout
def pdfimportview(request, pk):
    class UploadForm(forms.Form):
        importfile = forms.FileField(required=False)
        password = forms.CharField(required=False, label=_("PDF password"))

    form = UploadForm()
    pdfimporter = get_object_or_404(models.PDFImport, pk=pk)
    if request.method == "POST":
        uploadform = UploadForm(request.POST, request.FILES)
        if uploadform.is_valid():
            if uploadform.cleaned_data.get("importfile"):
                pdfcontent = uploadform.cleaned_data["importfile"].read()
                if uploadform.cleaned_data["password"]:
                    pdfcontent = remove_pdf_password(
                        pdfcontent, uploadform.cleaned_data["password"]
                    )
                pdffields = models.pdf_fields(pdfcontent)
                initial = {}
                for pdf_formfield in pdfimporter.fields.exclude(customform_field=None):
                    value = pdffields.get(pdf_formfield.pdf_field_name, "")
                    value = pdf_formfield.mapping.get(value, value)
                    if "." in pdf_formfield.fieldname:
                        (
                            inlinefield,
                            subfield,
                        ) = pdf_formfield.fieldname.split(".", 1)
                        if inlinefield not in initial:
                            initial[inlinefield] = [{}]
                        if subfield in initial[inlinefield][-1]:
                            if pdf_formfield.join == "":  # add a new inline-entry
                                initial[inlinefield].append({})
                            else:  # join field-values
                                value = (
                                    initial[inlinefield][-1][subfield]
                                    + pdf_formfield.join.replace("\\n", "\n")
                                    + value
                                )
                        initial[inlinefield][-1][subfield] = value
                    else:
                        if pdf_formfield.fieldname in initial:
                            value = (
                                initial[pdf_formfield.fieldname]
                                + pdf_formfield.join.replace("\\n", "\n")
                                + value
                            )
                        initial[pdf_formfield.fieldname] = value

                request.method = "GET"

                def custom_layout(layout):
                    pdf_preview = hg.IFRAME(
                        src=f"data:application/pdf;base64,{base64.b64encode(pdfcontent).decode()}#toolbar=0",
                        height="100%",
                        width="100%",
                    )
                    layout[1].attributes[
                        "style"
                    ] = "display: grid; grid-template-columns: 50% 1fr; grid-gap: 1rem"
                    layout[1].insert(0, pdf_preview)
                    return layout

                return formview_processing(
                    request,
                    form=pdfimporter.customform,
                    initial=initial,
                    custom_layout=custom_layout,
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
            layout.forms.FormField("password"),
            layout.forms.helpers.Submit(label=_("Import")),
        ),
    )
