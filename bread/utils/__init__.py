from .export import html_to_pdf, prepare_excel, render_template, xlsxresponse
from .media import get_audio_thumbnail, get_video_thumbnail
from .model_helpers import (
    filter_fieldlist,
    get_modelfields,
    has_permission,
    pretty_fieldname,
    resolve_relationship,
    title,
)
from .views import generate_path_for_view

__all__ = [
    "get_video_thumbnail",
    "get_audio_thumbnail",
    "has_permission",
    "pretty_fieldname",
    "title",
    "filter_fieldlist",
    "get_modelfields",
    "resolve_relationship",
    "html_to_pdf",
    "prepare_excel",
    "xlsxresponse",
    "render_template",
    "generate_path_for_view",
]


def try_call(var, *args, **kwargs):
    return var(*args, **kwargs) if callable(var) else var
