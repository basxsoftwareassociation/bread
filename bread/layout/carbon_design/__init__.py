from crispy_forms.layout import HTML, Layout
from crispy_forms.utils import TEMPLATE_PACK, render_field
from django.forms.formsets import DELETION_FIELD_NAME
from django.template import Template
from django.template.loader import render_to_string

from ...templatetags.bread_tags import querystring_order, updated_querystring
from ...templatetags.carbon_design_tags import carbon_icon
from ...utils import pretty_fieldname
from ..base import (
    BUTTON,
    DIV,
    INPUT,
    LABEL,
    SPAN,
    TABLE,
    TBODY,
    TD,
    TH,
    THEAD,
    TR,
    A,
    FieldLabel,
    FieldValue,
    HTMLTag,
    ItemContainer,
    NonFormField,
    get_fieldnames,
    with_str_fields_replaced,
)

# key: the common name, used in places where we need an icon independent from the design system
# value: identifier of the icon inside the carbon design system (see materalize_forms design for equivalent definition)
ICONS = {"edit": "edit", "delete": "trash-can"}


class Grid(DIV):
    def __init__(self, *args, grid_mode=None, **kwargs):
        """
        grid_mode can be one of None, "narrow", "condensed"
        """
        kwargs["css_class"] = kwargs.get("css_class", "") + " bx--grid"
        if grid_mode is not None:
            kwargs["css_class"] += f" bx--grid-{grid_mode}"
        super().__init__(*args, **kwargs)


class Row(DIV):
    def __init__(self, *args, **kwargs):
        kwargs["css_class"] = kwargs.get("css_class", "") + " bx--row"
        super().__init__(*args, **kwargs)


class Col(DIV):
    def __init__(self, *args, breakpoint=None, width=None, **kwargs):
        """
        breakpoint: Can be one of "sm", "md", "lg", "xlg", "max"
        """
        colclass = "bx--col"
        if breakpoint is not None:
            assert width is not None, "When breakpoint is given, width is also required"
            colclass += f"-{breakpoint}-{width}"
        kwargs["css_class"] = kwargs.get("css_class", "") + f" {colclass}"
        super().__init__(*args, **kwargs)


class InlineLayout(Layout):
    """Used to render inline forms"""

    def __init__(self, inlinefield, *args, **kwargs):
        super().__init__(inlinefield)
        self.fieldname = inlinefield
        self.wrapper = kwargs.pop("wrapper", DIV())
        self.args = args
        self.kwargs = kwargs

    def get_wrapper_layout(self):
        return self.wrapper

    def get_inline_layout(self):
        if (
            DELETION_FIELD_NAME not in self.args
            and DELETION_FIELD_NAME not in self.kwargs
        ):
            self.args = self.args + (DELETION_FIELD_NAME, "id")
        return Layout(*self.args, **self.kwargs)


class ObjectActionsDropDown(HTMLTag):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.field = ""
        self.fields = []
        self.template = Template(
            """
{% load bread_tags carbon_design_tags %}
{% object_actions view.admin request object as actions %}
{% if actions %}
<div data-overflow-menu role="menu" tabindex="0" aria-label="Actions" aria-expanded="false"class="bx--overflow-menu">
    {% carbon_icon "overflow-menu--vertical" 16 class="bx--overflow-menu__icon" %}
    <ul class="bx--overflow-menu-options bx--overflow-menu--flip">
        {% for action in actions %}
            <li class="bx--overflow-menu-options__option bx--table-row--menu-option">
                <button class="bx--overflow-menu-options__btn" onclick="window.location.href='{% linkurl action %}'">
                    <div class="bx--overflow-menu-options__option-content">
                        {% if action.icon %}
                            {% carbon_icon action.icon 16 %}
                        {% endif %}{{ action.label }}
                    </div>
                </button>
            </li>
        {% endfor %}
    </ul>
</div>
{% endif %}
    """
        )

    def render(self, form, form_style, context, template_pack=TEMPLATE_PACK, **kwargs):
        return self.template.render(context)


def default_list_layout(fieldnames, sortable_by):
    checkbox = TD(
        INPUT(
            data_event="select",
            css_class="bx--checkbox",
            type="checkbox",
            value="select",
            name="select",
        ),
        LABEL(css_class="bx--checkbox-label"),
        css_class="bx--table-column-checkbox",
    )
    fields = with_str_fields_replaced(
        Layout(
            TR(
                checkbox,
                *[TD(f) for f in fieldnames],
                TD(ObjectActionsDropDown(), css_class="bx--table-column-menu"),
            )
        ),
        layout_generator=lambda f: FieldValue(f),
    )
    headers = [
        TH(
            INPUT(
                data_event="select-all",
                id=f"bx--checkbox-{id(fields)}",
                css_class="bx--checkbox",
                type="checkbox",
                value="select-all",
                name="select-all",
            ),
            LABEL(_for=f"bx--checkbox-{id(fields)}", css_class="bx--checkbox-label"),
            css_class="bx--table-column-checkbox",
        )
    ]
    for fieldname in fieldnames:
        if fieldname in sortable_by:
            headers.append(TH(SortableHeader(fieldname)))
        else:
            headers.append(
                TH(SPAN(FieldLabel(fieldname), css_class="bx--table-header-label"))
            )
    headers.append(TH(css_class="bx--table-column-menu"))  # action-dropdown column

    return Layout(
        TABLE(
            THEAD(TR(*headers)),
            TBODY(ItemContainer("object_list", "object", fields)),
            css_class="bx--data-table bx--data-table--sort",
        )
    )


class SortableHeader(NonFormField):
    def __init__(self, field, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.field = field

    def render(self, form, form_style, context, template_pack=TEMPLATE_PACK, **kwargs):
        order = context.get("request").GET.get("order", "")
        href = updated_querystring(
            context, "order", querystring_order(order, self.field),
        )
        icon_asc = carbon_icon("ArrowUp", 16, **{"class": "bx--table-sort__icon"})
        icon_unsorted = carbon_icon(
            "ArrowsVertical", 16, **{"class": "bx--table-sort__icon-unsorted"}
        )
        sortascending = "-" + self.field in order
        sortactive = sortascending or self.field in order
        return render_field(
            BUTTON(
                SPAN(FieldLabel(self.field), css_class="bx--table-header-label",),
                HTML(icon_asc),
                HTML(icon_unsorted),
                css_class="bx--table-sort"
                + (" bx--table-sort--active" if sortactive else "")
                + (" bx--table-sort--ascending" if sortascending else ""),
                data_event="sort",
                onclick=f'location.href="{href}"',
            ),
            {},
            None,
            context,
        )
