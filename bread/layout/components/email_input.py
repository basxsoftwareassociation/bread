from bread.layout.components.text_input import TextInput


class EmailInput(TextInput):
    def __init__(self, **attributes):
        super().__init__(icon="email", **attributes)
