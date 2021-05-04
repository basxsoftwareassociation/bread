from bread.layout.components.text_input import TextInput


class UrlInput(TextInput):
    def __init__(self, **attributes):
        super().__init__(icon="link", **attributes)
