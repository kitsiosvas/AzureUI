from kivy.uix.tabbedpanel import TabbedPanelItem
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.togglebutton import ToggleButton

from ui.popup import PopupManager

class SecretsTab(TabbedPanelItem):
    def __init__(self, azure_client, namespace_spinner, **kwargs):
        super().__init__(text='Secrets', **kwargs)
        self.azure_client = azure_client
        self.namespace_spinner = namespace_spinner

        # UI
        self.content = BoxLayout(orientation='vertical')
        self.get_secrets_button = Button(text='Get Secrets', size_hint_y=None, height=40, disabled=True)
        self.get_secrets_button.bind(on_press=self.get_secrets_button_callback)
        self.content.add_widget(self.get_secrets_button)
        self.secrets_container = ScrollView(size_hint_y=0.9)
        self.secrets_grid = GridLayout(cols=1, size_hint_y=None)
        self.secrets_grid.bind(minimum_height=self.secrets_grid.setter('height'))
        self.secrets_container.add_widget(self.secrets_grid)
        self.content.add_widget(self.secrets_container)

    def get_secrets_button_callback(self, instance):
        """Get secrets using AzureClient."""
        namespace = self.namespace_spinner.text
        self.popup_manager = PopupManager("Getting Secrets", "Fetching secrets...")
        self.azure_client.get_secrets(namespace, self.display_get_secrets_result)

    def display_get_secrets_result(self, output):
        """Update secrets based on the command result."""
        self.secrets_grid.clear_widgets()
        secrets_output = output.strip()
        if secrets_output:
            secrets_lines = secrets_output.split('\n')[1:]  # Skip header
            for line in secrets_lines:
                if line:
                    secret_name = line.split()[0]
                    radio_button = ToggleButton(text=secret_name, group='secrets', size_hint_y=None, height=40)
                    self.secrets_grid.add_widget(radio_button)
        self.popup_manager.dismiss()