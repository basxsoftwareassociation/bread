import htmlgenerator as hg
from django.utils.translation import gettext_lazy as _

from basxbread.utils import get_all_subclasses

from .button import Button

_CACHE = {}


def field_help(model, max_depth=3):
    if model not in _CACHE:
        _CACHE[model] = hg.mark_safe(
            hg.render(
                hg.BaseElement(
                    hg.DIV(
                        hg.format(_("Base model: ")),
                        model._meta.verbose_name,
                        style="margin-top: 2rem",
                    ),
                    hg.DIV(
                        _("Click "),
                        hg.SPAN(
                            " ... ",
                            style="width: 1rem; height: 1rem; background-color: lightgray;",
                        ),
                        " ",
                        _(" to copy the accessor"),
                        style="margin-top: 2rem",
                    ),
                    hg.DIV(_("Fields"), style="margin-top: 2rem"),
                    hg.DIV(
                        get_field_list(
                            model,
                            max_depth,
                            list(
                                set(
                                    [
                                        model,
                                        model.__mro__[-3],
                                        *get_all_subclasses(model.__mro__[-3]),
                                    ]
                                )
                            ),
                            display="block",
                        ),
                        style="line-height: 2rem",
                    ),
                ),
                {},
            )
        )
    return _CACHE[model]


def get_field_list(model, depth, excludemodels, display="none", parent_accessor=[]):
    fields = {}
    for f in model._meta.get_fields():
        # if not f.concrete and (f.one_to_many or f.many_to_many):
        # continue
        fields[f] = hg.DIV(
            hg.SPAN(
                ".".join(parent_accessor + [_field_attname(f)]),
                style="display:none;"
                "position: absolute;"
                "top: -2rem;"
                "background-color: white;"
                "padding: 0.25rem",
            ),
            hg.SPAN(
                " ... ",
                style="width: 1rem; height: 1rem; background-color: lightgray; cursor: pointer;",
                onmouseover="this.previousElementSibling.style.display = 'block'",
                onmouseout="this.previousElementSibling.style.display = 'none'",
                onclick="navigator.clipboard.writeText(this.previousElementSibling.innerText);",
            ),
            " ",
            hg.SPAN(
                hg.SPAN(_field_attname(f), style="font-weight: 700"),
                " ",
                _field_type_repr(f),
            ),
            style="position: relative",
        )
        if (
            f.related_model
            and not f.many_to_many
            and f.related_model not in excludemodels
            and depth > 0
        ):
            fields[f].append(
                Button(
                    buttontype="ghost",
                    icon="chevron--down",
                    onclick=_js_toggle_display("this.nextElementSibling"),
                )
            )
            fields[f].append(
                get_field_list(
                    f.related_model,
                    depth - 1,
                    excludemodels + [model],
                    parent_accessor=parent_accessor + [_field_attname(f)],
                )
            )
    return hg.UL(
        hg.Iterator(
            sorted(
                fields.items(),
                key=lambda k: ("1" if k[0].related_model else "0")
                + _field_attname(k[0]),
            ),
            "field",
            hg.LI(hg.C("field.1")),
        ),
        style=f"margin-left: 2rem; display: {display}",
    )


def _field_type_repr(field):
    from django.contrib.contenttypes.fields import GenericForeignKey

    if field.related_model:
        if field.one_to_one or field.many_to_one:
            return _(' reference to "%s"') % field.related_model._meta.verbose_name
        if field.one_to_many or field.many_to_many:
            return (
                _(' reference to multiple "%s"')
                % field.related_model._meta.verbose_name_plural
            )
    if isinstance(field, GenericForeignKey):
        return f"{type(field).__name__}"

    return f"{type(field).__name__}({field.verbose_name})"


def _field_attname(field):
    attname = field.name
    if hasattr(field, "attname"):
        attname = field.attname
    elif hasattr(field, "get_accessor_name"):
        attname = field.get_accessor_name()
    if attname.endswith("_id"):
        attname = attname[:-3]
    return attname


def _js_toggle_display(element_accessor):
    return (
        f"{element_accessor}.style.display = "
        f"{element_accessor}.style.display == 'none' ? 'block': 'none'"
    )
