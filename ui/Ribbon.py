from data.colors import LIGHT_GRAY, SHADOW_GRAY
from ui.ColoredSpinner import ColoredSpinner
from kivymd.uix.button import MDRaisedButton
from kivy.graphics import Color, Rectangle
from kivy.uix.boxlayout import BoxLayout
from data.colors import *
from data.DATA import *

class Ribbon(BoxLayout):
    def __init__(self, size_hint_y=0.12, spinner_width=0.8, button_width=0.2, **kwargs):
        super(Ribbon, self).__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = 0.12  # 12% of window height

        # Create spinners and merge button
        self.region_spinner = ColoredSpinner(default_text=DEFAULT_TEXT_REGION_DROPDOWN, values=REGIONS, default_color=DARK_GRAY, selected_color=DROPDOWN_SELECTED_GREEN, height=40)
        self.environment_spinner = ColoredSpinner(default_text=DEFAULT_TEXT_ENVIRONMENT_DROPDOWN, values=ENVIRONMENTS, default_color=DARK_GRAY, selected_color=DROPDOWN_SELECTED_GREEN, height=40)
        self.subscription_spinner = ColoredSpinner(default_text=DEFAULT_TEXT_SUBSCRIPTION_DROPDOWN, values=[], default_color=DARK_GRAY, selected_color=DROPDOWN_SELECTED_GREEN, height=40)
        self.resource_group_spinner = ColoredSpinner(default_text=DEFAULT_TEXT_RESOURCE_GROUP_DROPDOWN, values=[], default_color=DARK_GRAY, selected_color=DROPDOWN_SELECTED_GREEN, height=40)
        self.cluster_spinner = ColoredSpinner(default_text=DEFAULT_TEXT_CLUSTER_DROPDOWN, values=[], default_color=DARK_GRAY, selected_color=DROPDOWN_SELECTED_GREEN, height=40)
        self.namespace_spinner = ColoredSpinner(default_text=DEFAULT_TEXT_NAMESPACE_DROPDOWN, values=[], default_color=DARK_BLUE, selected_color=DARK_BLUE, height=40)
        self.merge_button = MDRaisedButton(text='Merge', size_hint=(1, 1), disabled=True, md_bg_color=BUTTON_DARK_GRAY, text_color=WHITE)

        # Create ribbon
        spinners = [
            self.region_spinner,
            self.environment_spinner,
            self.subscription_spinner,
            self.resource_group_spinner,
            self.cluster_spinner,
            self.namespace_spinner
        ]
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
        self.merge_button.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        button_layout.add_widget(self.merge_button)

        self.add_widget(spinner_layout)
        self.add_widget(button_layout)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size
        self.shadow.pos = (instance.pos[0], instance.pos[1]-5)
        self.shadow.size = (instance.size[0], instance.size[1]+5)