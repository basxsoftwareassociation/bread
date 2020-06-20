import io
import os

import ffmpeg
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import FieldDoesNotExist
from django.http import HttpResponse
from django.template import Context, Template

from .fields import VirtualField


def pretty_fieldname(field):
    if field.is_relation and field.one_to_many:
        return field.target_field.model._meta.verbose_name_plural.title()
    elif field.is_relation and field.many_to_many and field.auto_created:
        return (
            getattr(
                field.target_field,
                "related_name",
                field.related_model._meta.verbose_name_plural.title(),
            )
            .replace("_", " ")
            .title()
        )
    elif field.is_relation and field.one_to_one:
        return field.target_field.model._meta.verbose_name.title()
    elif isinstance(field, GenericForeignKey):
        return field.name.replace("_", " ").title()
    else:
        return field.verbose_name.title()


def has_permission(user, operation, instance):
    """
        instance: can be model instance or a model
        operation is one of ["view", "add", "change", "delete"] (django defaults)
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


def render_template(value, context):
    """
    Renders a template text with values:
    [[ XXX ]] will be replace with context["XXX"]
    Used to work with CKEditor template tags
    """
    return Template(value.replace("[[", "{{").replace("]]", "}}")).render(
        Context(context)
    )


def html_to_pdf(html, as_http_response=False, name=None):
    """
    Renders html to PDF

        html: html string
        as_http_response: If True return PDF as HttpResponse with attachment
        name: Filename without extension, only used when as_http_response == True
        returns: PDF content or HttpResponse with attachment
    """
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
    """
    Returns workbook as a downloadable file

        workbook: openpyxl workbook
        title: filename without extension
        returns: HttpResponse with attachment
    """
    workbook = prepare_excel(workbook)
    buf = io.BytesIO()
    workbook.save(buf)
    buf.seek(0)
    response = HttpResponse(buf.read(), content_type="application/vnd.ms-excel")
    response["Content-Disposition"] = f'attachment; filename="{title}.xlsx"'
    return response


def prepare_excel(workbook, filter=False):
    """
    Formats the excel a bit in order to be displayed nicely

        workbook: openpyxl workbook
        filter: If True enable excel filtering headers
        returns: formated workbook
    """
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
        modelfields = {
            f.get_accessor_name() if hasattr(f, "get_accessor_name") else f.name: f
            for f in model._meta.get_fields(include_hidden=True)
        }
        if field not in modelfields:
            return False
        field = modelfields[field]
        return (
            field.editable
            or isinstance(field, GenericForeignKey)
            or field.many_to_many
            or field.one_to_many
            or field.one_to_one,
        )

    # filter generic foreign key and id field out
    genericfk_exclude = set()
    for f in model._meta.get_fields():
        if isinstance(f, GenericForeignKey):
            genericfk_exclude.add(f.ct_field)
            genericfk_exclude.add(f.fk_field)

    def unwanted_fields_filter(field):
        modelfield = {
            f.get_accessor_name() if hasattr(f, "get_accessor_name") else f.name: f
            for f in model._meta.get_fields()
        }.get(field)
        # do not include the one-to-one field to a parent-model table
        if (
            hasattr(modelfield, "remote_field")
            and modelfield.remote_field
            and getattr(modelfield.remote_field, "parent_link", False) is True
        ):
            return False
        return field not in genericfk_exclude and field != "id"

    # default configuration: display only direct defined fields on the modle (no reverse related models)
    if "__all__" in fields_parameter:
        concrete_fields = [f.name for f in model._meta.get_fields() if f.concrete]
        i = fields_parameter.index("__all__")
        fields_parameter = (
            fields_parameter[:i] + concrete_fields + fields_parameter[i + 1 :]
        )
    ret = filter(unwanted_fields_filter, fields_parameter)
    if is_form:
        ret = filter(form_filter, ret)
    return list(ret)


# similar to parse_fieldlist but will return django Field instances
def get_modelfields(model, fieldlist, admin=None):
    fields = {}
    modelfields = {f.name: f for f in model._meta.get_fields()}
    modelfields_rel = {
        f.get_accessor_name(): f
        for f in modelfields.values()
        if hasattr(f, "get_accessor_name")
    }
    for field in fieldlist:
        if field in modelfields:
            fields[field] = modelfields[field]
        elif field in modelfields_rel:
            fields[field] = modelfields_rel[field]
        elif hasattr(model, field) or hasattr(admin, field):
            fields[field] = VirtualField(
                name=field, verbose_name=field.replace("_", " ")
            )
        else:
            raise FieldDoesNotExist(field)
        if isinstance(fields[field], GenericForeignKey):
            fields[field].sortable = False
    return fields


def get_audio_thumbnail(file_):
    # TODO: make this working with any storage (not only local disk)
    """Generate audio mp3 which can be played in all browsers.
    """
    thumbnail_name = file_.name + "_thumbnail.mp3"
    inputname = os.path.join(settings.MEDIA_ROOT, file_.name)
    outputname = os.path.join(settings.MEDIA_ROOT, thumbnail_name)
    outputurl = os.path.join(settings.MEDIA_URL, thumbnail_name)
    if not os.path.exists(outputname):
        ffmpeg.input(inputname).filter("atrim", start=0, duration=60).output(
            outputname, format="mp3", audio_bitrate=64
        ).run()
    return outputurl


def get_video_thumbnail(file_):
    # TODO: make this working with any storage (not only local disk)
    """Generate video mp3 which can be played in all browsers.
    """
    thumbnail_name = file_.name + "_thumbnail.mp4"
    inputname = os.path.join(settings.MEDIA_ROOT, file_.name)
    outputname = os.path.join(settings.MEDIA_ROOT, thumbnail_name)
    outputurl = os.path.join(settings.MEDIA_URL, thumbnail_name)
    if not os.path.exists(outputname):
        _in = ffmpeg.input(inputname)
        v = _in.video
        a = _in.audio
        ffmpeg.output(
            v.trim(start=0, duration=60).filter("scale", 200, -2),
            a.filter("atrim", start=0, duration=60),
            outputname,
            preset="ultrafast",
            acodec="mp3",
            audio_bitrate=64,
        ).run()
    return outputurl


def title(label):
    if label and label[0].islower():
        return label.title()
    return label
