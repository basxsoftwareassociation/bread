from bread.layout.components.text_input_with_icon import TextInputWithIcon


class UrlInput(TextInputWithIcon):
    def __init__(self, **attributes):
        super().__init__("link", **attributes)
