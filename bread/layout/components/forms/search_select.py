import htmlgenerator as hg

from ..search import Search
from ..tag import Tag
from .widgets import BaseWidget

# TODO: Make this a BaseWidget class
# (requires some refactoring, should include generlized implementation of possible)


class SearchSelect(BaseWidget):
    def __init__(
        self,
        label=None,
        help_text=None,
        errors=None,
        inputelement_attrs=None,
        boundfield=None,
        backend=None,
        **attributes,
    ):
        """
        :param SearchBackendConfig backend: Where and how to get search results
        """
        inputelement_attrs = inputelement_attrs or {}

        # This works inside a formset. Might need to be changed for other usages.

        widget_id = inputelement_attrs.get("id")
        resultcontainerid = hg.format("search-result-{}", widget_id)
        tag_id = hg.format("{}-tag", widget_id)
        super().__init__(
            label,
            Tag(
                hg.F(
                    lambda c: hg.resolve_lazy(boundfield, c).field.to_python(
                        hg.resolve_lazy(boundfield, c).value()
                    )
                )
                if boundfield
                else "",
                id=tag_id,
                style=hg.If(
                    inputelement_attrs.get("value"),
                    hg.BaseElement(""),
                    hg.BaseElement("display: none;"),
                ),
                onclick="return false;",
            ),
            self.get_input_element(inputelement_attrs, errors, type="hidden"),
            Search(
                backend=backend,
                resultcontainerid=resultcontainerid,
                resultcontainer_onload_js=_resultcontainer_onload_js(
                    backend, resultcontainerid, tag_id, widget_id
                ),
                size="lg",
                disabled=inputelement_attrs.get("disabled", False),
                widgetattributes={"id": hg.format("search__{}", widget_id)},
            ),
            help_text,
            errors,
            **hg.merge_html_attrs(attributes, {"_class": "bx--text-input-wrapper"}),
        )


def _resultcontainer_onload_js(backend, resultcontainerid, tag_id, widget_id):
    on_click = hg.format(
        """function(evt) {{
        let label = $('{}', this).innerHTML;
        let value = $('{}', this).innerHTML;
        $('#{}').value = value;
        $('#{}').innerHTML = label;
        $('#{}').style = 'display: inline-block;';
        }}""",
        backend.result_label_selector,
        backend.result_value_selector,
        widget_id,
        tag_id,
        tag_id,
        autoescape=False,
    )

    return hg.format(
        """
    document.addEventListener('click', (evt) => this.innerHTML='');
    htmx.onLoad(function(target) {{
    // remove existing onlick attribute in case it e.g. redirects to the selected person
    $$('#{} {}')._.setAttribute('onclick', null);
    $$('#{} {}')._
    .addEventListener('click', {});
    }});""",
        resultcontainerid,
        backend.result_selector,
        resultcontainerid,
        backend.result_selector,
        on_click,
    )
