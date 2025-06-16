from kivymd.uix.tab import MDTabsBase
from kivymd.uix.floatlayout import MDFloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from data.colors import DARK_GRAY, WHITE

class MergeTab(MDFloatLayout, MDTabsBase):
    def __init__(self, **kwargs):
        super().__init__(title='Merge', _md_bg_color=DARK_GRAY, **kwargs)
        self.content = BoxLayout(orientation='vertical', size_hint=(1, 1), pos_hint={'top': 1})
        self.merge_output_text = TextInput(multiline=True, readonly=True, size_hint_y=1)
        self.content.add_widget(self.merge_output_text)
        self.add_widget(self.content)