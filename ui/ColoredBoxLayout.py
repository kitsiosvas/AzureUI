from kivy.graphics import Color, Rectangle
from kivy.uix.boxlayout import BoxLayout


class ColoredBoxLayout(BoxLayout):
    def __init__(self, color, **kwargs):
        super(ColoredBoxLayout, self).__init__(**kwargs)
        with self.canvas.before:
            Color(*color)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)
    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size