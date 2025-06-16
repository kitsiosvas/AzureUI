from kivymd.uix.tab import MDTabsBase
from kivymd.uix.floatlayout import MDFloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.togglebutton import ToggleButton
from ui.popup import PopupManager
from data.colors import *
from kivymd.uix.button import MDRaisedButton

class SecretsTab(MDFloatLayout, MDTabsBase):
    def __init__(self, azure_client, namespace_spinner, **kwargs):
        super().__init__(title='Secrets', _md_bg_color=TAB_GRAY, **kwargs)
        self.azure_client = azure_client
        self.namespace_spinner = namespace_spinner
        self.secrets_popup_manager = None

        self.azure_client.bind(on_secrets_output=self.on_secrets_output)

        # UI
        self.content = BoxLayout(orientation='vertical')
        self.get_secrets_button = MDRaisedButton(text='Get Secrets', size_hint=(1.0, None), height=40, disabled=True, md_bg_color=BUTTON_DARK_GRAY, text_color=WHITE)
        self.get_secrets_button.bind(on_press=self.get_secrets_button_callback)
        self.content.add_widget(self.get_secrets_button)
        self.secrets_container = ScrollView(size_hint_y=0.9)
        self.secrets_grid = GridLayout(cols=1, size_hint_y=None)
        self.secrets_grid.bind(minimum_height=self.secrets_grid.setter('height'))
        self.secrets_container.add_widget(self.secrets_grid)
        self.content.add_widget(self.secrets_container)
        self.add_widget(self.content)

    def get_secrets_button_callback(self, instance):
        """Fetch secrets using AzureClient."""
        namespace = self.namespace_spinner.text
        self.secrets_popup_manager = PopupManager("Getting Secrets", "Fetching secrets...")
        self.azure_client.get_secrets(namespace)

    def on_secrets_output(self, instance, output):
        """Handle secrets output event from AzureClient."""
        self.display_get_secrets_result(output)
        self.secrets_popup_manager.dismiss()
        self.secrets_popup_manager = None

    def display_get_secrets_result(self, output):
        """Update secrets based on the command result."""
        self.secrets_grid.clear_widgets()
        secrets_output = output.strip()
        if secrets_output:
            secrets_lines = secrets_output.split('\n')  # SDK returns secret names, one per line
            for line in secrets_lines:
                if line:
                    secret_name = line
                    radio_button = ToggleButton(text=secret_name, group='secrets', size_hint_y=None, height=40)
                    self.secrets_grid.add_widget(radio_button)