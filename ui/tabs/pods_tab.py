from kivy.uix.tabbedpanel import TabbedPanelItem
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.togglebutton import ToggleButton

from ui.popup import PopupManager

class PodsTab(TabbedPanelItem):
    def __init__(self, azure_client, namespace_spinner, **kwargs):
        super().__init__(text='Pods', **kwargs)
        self.azure_client = azure_client
        self.namespace_spinner = namespace_spinner
        self.last_selected_pod = None
        
        # UI
        self.content = BoxLayout(orientation='vertical')
        self.get_pods_button = Button(text='Get Pods', size_hint_y=None, height=40, disabled=True)
        self.get_pods_button.bind(on_press=self.get_pods_button_callback)
        self.content.add_widget(self.get_pods_button)
        self.pods_container = ScrollView(size_hint_y=0.5)
        self.pods_grid = GridLayout(cols=1, size_hint_y=None)
        self.pods_grid.bind(minimum_height=self.pods_grid.setter('height'))
        self.pods_container.add_widget(self.pods_grid)
        self.content.add_widget(self.pods_container)
        logs_layout = BoxLayout(orientation='horizontal', size_hint_y=0.4)
        self.logs_output = TextInput(multiline=True, readonly=True, size_hint_x=0.7)
        self.fetch_logs_button = Button(text='Fetch Logs', size_hint=(0.3, None), height=40, disabled=True)
        self.fetch_logs_button.bind(on_press=self.fetch_logs_button_callback)
        logs_layout.add_widget(self.logs_output)
        logs_layout.add_widget(self.fetch_logs_button)
        self.content.add_widget(logs_layout)

    def get_pods_button_callback(self, instance):
        """Get pods using AzureClient."""
        namespace = self.namespace_spinner.text
        self.popup_manager = PopupManager("Getting Pods", "Fetching pods...")
        self.azure_client.get_pods(namespace, self.display_get_pods_result)

    def display_get_pods_result(self, output):
        """Update pods based on the command result."""
        self.pods_grid.clear_widgets()
        self.last_selected_pod = None
        self.fetch_logs_button.disabled = True
        pods_output = output.strip()
        if pods_output:
            pods_lines = pods_output.split('\n')[1:]  # Skip header
            for line in pods_lines:
                if line:
                    pod_name = line.split()[0]
                    radio_button = ToggleButton(
                        text=pod_name,
                        group='pods',
                        size_hint_y=None,
                        height=40
                    )
                    radio_button.bind(on_press=self.pod_toggle_callback)
                    self.pods_grid.add_widget(radio_button)
        self.popup_manager.dismiss()

    def pod_toggle_callback(self, instance):
        """Handle pod selection."""
        self.last_selected_pod = instance.text if instance.state == 'down' else None
        self.check_get_logs_button_state()

    def check_get_logs_button_state(self):
        """Enable/disable the Fetch Logs button based on pod selection."""
        self.fetch_logs_button.disabled = not bool(self.last_selected_pod)

    def fetch_logs_button_callback(self, instance):
        """Fetch logs for the selected pod."""
        namespace = self.namespace_spinner.text
        self.popup_manager = PopupManager("Getting Logs", "Fetching logs...")
        self.azure_client.get_logs(self.last_selected_pod, namespace, self.display_get_logs_result)

    def display_get_logs_result(self, output):
        """Update the logs based on the command result."""
        self.logs_output.text = output
        self.popup_manager.dismiss()