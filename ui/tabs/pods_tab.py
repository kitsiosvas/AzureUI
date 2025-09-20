from kivymd.uix.tab import MDTabsBase
from kivymd.uix.floatlayout import MDFloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.button import MDRaisedButton
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from data.colors import *
from ui.popup import PopupManager
from ui.datatable import CustomDataTable

class PodsTab(MDFloatLayout, MDTabsBase):
    POD_LAYOUT_SIZE_HINT = (0.35, 1)
    OUTPUT_LAYOUT_SIZE_HINT = (0.65, 1)

    def __init__(self, azure_client, namespace_spinner, **kwargs):
        super().__init__(title='Pods', _md_bg_color=TAB_GRAY, **kwargs)
        self.azure_client = azure_client
        self.namespace_spinner = namespace_spinner
        self.last_selected_pod = None
        self.full_output = ""
        self.pods_popup_manager = None
        self.logs_popup_manager = None
        
        self.azure_client.bind(on_pods_output=self.on_pods_output)
        self.azure_client.bind(on_logs_output=self.on_logs_output)
        self.azure_client.bind(on_describe_output=self.on_describe_output)

        self.content = BoxLayout(orientation='horizontal')
        
        # LEFT PANEL
        self.left_panel = BoxLayout(orientation='vertical', size_hint=self.POD_LAYOUT_SIZE_HINT)
        self.get_pods_button = MDRaisedButton(text='Get Pods', size_hint=(1.0, None), height=40, disabled=True, md_bg_color=BUTTON_DARK_GRAY, text_color=WHITE)
        self.get_pods_button.bind(on_press=self.get_pods_button_callback)
        self.left_panel.add_widget(self.get_pods_button)
        
        self.pods_container = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)
        self.pods_table = CustomDataTable(
            column_data=["Name", "Status", "Age", "Restarts"],
            row_data=[],
            column_widths=[dp(200), dp(150), dp(100), dp(100)]
        )
        self.pods_table.bind(on_row_select=self.pod_row_press)
        self.pods_container.add_widget(self.pods_table)
        self.left_panel.add_widget(self.pods_container)
        self.content.add_widget(self.left_panel)
        
        # RIGHT PANEL
        self.right_panel = BoxLayout(orientation='vertical', size_hint=self.OUTPUT_LAYOUT_SIZE_HINT)
        
        self.command_layout = BoxLayout(orientation='horizontal', size_hint_y=0.10, spacing=2)
        self.fetch_logs_button = MDRaisedButton(text='Fetch Logs', size_hint=(0.5, 1), disabled=True, md_bg_color=BUTTON_DARK_GRAY, text_color=WHITE)
        self.fetch_logs_button.bind(on_press=self.get_logs_button_callback)
        self.describe_pod_button = MDRaisedButton(text='Describe Pod', size_hint=(0.5, 1), disabled=True, md_bg_color=BUTTON_DARK_GRAY, text_color=WHITE)
        self.describe_pod_button.bind(on_press=self.describe_pod_button_callback)
        self.command_layout.add_widget(self.fetch_logs_button)
        self.command_layout.add_widget(self.describe_pod_button)
        self.right_panel.add_widget(self.command_layout)
        
        self.output_layout = BoxLayout(orientation='vertical', size_hint_y=0.90)
        self.filter_input = TextInput(
            multiline=False,
            size_hint_y=0.1,
            hint_text='Filter (e.g., req_id, error)',
        )
        self.filter_input.bind(on_text_validate=self.filter_output)
        self.output_layout.add_widget(self.filter_input)
        self.command_output = TextInput(
            multiline=True,
            readonly=True,
            size_hint_y=0.9,
        )
        self.output_layout.add_widget(self.command_output)
        self.right_panel.add_widget(self.output_layout)
        
        self.content.add_widget(self.right_panel)
        self.add_widget(self.content)

    def get_pods_button_callback(self, instance):
        """Fetch pods using AzureClient."""
        namespace = self.namespace_spinner.text
        self.pods_popup_manager = PopupManager("Getting Pods", "Fetching pods...")
        self.azure_client.get_pods(namespace)

    def on_pods_output(self, instance, output):
        """Handle pods output event from AzureClient."""
        self.display_get_pods_result(output)
        self.pods_popup_manager.dismiss()
        self.pods_popup_manager = None

    def display_get_pods_result(self, output):
        """Display pods based on the command result."""
        self.last_selected_pod = None
        self.fetch_logs_button.disabled = True
        self.describe_pod_button.disabled = True
        self.full_output = ""
        self.command_output.text = ""
        self.filter_input.text = ""
        
        if isinstance(output, str) and "Error" in output:
            self.pods_table.update_row_data([])
            return
        
        # Update table with pod data
        row_data = [
            (pod["name"], pod["status"], pod["age"], str(pod["restarts"]))
            for pod in output
        ]
        self.pods_table.update_row_data(row_data)

    def pod_row_press(self, instance, pod_name):
        """Handle row selection in the table."""
        self.last_selected_pod = pod_name
        self.check_get_logs_button_state()

    def check_get_logs_button_state(self):
        """Enable/disable command buttons based on pod selection."""
        enabled = bool(self.last_selected_pod)
        self.fetch_logs_button.disabled = not enabled
        self.describe_pod_button.disabled = not enabled

    def get_logs_button_callback(self, instance):
        """Fetch logs for the selected pod using AzureClient."""
        namespace = self.namespace_spinner.text
        self.logs_popup_manager = PopupManager("Getting Logs", "Fetching logs...")
        self.azure_client.get_logs(self.last_selected_pod, namespace)
    
    def on_logs_output(self, instance, output):
        """Handle logs output event from AzureClient."""
        self.display_get_logs_result(output)
        self.logs_popup_manager.dismiss()
        self.logs_popup_manager = None

    def display_get_logs_result(self, output):
        """Display the logs based on the command result."""
        self.full_output = output
        self.filter_input.text = ""
        self.command_output.text = output

    def describe_pod_button_callback(self, instance):
        """Fetch describe for the selected pod using AzureClient."""
        namespace = self.namespace_spinner.text
        self.logs_popup_manager = PopupManager("Getting Describe", "Fetching pod describe...")
        self.azure_client.get_describe_pod(self.last_selected_pod, namespace)

    def on_describe_output(self, instance, output):
        """Handle describe output event from AzureClient."""
        self.display_get_describe_result(output)
        self.logs_popup_manager.dismiss()  # Reuse var
        self.logs_popup_manager = None

    def display_get_describe_result(self, output):
        """Display the describe output based on the command result."""
        self.full_output = output
        self.filter_input.text = ""
        self.command_output.text = output

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