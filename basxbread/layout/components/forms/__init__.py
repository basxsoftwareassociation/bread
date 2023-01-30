from typing import List, Optional

import htmlgenerator as hg
from django import forms
from django.utils.html import mark_safe
from django.utils.translation import gettext_lazy as _

from ..button import Button
from ..notification import InlineNotification
from .fields import DEFAULT_FORM_CONTEXTNAME, FormField, FormFieldMarker
from .helpers import HelpText, Submit  # noqa


class Form(hg.FORM):
    def __init__(
        self,
        form,
        *children,
        use_csrf=True,
        standalone=True,
        formname=None,
        **kwargs,
    ):
        """
        form: lazy evaluated value which should resolve to the form object
        children: any child elements, can be formfields or other
        use_csrf: add a CSRF input, but only for POST submission and standalone forms
        standalone: if true, will add a CSRF token and will render enclosing FORM-element
        """
        formname = formname or DEFAULT_FORM_CONTEXTNAME
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
            # default "application/x-www-form-urlencoded" inside basxbread. We do
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
                **{formname: form, DEFAULT_FORM_CONTEXTNAME: form},
            ),
            **attributes,
        )

    # makes sure that any child elements appended to the form are
    # inside the intermediate context (from WithContext)
    def append(self, obj):
        self[0].append(obj)

    def render(self, context, stringify=True, fragment=None):
        if self.standalone:
            return super().render(context, stringify=stringify, fragment=fragment)
        return super().render_children(context, stringify=stringify, fragment=fragment)


class Formset(hg.Iterator):
    def __init__(
        self,
        formset,
        content,
        formsetinitial=None,
        fieldname=None,  # required for inline-formsets
        **formsetfactory_kwargs,
    ):
        self.formset = formset
        if fieldname is not None:
            self.fieldname = fieldname
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
                            formname=DEFAULT_FORM_CONTEXTNAME,
                            no_wrapper=True,
                            no_label=True,
                            no_helptext=True,
                        )
                        for field in hg.resolve_lazy(self.formset, c).empty_form.fields
                        if field not in declared_fields
                        and field != forms.formsets.DELETION_FIELD_NAME
                    ]
                )
            )
        )

        super().__init__(
            iterator=self.formset,
            loopvariable="__current_formset_form",
            content=Form(
                hg.C("__current_formset_form"), self.content, standalone=False
            ),
        )

    @property
    def management_form(self):
        # the management form is required for Django formsets
        def lazy_form(context):
            form = hg.resolve_lazy(self.formset, context).management_form
            return Form(
                form,
                *[
                    FormField(f, no_wrapper=True, no_label=True, no_helptext=True)
                    for f in form.fields
                ],
                standalone=False,
            )

        return hg.BaseElement(
            # management forms, for housekeeping of inline forms
            hg.F(lazy_form),
            # Empty form as template for new entries. The script tag works very well
            # for this since we need a single, raw, unescaped HTML string
            hg.SCRIPT(
                Form(
                    self.formset.empty_form,
                    hg.WithContext(
                        self.content,
                        **{DEFAULT_FORM_CONTEXTNAME: self.formset.empty_form},
                    ),
                    standalone=False,
                ),
                id=hg.BaseElement(
                    "empty_",
                    self.formset.prefix,
                    "_form",
                ),
                type="text/plain",
            ),
            hg.SCRIPT(
                hg.format(
                    mark_safe(
                        "document.addEventListener('DOMContentLoaded', e => init_formset('{}'))"
                    ),
                    self.formset.prefix,
                ),
            ),
            hg.SPAN(onload=hg.format("init_formset('{}')", self.formset.prefix)),
        )

    def add_button(self, container_css_selector, label=_("Add"), **kwargs):
        prefix = self.formset.prefix
        defaults = {
            "icon": "add",
            "notext": True,
            "buttontype": "tertiary",
            "id": hg.format("add_{}_button", prefix),
        }
        click_arg = {
            "onclick": hg.format(
                "formset_add('{}', '{}')", prefix, container_css_selector
            ),
        }
        return Button(label, **{**defaults, **hg.merge_html_attrs(click_arg, kwargs)})

    @staticmethod
    def as_plain(formset, content, add_label=_("Add"), **kwargs):
        """Shortcut to render a complete formset with add-button"""
        formset = Formset(formset, content, **kwargs)
        id = hg.html_id(formset, prefix="formset-")
        return hg.BaseElement(
            hg.If(
                formset.non_form_errors(),
                hg.Iterator(
                    formset.non_form_errors(),
                    "formerror",
                    InlineNotification(
                        _("Form error"), hg.C("formerror"), kind="error"
                    ),
                ),
            ),
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
    def as_inline_datatable(
        fieldname: str, fields: List, outerform_name: str = "form", **kwargs
    ):
        """when used in view the outerform_name can be "form" as it is set in the context by the view for the top-level form"""
        return Formset.as_datatable(
            formset=hg.C(outerform_name)[fieldname].formset,
            fields=fields,
            title=hg.C(outerform_name)[fieldname].label,
            fieldname=fieldname,
            **kwargs,
        )

    @staticmethod
    def as_datatable(
        formset,
        fields: List,
        title: Optional[str] = None,
        formsetfield_kwargs: Optional[dict] = None,
        fieldname=None,  # required for inline-formsets
        can_add=True,
        **kwargs,
    ) -> hg.BaseElement:
        from ..datatable import DataTable, DataTableColumn

        """
        :param list fields: A list of strings or objects. Strings are converted
                            to DataTableColumn, objects are passed on as they are
        :param str title: Datatable title, automatically generated from form if None
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
                        formset.form.base_fields[f.fieldname].label,
                        HelpText(formset.form.base_fields[f.fieldname].help_text),
                    ),
                    f,
                )
            columns.append(f)
        columns.append(
            DataTableColumn(
                hg.If(
                    formset.can_order,
                    _("Order"),
                ),
                hg.If(
                    formset.can_order,
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
                    formset.can_delete,
                    InlineDeleteButton(parentcontainerselector="tr"),
                ),
            )
        )

        formsetelem = Formset(
            formset,
            DataTable.row(columns),
            **({"fieldname": fieldname} if fieldname else {}),
            **(formsetfield_kwargs or {}),
        )
        id = hg.html_id(formsetelem, prefix="formset-")

        return hg.BaseElement(
            hg.If(
                formset.non_form_errors(),
                hg.Iterator(
                    formset.non_form_errors(),
                    "formerror",
                    InlineNotification(
                        _("Form error"), hg.C("formerror"), kind="error"
                    ),
                ),
            ),
            DataTable(
                row_iterator=formsetelem,
                rowvariable="",
                columns=columns,
                id=id,
                **kwargs,
            ).with_toolbar(
                title=title,
                primary_button=formsetelem.add_button(
                    buttontype="primary", container_css_selector=f"#{id} tbody"
                )
                if can_add
                else None,
            ),
            formsetelem.management_form,
        )


class InlineDeleteButton(Button):
    def __init__(self, parentcontainerselector, label=_("Delete"), **kwargs):
        """
        Show a delete button for the current inline form. This element needs to
        be inside a Formset.
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
