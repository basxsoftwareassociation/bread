from django import forms


class AutocompleteSelect(forms.Select):
    template_name = "materialize_forms/autocomplete.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "class" not in self.attrs:
            self.attrs["class"] = ""
        self.attrs["class"] += " no-autoinit"

    # media is included in base.html


class AutocompleteSelectMultiple(forms.SelectMultiple):
    template_name = "materialize_forms/autocomplete.html"

    def __init__(self, attrs=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "class" not in self.attrs:
            self.attrs["class"] = ""
        self.attrs["class"] += " no-autoinit"

    # media is included in base.html
