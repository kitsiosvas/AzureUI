from kivy.uix.tabbedpanel import TabbedPanelItem
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.togglebutton import ToggleButton

from ui.popup import PopupManager

class PodsTab(TabbedPanelItem):
    def __init__(self, azure_client, namespace_spinner, **kwargs):
        super().__init__(text='Pods', **kwargs)
        self.azure_client = azure_client
        self.namespace_spinner = namespace_spinner
        self.last_selected_pod = None
        self.full_output = ""  # Store unfiltered command output
        
        # UI: Horizontal split (left 30%, right 70%)
        self.content = BoxLayout(orientation='horizontal')
        
        # Left panel: Get Pods button and pod list
        self.left_panel = BoxLayout(orientation='vertical', size_hint=(0.3, 1))
        self.get_pods_button = Button(text='Get Pods', size_hint_y=None, height=40, disabled=True)
        self.get_pods_button.bind(on_press=self.get_pods_button_callback)
        self.left_panel.add_widget(self.get_pods_button)
        self.pods_container = ScrollView(size_hint=(1, 1))
        self.pods_list = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5, padding=5)
        self.pods_list.bind(minimum_height=self.pods_list.setter('height'))
        self.pods_container.add_widget(self.pods_list)
        self.left_panel.add_widget(self.pods_container)
        self.content.add_widget(self.left_panel)
        
        # Right panel: Command buttons (top 15%) and output (bottom 85%)
        self.right_panel = BoxLayout(orientation='vertical', size_hint=(0.7, 1))
        
        # Command buttons
        self.command_layout = BoxLayout(orientation='horizontal', size_hint_y=0.15)
        self.fetch_logs_button = Button(text='Fetch Logs', size_hint_x=0.5, disabled=True)
        self.fetch_logs_button.bind(on_press=self.fetch_logs_button_callback)
        self.describe_pod_button = Button(text='Describe Pod', size_hint_x=0.5, disabled=True)
        self.describe_pod_button.bind(on_press=self.describe_pod_button_callback)
        self.command_layout.add_widget(self.fetch_logs_button)
        self.command_layout.add_widget(self.describe_pod_button)
        self.right_panel.add_widget(self.command_layout)
        
        # Output area: Filter + TextInput
        self.output_layout = BoxLayout(orientation='vertical', size_hint_y=0.85)
        self.filter_input = TextInput(
            multiline=False,
            size_hint_y=0.1,
            hint_text='Filter (e.g., req_id, error)'
        )
        self.filter_input.bind(on_text_validate=self.filter_output)
        self.output_layout.add_widget(self.filter_input)
        self.command_output = TextInput(multiline=True, readonly=True, size_hint_y=0.9)
        self.output_layout.add_widget(self.command_output)
        self.right_panel.add_widget(self.output_layout)
        
        self.content.add_widget(self.right_panel)
        self.add_widget(self.content)

    def get_pods_button_callback(self, instance):
        """Get pods using AzureClient."""
        namespace = self.namespace_spinner.text
        self.popup_manager = PopupManager("Getting Pods", "Fetching pods...")
        self.azure_client.get_pods(namespace, self.display_get_pods_result)

    def display_get_pods_result(self, output):
        """Update pods based on the command result."""
        self.pods_list.clear_widgets()
        self.last_selected_pod = None
        self.fetch_logs_button.disabled = True
        self.describe_pod_button.disabled = True
        self.full_output = ""
        self.logs_output.text = ""
        self.filter_input.text = ""
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
                    self.pods_list.add_widget(radio_button)
        self.popup_manager.dismiss()

    def pod_toggle_callback(self, instance):
        """Handle pod selection."""
        self.last_selected_pod = instance.text if instance.state == 'down' else None
        self.check_get_logs_button_state()

    def check_get_logs_button_state(self):
        """Enable/disable command buttons based on pod selection."""
        self.fetch_logs_button.disabled = not bool(self.last_selected_pod)
        self.describe_pod_button.disabled = not bool(self.last_selected_pod)

    def fetch_logs_button_callback(self, instance):
        """Fetch logs for the selected pod."""
        namespace = self.namespace_spinner.text
        self.popup_manager = PopupManager("Getting Logs", "Fetching logs...")
        self.azure_client.get_logs(self.last_selected_pod, namespace, self.display_get_logs_result)

    def display_get_logs_result(self, output):
        """Update the logs based on the command result."""
        self.full_output = output
        self.filter_input.text = ""
        self.command_output.text = output
        self.popup_manager.dismiss()

    def describe_pod_button_callback(self, instance):
        """Placeholder for Describe Pod command."""
        print("Describe Pod not implemented")
        self.full_output = "Describe Pod output placeholder"
        self.filter_input.text = ""
        self.command_output.text = self.full_output

    def filter_output(self, instance):
        """Filter command_output based on filter_input text."""
        if not self.full_output:
            self.command_output.text = ""
            return
        filter_text = instance.text.lower()
        if not filter_text:
            self.command_output.text = self.full_output
            return
        filtered_lines = [
            line for line in self.full_output.split('\n')
            if filter_text in line.lower()
        ]
        self.command_output.text = '\n'.join(filtered_lines)