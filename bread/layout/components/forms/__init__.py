import htmlgenerator as hg
from django import forms
from django.utils.html import mark_safe
from django.utils.translation import gettext_lazy as _

from ..button import Button
from ..notification import InlineNotification
from .fields import BaseWidget, FormField, FormFieldMarker  # noqa


class Form(hg.FORM):
    def __init__(self, form, *children, use_csrf=True, standalone=True, **kwargs):
        """
        form: lazy evaluated value which should resolve to the form object
        children: any child elements, can be formfields or other
        use_csrf: add a CSRF input, but only for POST submission and standalone forms
        standalone: if true, will add a CSRF token and will render enclosing FORM-element
        """
        self.standalone = standalone
        attributes = {"method": "POST", "autocomplete": "off"}
        attributes.update(kwargs)
        if (
            attributes["method"].upper() == "POST"
            and use_csrf is not False
            and standalone is True
        ):
            children = (CsrfToken(),) + children

        if self.standalone and "enctype" not in attributes:
            # note: We will always use "multipart/form-data" instead of the
            # default "application/x-www-form-urlencoded" inside bread. We do
            # this because forms with file uploads require multipart/form-data.
            # Not distinguishing between two encoding types can save us some issues,
            # especially when handling files.
            # The only draw back with this is a slightly larger payload because
            # multipart-encoding takes a little bit more space
            attributes["enctype"] = "multipart/form-data"

        super().__init__(
            # generic errors
            hg.If(
                form.non_field_errors(),
                hg.Iterator(
                    form.non_field_errors(),
                    "formerror",
                    InlineNotification(
                        _("Form error"), hg.C("formerror"), kind="error"
                    ),
                ),
            ),
            # errors from hidden fields
            hg.If(
                form.hidden_fields(),
                hg.Iterator(
                    form.hidden_fields(),
                    "hiddenfield",
                    hg.Iterator(
                        hg.C("hiddenfield").errors,
                        "hiddenfield_error",
                        InlineNotification(
                            _("Hidden field error: "),
                            hg.format(
                                "{}: {}",
                                hg.C("hiddenfield").name,
                                hg.C("hiddenfield_error"),
                            ),
                            kind="error",
                        ),
                    ),
                ),
            ),
            hg.WithContext(*children, _bread_form=form),
            **attributes,
        )

    def render(self, context):
        if self.standalone:
            return super().render(context)
        return super().render_children(context)


class FormChild:
    """Used to mark elements which need the "form" attribute set by the parent form before rendering"""


class FormField1(FormChild, hg.BaseElement):
    """Dynamic element which will resolve the field with the given name
    and return the correct HTML, based on the widget of the form field or on the passed argument 'fieldtype'"""

    def __init__(
        self,
        fieldname,
        fieldtype=None,
        hidelabel=False,
        elementattributes=None,
        widgetattributes=None,
        formname="form",
    ):
        if fieldtype is not None and not isinstance(fieldtype, type):
            raise ValueError("argument 'fieldtype' is not a type")
        self.fieldname = fieldname
        self.fieldtype = fieldtype
        self.widgetattributes = widgetattributes or {}
        self.elementattributes = elementattributes or {}
        self.hidelabel = hidelabel
        self.form = None  # will be set by the render method of the parent method
        self.formname = formname  # in the future we should only depend on the formname to extract the form from the context

    def render(self, context):
        form = self.form or hg.resolve_lazy(context[self.formname], context)
        element = _mapwidget(
            form[self.fieldname],
            self.fieldtype,
            self.elementattributes,
            self.widgetattributes,
        )
        if self.hidelabel:
            element.replace(
                lambda e, ancestors: isinstance(e, hg.LABEL), None, all=True
            )
        return element.render(context)


class FormsetField(hg.Iterator):
    def __init__(
        self,
        fieldname,
        content,
        formname="form",
        formsetinitial=None,
        **formsetfactory_kwargs,
    ):
        self.fieldname = fieldname
        self.formname = formname
        self.formsetfactory_kwargs = formsetfactory_kwargs  # used in bread.forms.forms._generate_formset_class, maybe refactor this?
        self.formsetinitial = formsetinitial  # used in bread.forms.forms._generate_formset_class, maybe refactor this?
        self.content = content
        if isinstance(self.content, FormField):
            self.content = hg.BaseElement(self.content)

        # search fields which have explicitly been defined in the content element
        declared_fields = set(
            f.fieldname
            for f in self.content.filter(
                lambda e, ancestors: isinstance(e, FormField) and e.is_djangoformfield
            )
        )

        # append all additional fields of the form which are not rendered explicitly
        # These should be internal, hidden fields (can we test this somehow?)
        self.content.append(
            hg.F(
                lambda c: hg.BaseElement(
                    *[
                        FormField(field, formname="formset_form")
                        for field in c[self.formname][
                            self.fieldname
                        ].formset.empty_form.fields
                        if field not in declared_fields
                        and field != forms.formsets.DELETION_FIELD_NAME
                    ]
                )
            )
        )

        super().__init__(
            iterator=hg.C(f"{self.formname}.{self.fieldname}.formset"),
            loopvariable="formset_form",
            content=Form(hg.C("formset_form"), self.content, standalone=False),
        )

    @property
    def management_form(self):
        # the management form is required for Django formsets
        return hg.BaseElement(
            # management forms, for housekeeping of inline forms
            hg.F(
                lambda c: Form(
                    c[self.formname][self.fieldname].formset.management_form,
                    *[
                        FormField(f)
                        for f in c[self.formname][
                            self.fieldname
                        ].formset.management_form.fields
                    ],
                    standalone=False,
                )
            ),
            # Empty form as template for new entries. The script tag works very well
            # for this since we need a single, raw, unescaped HTML string
            hg.SCRIPT(
                Form(
                    hg.C(f"{self.formname}.{self.fieldname}.formset.empty_form"),
                    hg.WithContext(
                        self.content,
                        formset_form=hg.C(
                            f"{self.formname}.{self.fieldname}.formset.empty_form"
                        ),
                    ),
                    standalone=False,
                ),
                id=hg.BaseElement(
                    "empty_",
                    hg.C(f"{self.formname}.{self.fieldname}.formset.prefix"),
                    "_form",
                ),
                type="text/plain",
            ),
            hg.SCRIPT(
                mark_safe(
                    "document.addEventListener('DOMContentLoaded', e => init_formset('"
                ),
                hg.C(f"{self.formname}.{self.fieldname}.formset.prefix"),
                mark_safe("'));"),
            ),
        )

    def add_button(self, container_css_selector, label=_("Add"), **kwargs):
        prefix = hg.C(f"{self.formname}.{self.fieldname}.formset.prefix")
        defaults = {
            "icon": "add",
            "notext": True,
            "buttontype": "tertiary",
            "id": hg.BaseElement(
                "add_", prefix, "_button"
            ),  # required for javascript to work correctly
            "onclick": hg.BaseElement(
                "formset_add('",
                prefix,
                "', '",
                container_css_selector,
                "');",
            ),
        }
        return Button(label, **{**defaults, **kwargs})

    @staticmethod
    def as_plain(*args, add_label=_("Add"), **kwargs):
        """Shortcut to render a complete formset with add-button"""
        formset = FormsetField(*args, **kwargs)
        id = hg.html_id(formset, prefix="formset-")
        return hg.BaseElement(
            hg.DIV(formset, id=id),
            formset.management_form,
            formset.add_button(
                buttontype="ghost",
                notext=False,
                label=add_label,
                container_css_selector=f"#{id}",
            ),
        )

    @staticmethod
    def as_datatable(
        fieldname,
        fields,
        title=None,
        formname="form",
        formsetfield_kwargs=None,
        **kwargs,
    ):
        from ..datatable import DataTable, DataTableColumn

        """
        :param str fieldname: The fieldname which should be used for an formset, in general a one-to-many or many-to-many field
        :param list fields: A list of strings or objects. Strings are converted to DataTableColumn, objects are passed on as they are
        :param str title: Datatable title, automatically generated from form if None
        :param str formname: Name of the surounding django-form object in the context
        :param dict formsetfield_kwargs: Arguments to be passed to the FormSetField constructor
        :param kwargs: Arguments to be passed to the DataTable constructor
        :return: A datatable with inline-editing capabilities
        :rtype: hg.HTMLElement
        """

        columns = []
        for f in fields:
            if isinstance(f, str):
                f = DataTableColumn(
                    hg.C(f"{formname}.{fieldname}.formset.form.base_fields.{f}.label"),
                    FormField(f, hidelabel=True),
                )
            columns.append(f)
        columns.append(
            DataTableColumn(
                _("Order"),
                hg.If(
                    hg.C(f"{formname}.{fieldname}.formset.can_order"),
                    FormField(forms.formsets.ORDERING_FIELD_NAME, hidelabel=True),
                ),
            )
        )
        columns.append(
            DataTableColumn(
                "",
                hg.If(
                    hg.C(f"{formname}.{fieldname}.formset.can_delete"),
                    InlineDeleteButton(parentcontainerselector="tr"),
                ),
            )
        )

        formset = FormsetField(
            fieldname,
            DataTable.row(columns),
            formname=formname,
            **(formsetfield_kwargs or {}),
        )
        id = hg.html_id(formset, prefix="formset-")

        return hg.BaseElement(
            DataTable(
                row_iterator=formset,
                rowvariable="",
                columns=columns,
                id=id,
                **kwargs,
            ).with_toolbar(
                title=title or hg.C(f"{formname}.{fieldname}.label"),
                primary_button=formset.add_button(
                    buttontype="primary", container_css_selector=f"#{id} tbody"
                ),
            ),
            formset.management_form,
        )


class InlineDeleteButton(Button):
    def __init__(self, parentcontainerselector, label=_("Delete"), **kwargs):
        """
        Show a delete button for the current inline form. This element needs to be inside a FormsetField
        parentcontainerselector: CSS-selector which will be passed to element.closest in order to select the parent container which should be hidden on delete
        """
        defaults = {
            "notext": True,
            "small": True,
            "icon": "trash-can",
            "buttontype": "ghost",
            "onclick": f"delete_inline_element(this.querySelector('input[type=checkbox]'), this.closest('{parentcontainerselector}'))",
        }
        defaults.update(kwargs)
        super().__init__(
            label,
            FormField(
                forms.formsets.DELETION_FIELD_NAME,
                elementattributes={"style": "display: none"},
            ),
            **defaults,
        )


class HiddenInput(FormChild, hg.INPUT):
    def __init__(self, fieldname, widgetattributes, boundfield=None, **attributes):
        self.fieldname = fieldname
        super().__init__(type="hidden", **{**widgetattributes, **attributes})

        if boundfield is not None:
            self.attributes["id"] = boundfield.auto_id
        if boundfield is not None:
            self.attributes["name"] = boundfield.html_name
            if boundfield.value() is not None:
                self.attributes["value"] = boundfield.value()


class CsrfToken(FormChild, hg.INPUT):
    def __init__(self):
        super().__init__(
            type="hidden", name="csrfmiddlewaretoken", value=hg.C("csrf_token")
        )


def _mapwidget(
    field, fieldtype, elementattributes=None, widgetattributes=None, only_initial=False
):
    from .checkbox import Checkbox  # done
    from .date_picker import DatePicker  # done
    from .file_uploader import FileUploader  # done
    from .multiselect import MultiSelect
    from .select import Select  # done
    from .text_area import TextArea  # done
    from .text_input import EmailInput  # done
    from .text_input import PasswordInput  # done
    from .text_input import PhoneNumberInput  # done
    from .text_input import TextInput  # done
    from .text_input import UrlInput  # done

    widgetattributes = update_widgetattributes(field, only_initial, widgetattributes)
    elementattributes = {
        "label": field.label,
        "help_text": field.help_text,
        "errors": field.errors,
        "disabled": field.field.disabled,
        "required": field.field.required,
        **getattr(field.field, "layout_kwargs", {}),
        **(elementattributes or {}),
    }

    if fieldtype and not isinstance(field.field.widget, forms.HiddenInput):
        return fieldtype(
            fieldname=field.name,
            widgetattributes=widgetattributes,
            boundfield=field,
            **elementattributes,
        )

    if isinstance(field.field.widget, forms.CheckboxInput):
        widgetattributes["checked"] = field.value()
        return hg.DIV(
            Checkbox(
                widgetattributes=widgetattributes,
                **elementattributes,
            ),
            _class="bx--form-item",
        )

    if isinstance(field.field.widget, forms.CheckboxSelectMultiple):
        del elementattributes["label"]
        del elementattributes["required"]

        return hg.DIV(
            *[
                Checkbox(
                    **elementattributes,
                    label=widget.data["label"],
                    widgetattributes={
                        **widgetattributes,
                        "name": widget.data["name"],
                        "value": widget.data["value"],
                        "checked": widget.data["selected"],
                        **widget.data["attrs"],
                    },
                )
                for widget in field.subwidgets
            ],
            _class="bx--form-item",
        )

    if isinstance(field.field.widget, forms.Select):
        # This is to prevent rendering extrem long lists of database entries
        # (e.g. all persons) for relational fields if the field is disabled.
        if isinstance(field.field.widget, forms.SelectMultiple):
            if field.field.disabled and hasattr(field.field, "queryset"):
                field.field.queryset = field.field.queryset.filter(
                    pk__in=[i.pk for i in field.form.initial.get(field.name)]
                )
            return hg.DIV(
                MultiSelect(
                    field.field.widget.optgroups(
                        field.name,
                        field.field.widget.get_context(field.name, field.value(), {})[
                            "widget"
                        ]["value"],
                    ),
                    widgetattributes=widgetattributes,
                    **elementattributes,
                ),
                _class="bx--form-item",
            )
        if field.field.disabled and hasattr(field.field, "queryset"):
            default = field.form.initial.get(field.name) or None
            field.field.queryset = field.field.queryset.filter(
                pk=getattr(default, "pk", default)
            )
        return hg.DIV(
            Select(
                field.field.widget.optgroups(
                    field.name,
                    field.field.widget.get_context(field.name, field.value(), {})[
                        "widget"
                    ]["value"],
                ),
                widgetattributes=widgetattributes,
                **elementattributes,
            ),
            _class="bx--form-item",
        )

    WIDGET_MAPPING = {
        forms.TextInput: TextInput,
        # Attention: NumberInput is not the widget that is used for phone numbers. See below for handling of phone numbers
        forms.NumberInput: TextInput,
        forms.EmailInput: EmailInput,
        forms.URLInput: UrlInput,
        forms.PasswordInput: PasswordInput,
        forms.HiddenInput: HiddenInput,
        forms.DateInput: DatePicker,
        forms.DateTimeInput: TextInput,  # TODO
        forms.TimeInput: TextInput,  # TODO HIGH
        forms.Textarea: TextArea,
        forms.CheckboxInput: Checkbox,
        forms.NullBooleanSelect: Select,
        forms.SelectMultiple: MultiSelect,
        forms.RadioSelect: TextInput,  # TODO HIGH
        forms.FileInput: FileUploader,
        forms.ClearableFileInput: FileUploader,  # TODO HIGH
        forms.MultipleHiddenInput: TextInput,  # TODO
        forms.SplitDateTimeWidget: TextInput,  # TODO
        forms.SplitHiddenDateTimeWidget: TextInput,  # TODO
        forms.SelectDateWidget: TextInput,  # TODO
    }

    fieldtype = (
        getattr(field.field, "layout", None)
        # needs to be above the WIDGET_MAPPING, because the field.field.widget is a forms.TextInput which would match
        or (
            PhoneNumberInput
            if hasattr(field.field.widget, "input_type")
            and field.field.widget.input_type == "tel"
            else None
        )
        or WIDGET_MAPPING[type(field.field.widget)]
    )
    if isinstance(fieldtype, type) and issubclass(fieldtype, hg.BaseElement):
        ret = fieldtype(
            fieldname=field.name,
            widgetattributes=widgetattributes,
            boundfield=field,
            **elementattributes,
        )
    else:
        ret = hg.DIV(f"Field {field.name}")

    if (
        field.field.show_hidden_initial and fieldtype != HiddenInput
    ):  # special case, prevent infinte recursion
        return hg.BaseElement(
            ret,
            _mapwidget(field, HiddenInput, only_initial=True),
        )

    return ret


def update_widgetattributes(field, only_initial, widgetattributes):
    # TODO: This can be simplified, and improved
    widgetattributes = widgetattributes or {}
    attrs = dict(field.field.widget.attrs)
    attrs.update(widgetattributes)
    attrs = field.build_widget_attrs(attrs)
    if getattr(field.field.widget, "allow_multiple_selected", False):
        attrs["multiple"] = True
    if field.auto_id and "id" not in field.field.widget.attrs:
        attrs.setdefault("id", field.html_initial_id if only_initial else field.auto_id)
    if "name" not in attrs:
        attrs["name"] = field.html_initial_name if only_initial else field.html_name
    value = field.field.widget.format_value(field.value())
    if value is not None and "value" not in attrs:
        attrs["value"] = value
    return attrs
