from data.colors import LIGHT_GRAY, SHADOW_GRAY


from kivy.graphics import Color, Rectangle
from kivy.uix.boxlayout import BoxLayout


class Ribbon(BoxLayout):
    def __init__(self, spinners, merge_button, spinner_width=0.8, button_width=0.2, **kwargs):
        super(Ribbon, self).__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = 0.12  # 12% of window height
        with self.canvas.before:
            Color(*LIGHT_GRAY)
            self.rect = Rectangle(size=self.size, pos=self.pos)
            Color(*SHADOW_GRAY)
            self.shadow = Rectangle(size=(self.size[0], self.size[1]+5), pos=(self.pos[0], self.pos[1]-5))
        self.bind(size=self._update_rect, pos=self._update_rect)

        # Spinner component
        spinner_layout = BoxLayout(orientation='vertical', size_hint_x=spinner_width)
        row1 = BoxLayout(orientation='horizontal', size_hint_y=0.5)
        row2 = BoxLayout(orientation='horizontal', size_hint_y=0.5)

        # Add spinners (3 per row)
        for i, spinner in enumerate(spinners[:3]):  # Region, Environment, Subscription
            spinner.size_hint_x = 0.333
            row1.add_widget(spinner)
        for i, spinner in enumerate(spinners[3:]):  # Resource Group, Cluster, Namespace
            spinner.size_hint_x = 0.333
            row2.add_widget(spinner)

        spinner_layout.add_widget(row1)
        spinner_layout.add_widget(row2)

        # Button component
        button_layout = BoxLayout(orientation='vertical', size_hint_x=button_width)
        merge_button.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        button_layout.add_widget(merge_button)

        self.add_widget(spinner_layout)
        self.add_widget(button_layout)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size
        self.shadow.pos = (instance.pos[0], instance.pos[1]-5)
        self.shadow.size = (instance.size[0], instance.size[1]+5)