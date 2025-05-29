from kivy.uix.tabbedpanel import TabbedPanelItem
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput

class MergeTab(TabbedPanelItem):
    def __init__(self, **kwargs):
        super(MergeTab, self).__init__(text='Merge', **kwargs)
        self.content = BoxLayout(orientation='vertical')
        self.merge_output_text = TextInput(multiline=True, readonly=True, size_hint_y=1)
        self.content.add_widget(self.merge_output_text)