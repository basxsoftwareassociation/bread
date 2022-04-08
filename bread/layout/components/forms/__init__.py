import typing
from typing import List

import htmlgenerator as hg
from django import forms
from django.utils.html import mark_safe
from django.utils.translation import gettext_lazy as _

from ..button import Button
from ..notification import InlineNotification
from .fields import (
    DEFAULT_FORM_CONTEXTNAME,
    DEFAULT_FORMSET_CONTEXTNAME,
    FormField,
    FormFieldMarker,
)
from .helpers import HelpText


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
            hg.WithContext(
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
                *children,
                **{DEFAULT_FORM_CONTEXTNAME: form},
            ),
            **attributes,
        )

    # makes sure that any child elements appended to the form are
    # inside the intermediate context (from WithContext)
    def append(self, obj):
        self[0].append(obj)

    def render(self, context):
        if self.standalone:
            return super().render(context)
        return super().render_children(context)


class FormsetField(hg.Iterator):
    def __init__(
        self,
        fieldname,
        content,
        formname,
        formsetinitial=None,
        **formsetfactory_kwargs,
    ):
        self.fieldname = fieldname
        self.formname = formname
        self.formsetfactory_kwargs = formsetfactory_kwargs
        self.formsetinitial = formsetinitial
        self.content = content
        if isinstance(self.content, FormFieldMarker):
            self.content = hg.BaseElement(self.content)

        # search fields which have explicitly been defined in the content element
        declared_fields = set(
            f.fieldname
            for f in self.content.filter(
                lambda e, ancestors: isinstance(e, FormFieldMarker)
            )
        )

        # append all additional fields of the form which are not rendered explicitly
        # These should be internal, hidden fields (can we test this somehow?)
        self.content.append(
            hg.F(
                lambda c: hg.BaseElement(
                    *[
                        FormField(
                            field,
                            formname=DEFAULT_FORMSET_CONTEXTNAME,
                            no_wrapper=True,
                            no_label=True,
                            no_helptext=True,
                        )
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
            loopvariable=DEFAULT_FORMSET_CONTEXTNAME,
            content=Form(
                hg.C(DEFAULT_FORMSET_CONTEXTNAME), self.content, standalone=False
            ),
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
                        FormField(f, no_wrapper=True, no_label=True, no_helptext=True)
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
                        **{
                            DEFAULT_FORMSET_CONTEXTNAME: hg.C(
                                f"{self.formname}.{self.fieldname}.formset.empty_form"
                            )
                        },
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
            hg.SPAN(
                onload=hg.BaseElement(
                    mark_safe("init_formset('"),
                    hg.C(f"{self.formname}.{self.fieldname}.formset.prefix"),
                    mark_safe("');"),
                ),
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
        fieldname: str,
        fields: List,
        title: typing.Optional[str] = None,
        formname: str = "form",
        formsetfield_kwargs: dict = None,
        **kwargs,
    ) -> hg.BaseElement:
        from ..datatable import DataTable, DataTableColumn

        """
        :param str fieldname: The fieldname which should be used for an
                              formset, in general a one-to-many or many-to-many field
        :param list fields: A list of strings or objects. Strings are converted
                            to DataTableColumn, objects are passed on as they are
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
                f = FormField(f, no_wrapper=True, no_label=True, no_helptext=True)
            if isinstance(f, FormFieldMarker):
                f = DataTableColumn(
                    hg.BaseElement(
                        hg.C(
                            f"{formname}.{fieldname}.formset.form.base_fields.{f.fieldname}.label"
                        ),
                        HelpText(
                            hg.C(
                                f"{formname}.{fieldname}.formset.form.base_fields."
                                f"{f.fieldname}.help_text"
                            )
                        ),
                    ),
                    f,
                )
            columns.append(f)
        columns.append(
            DataTableColumn(
                hg.If(
                    hg.C(f"{formname}.{fieldname}.formset.can_order"),
                    _("Order"),
                ),
                hg.If(
                    hg.C(f"{formname}.{fieldname}.formset.can_order"),
                    FormField(
                        forms.formsets.ORDERING_FIELD_NAME,
                        no_wrapper=True,
                        no_label=True,
                    ),
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
        Show a delete button for the current inline form. This element needs to
        be inside a FormsetField.
        parentcontainerselector: CSS-selector which will be passed to
                                 element.closest in order to select the parent
                                 container which should be hidden on delete.
        """
        defaults = {
            "notext": True,
            "small": True,
            "icon": "trash-can",
            "buttontype": "ghost",
            "onclick": f"delete_inline_element(this.querySelector('input[type=checkbox]'), "
            f"this.closest('{parentcontainerselector}'))",
        }
        defaults.update(kwargs)
        super().__init__(
            label,
            FormField(
                forms.formsets.DELETION_FIELD_NAME,
                style="display: none",
            ),
            **defaults,
        )


class CsrfToken(hg.INPUT):
    def __init__(self):
        super().__init__(
            type="hidden", name="csrfmiddlewaretoken", value=hg.C("csrf_token")
        )
