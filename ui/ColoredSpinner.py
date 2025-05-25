from kivy.uix.dropdown import DropDown
from kivy.uix.spinner import Spinner


class ColoredSpinner(Spinner):
    def __init__(self, default_text, values, default_color, selected_color, **kwargs):
        super(ColoredSpinner, self).__init__(**kwargs)
        self.text = default_text
        self.default_text = default_text
        self.values = values
        self.default_color = default_color
        self.selected_color = selected_color
        self.bind(text=self._on_text)
        self.background_color = default_color
        self.dropdown_cls = type('CustomDropDown', (DropDown,), {'max_height': 200})
    def _on_text(self, instance, value):
        self.background_color = self.selected_color if value != self.default_text else self.default_color