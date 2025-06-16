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


class DeploymentsTab(MDFloatLayout, MDTabsBase):
    def __init__(self, azure_client, namespace_spinner, **kwargs):
        super().__init__(title='Deployments', _md_bg_color=TAB_GRAY, **kwargs)  # Pass title to MDTabsBase
        self.azure_client = azure_client
        self.namespace_spinner = namespace_spinner
        self.deployments_popup_manager = None  # Store PopupManager for get_deployments

        # Bind to AzureClient's on_deployments_output event
        self.azure_client.bind(on_deployments_output=self.on_deployments_output)

        # UI
        self.content = BoxLayout(orientation='vertical')
        self.get_deployments_button = MDRaisedButton(text='Get Deployments', size_hint=(1.0, None), height=40, disabled=True, md_bg_color=BUTTON_DARK_GRAY, text_color=WHITE)
        self.get_deployments_button.bind(on_press=self.get_deployments_button_callback)
        self.content.add_widget(self.get_deployments_button)
        self.deployments_container = ScrollView(size_hint_y=0.9)
        self.deployments_grid = GridLayout(cols=1, size_hint_y=None)
        self.deployments_grid.bind(minimum_height=self.deployments_grid.setter('height'))
        self.deployments_container.add_widget(self.deployments_grid)
        self.content.add_widget(self.deployments_container)
        self.add_widget(self.content)

    def get_deployments_button_callback(self, instance):
        """Fetch deployments using AzureClient."""
        namespace = self.namespace_spinner.text
        self.deployments_popup_manager = PopupManager("Getting Deployments", "Fetching deployments...")
        self.azure_client.get_deployments(namespace)

    def on_deployments_output(self, instance, output):
        """Handle deployments output event from AzureClient."""
        self.display_get_deployments_result(output)
        self.deployments_popup_manager.dismiss()
        self.deployments_popup_manager = None

    def display_get_deployments_result(self, output):
        """Update deployments based on the command result."""
        self.deployments_grid.clear_widgets()
        deployments_output = output.strip()
        if deployments_output:
            deployments_lines = deployments_output.split('\n')  # SDK returns deployment names, one per line
            for line in deployments_lines:
                if line:
                    deployment_name = line
                    radio_button = ToggleButton(text=deployment_name, group='deployments', size_hint_y=None, height=40)
                    self.deployments_grid.add_widget(radio_button)