import io

import bread.settings as app_settings
from ckeditor.fields import RichTextField
from ckeditor_uploader.fields import RichTextUploadingField
from django.apps import apps
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.http import HttpResponse
from django.template import Context, Template
from django.template.loader import render_to_string
from django.urls import NoReverseMatch, reverse
from django.utils.html import format_html_join, linebreaks, mark_safe
from django_countries.fields import CountryField
from sorl.thumbnail import get_thumbnail

from .models import VirtualField


def try_get_url(model, object):
    if hasattr(object, "get_absolute_url"):
        return object.get_absolute_url()
    elif hasattr(model, "_meta"):
        try:
            try_resolve_app_label(
                model._meta.app_label,
                model._meta.model_name + "_detail",
                kwargs={"pk": object.pk},
            )
        except NoReverseMatch:
            return None
    return None


def modelname(model, plural=False):
    if plural:
        return model._meta.verbose_name_plural.title()
    return model._meta.verbose_name.title()


def pretty_fieldname(field):
    if field.is_relation and (field.one_to_many or field.many_to_many):
        return field.target_field.model._meta.verbose_name_plural.title()
    elif field.is_relation and field.one_to_one:
        return field.target_field.model._meta.verbose_name.title()
    elif isinstance(field, GenericForeignKey):
        return field.name.replace("_", " ").title()
    else:
        return field.verbose_name.title()


def try_resolve_app_label(app_label, url_name, kwargs={}):
    try:
        ret = reverse("bread:%s:%s" % (app_label, url_name), kwargs=kwargs)
    except NoReverseMatch:
        ret = reverse(url_name, kwargs=kwargs)
    return ret


def listurl(model):
    return try_resolve_app_label(
        model._meta.app_label, model._meta.model_name + "_list"
    )


def detailurl(object):
    model = object._meta.model
    try:
        return try_resolve_app_label(
            model._meta.app_label,
            model._meta.model_name + "_detail",
            kwargs={"pk": object.pk},
        )
    except NoReverseMatch:
        return None


def object_link(object):
    link = detailurl(object)
    if link:
        return mark_safe(f'<a href="{link}">{object}</a>')
    return str(object)


def createurl(model):
    return try_resolve_app_label(
        model._meta.app_label, model._meta.model_name + "_create"
    )


def updateurl(object):
    model = object._meta.model
    return try_resolve_app_label(
        model._meta.app_label,
        model._meta.model_name + "_update",
        kwargs={"pk": object.pk},
    )


def deleteurl(object):
    model = object._meta.model
    return try_resolve_app_label(
        model._meta.app_label,
        model._meta.model_name + "_delete",
        kwargs={"pk": object.pk},
    )


def has_permission(user, operation, instance):
    """
        instance: can be model instance or a model
        operation is one of ["view", "add", "change", "delete"]
    """
    operations = ["view", "add", "change", "delete"]
    if operation not in operations:
        raise RuntimeError(
            f"argument 'operation' must be one of {operations} but was {operation}"
        )
    return user.has_perm(
        f"{instance._meta.app_label}.{operation}_{instance._meta.model_name}", instance
    ) or user.has_perm(
        f"{instance._meta.app_label}.{operation}_{instance._meta.model_name}"
    )


def htmlformatter(model, field):
    """
    Returns a function f(field, value) which returns the html value for a field when called.
    """

    formatter = DEFAULT_FORMATTERS.get(type(field), None)

    def get_field_display(object):
        value = getattr(object, field.name, None)
        if value is None:
            return to_none()
        if formatter is None:
            return value
        return formatter(field, value)

    return get_field_display


def render_queryset_complex(
    qs,
    fields=None,
    max_count=None,
    hide_title=True,
    hide_actions=True,
    hide_summary=True,
    hide_heading=True,
):
    # import must be here to prevent circular import
    from .views import GeneralList

    context = {
        "view": GeneralList(model=qs.model, fields=fields),
        "object_list": qs if max_count is None else qs[:3],
        "hide_title": hide_title,
        "hide_actions": hide_actions,
        "hide_summary": hide_summary,
        "hide_heading": hide_heading,
    }
    ret = render_to_string("bread/inline_list.html", context)
    return ret


def to_none():
    return mark_safe(app_settings.HTML_NONE)


def to_one(field, value):
    if isinstance(field.related_model, str):
        field.related_model = apps.get_model(field.related_model)
    if isinstance(value, int):
        value = field.related_model.objects.get(pk=value)
    url = detailurl(value)
    if url is not None:
        return mark_safe(f'<a href="{url}">{value}</a>')
    return value


def to_email(field, value):
    return mark_safe(f'<a href="mailto:{value}">{value}</a>')


def to_url(field, value):
    return mark_safe(
        f'<a href="{value}" target="_blank" rel="noopener noreferrer">{value}</a>'
    )


def to_text(field, value):
    return mark_safe(linebreaks(value))


def to_duration(field, value):
    return mark_safe(":".join(str(value).split(":")[:3]))


def to_boolean(field, value):
    return mark_safe(
        f"<div class='center'>{app_settings.HTML_TRUE if value else app_settings.HTML_FALSE}</div>"
    )


def to_set(field, value):
    return to_iterable(field, value.all())


def to_countries(field, value):
    return to_iterable(field, [c.name for c in value])


def to_iterable(field, iterable):
    return (
        mark_safe("<ul>")
        + format_html_join("\n", "<li>{}</li>", ((str(v),) for v in iterable))
        + mark_safe("</ul>")
    )


def to_richtext(field, value):
    return mark_safe(value)


def to_download(field, value):
    if value:
        return mark_safe(
            f'<a class="center" style="display: block" href="{value.url}"><i class="material-icons">open_in_browser</i></a>'
        )
    return app_settings.HTML_NONE


def to_image(field, value):
    if value:
        im = get_thumbnail(value, "100x100", crop="center", quality=75)
        return mark_safe(
            f'<a class="center" style="display: block" href="{value.url}"><img src={im.url} width="{im.width}" height="{im.height}"/></a>'
        )
    return app_settings.HTML_NONE


DEFAULT_FORMATTERS = {
    models.EmailField: to_email,
    models.fields.files.FieldFile: to_download,
    models.ImageField: to_image,
    models.FileField: to_download,
    models.URLField: to_url,
    models.TextField: to_text,
    models.DurationField: to_duration,
    models.BooleanField: to_boolean,
    models.OneToOneRel: to_one,
    models.ForeignKey: to_one,
    models.ManyToOneRel: to_set,
    models.ManyToManyField: to_set,
    RichTextField: to_richtext,
    RichTextUploadingField: to_richtext,
    CountryField: to_countries,
}
if hasattr(settings, "DEFAULT_FORMATTERS"):
    DEFAULT_FORMATTERS.update(settings.DEFAULT_FORMATTERS)


def render_template(value, context):
    return Template(value.replace("[[", "{{").replace("]]", "}}")).render(
        Context(context)
    )


def html_to_pdf(html, as_http_response=False, name=None):
    # weasyprint is an extra dependency
    import weasyprint

    def url_fetcher(url, timeout=10, ssl_context=None):
        return weasyprint.default_url_fetcher(
            "file://" + url.replace("file://", settings.BASE_DIR), timeout, ssl_context
        )

    ret = weasyprint.HTML(string=html, base_url="", url_fetcher=url_fetcher).write_pdf()
    if as_http_response:
        ret = HttpResponse(ret, content_type="application/pdf")
        ret["Content-Disposition"] = f"inline; filename={name}.pdf"
    return ret


def xlsxresponse(workbook, title):
    workbook = prepare_excel(workbook)
    buf = io.BytesIO()
    workbook.save(buf)
    buf.seek(0)
    response = HttpResponse(buf.read(), content_type="application/vnd.ms-excel")
    response["Content-Disposition"] = f'attachment; filename="{title}.xlsx"'
    return response


# workbook: openpyxl workbook
def prepare_excel(workbook, filter=False):
    # openpyxl is an extra requirement
    from openpyxl.styles import Alignment

    for worksheet in workbook:
        # estimate column width
        for col in worksheet.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            adjusted_width = (max_length + 3) * 1.2
            worksheet.column_dimensions[column].width = min([adjusted_width, 50])

        # enable excel filters
        if filter is True:
            worksheet.auto_filter.ref = f"A1:{column}1"

        # enable word wrap
        for row in worksheet.iter_rows():
            for cell in row:
                cell.alignment = Alignment(wrap_text=True)
                if isinstance(cell.value, str):
                    cell.value = cell.value.strip()
                    if cell.value.isdigit():
                        cell.value = int(cell.value)

    return workbook


def parse_fieldlist(model, fields_parameter, is_form=False):

    # filter fields which cannot be processed in a form
    def form_filter(field):
        field = model._meta.get_field(field)
        return (
            field.editable
            or isinstance(field, GenericForeignKey)
            or field.many_to_many
            or field.one_to_many
        )

    # filter generic foreign key and id field out
    genericfk_exclude = set()
    for f in model._meta.get_fields():
        if isinstance(f, GenericForeignKey):
            genericfk_exclude.add(f.ct_field)
            genericfk_exclude.add(f.fk_field)

    def unwanted_fields_filter(field):
        return field not in genericfk_exclude and field != "id"

    # default configuration: display only direct defined fields on the modle (no reverse related models)
    if "__all__" in fields_parameter:
        __allfields__ = [
            f.name
            for f in model._meta.get_fields()
            if not f.one_to_many and not f.many_to_many
        ]
        i = fields_parameter.index("__all__")
        fields_parameter = (
            fields_parameter[:i] + __allfields__ + fields_parameter[i + 1 :]
        )
    ret = filter(unwanted_fields_filter, fields_parameter)
    if is_form:
        ret = filter(form_filter, ret)
    return list(ret)


# similar to parse_fieldlist but will return django Field instances
def get_modelfields(model, fieldlist):
    fields = []
    modelfields = {f.name: f for f in model._meta.get_fields()}
    modelfields_rel = {
        f.get_accessor_name(): f
        for f in modelfields.values()
        if hasattr(f, "get_accessor_name")
    }
    for field in fieldlist:
        if field in modelfields:
            fields.append(modelfields[field])
        elif field in modelfields_rel:
            fields.append(modelfields_rel[field])
        elif hasattr(model, field):
            fields.append(
                VirtualField(name=field, verbose_name=field.replace("_", " "))
            )
        else:
            raise FieldDoesNotExist(field)
    return fields
