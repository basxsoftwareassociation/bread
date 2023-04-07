import shutil

from django.apps import AppConfig
from django.core.checks import Warning, register
from django.utils.translation import gettext_lazy as _


class DocumentTemplatesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "basxbread.contrib.document_templates"
    verbose_name = _("Document templates")


@register()
def libreoffice_check(app_configs, **kwargs):
    warnings = []
    has_libreoffice = shutil.which("libreoffice") is not None
    if not has_libreoffice:
        warnings.append(
            Warning(
                "the 'libreoffice' executable could not be found",
                hint="Generating PDFs will not work. Install libreoffice-writer-nogui (recommended) to enable this functionality.",
                id="document_templates.W001",
            )
        )
    return warnings
