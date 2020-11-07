import plisplate

from .icon import Icon


class Button(plisplate.htmltags.BUTTON):
    """ type: "primary", "secondary", "tertiary", "danger", "ghost" """

    def __init__(
        self,
        *children,
        type="primary",
        disabled_func=lambda context: False,
        icon=None,
        notext=False,
        small=False,
        **attributes,
    ):
        self.disabled_func = disabled_func
        attributes["type"] = "button"
        attributes["tabindex"] = attributes.get("tabindex", "0")
        attributes["_class"] = (
            attributes.get("_class", "") + f" bx--btn bx--btn--{type}"
        )
        if small:
            attributes["_class"] += " bx--btn--sm "
        if notext:
            attributes[
                "_class"
            ] += " bx--btn--icon-only bx--tooltip__trigger bx--tooltip--a11y bx--tooltip--bottom bx--tooltip--align-center"
            children = (plisplate.SPAN(*children, _class="bx--assistive-text"),)

        if icon:
            children += (Icon(icon, _class="bx--btn__icon"),)
        super().__init__(*children, **attributes)

    def render(self, context):
        attribs = {**self.attributes, **{"disabled": self.disabled_func(context)}}
        yield f"<{self.tag} {plisplate.flatattrs(attribs)}>"
        yield from super().render_children(context)
        yield f"</{self.tag}>"


class ButtonSet(plisplate.htmltags.DIV):
    def __init__(self, *buttons, **attributes):
        attributes["_class"] = attributes.get("_class", "") + " bx--btn-set"
        super().__init__(*buttons, **attributes)
