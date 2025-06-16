from kivy.uix.tabbedpanel import TabbedPanelItem
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.button import MDRaisedButton
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivymd.uix.datatables import MDDataTable
from kivy.metrics import dp
from data.colors import DARK_GRAY, PURPLE, WHITE

from ui.popup import PopupManager

class PodsTab(TabbedPanelItem):
    def __init__(self, azure_client, namespace_spinner, **kwargs):
        super().__init__(text='Pods', **kwargs)
        self.azure_client = azure_client
        self.namespace_spinner = namespace_spinner
        self.last_selected_pod = None
        self.full_output = ""  # Store unfiltered command output
        self.pods_popup_manager = None  # Store PopupManager for get_pods
        self.logs_popup_manager = None  # Store PopupManager for get_logs
        
        # Bind to AzureClient's events
        self.azure_client.bind(on_pods_output=self.on_pods_output)
        self.azure_client.bind(on_logs_output=self.on_logs_output)
        
        # UI: Horizontal split (left 30%, right 70%)
        self.content = BoxLayout(orientation='horizontal')
        
        # Left panel: Get Pods button and pod table
        self.left_panel = BoxLayout(orientation='vertical', size_hint=(0.3, 1))
        self.get_pods_button = MDRaisedButton(
            text='Get Pods',
            size_hint=(1.0, None),
            height=40,
            disabled=True,
            md_bg_color=DARK_GRAY,
            text_color=WHITE
        )
        self.get_pods_button.bind(on_press=self.get_pods_button_callback)
        self.left_panel.add_widget(self.get_pods_button)
        
        # Scrollable table
        self.pods_container = ScrollView(size_hint=(1, 1))
        self.pods_table = MDDataTable(
            use_pagination=False,
            background_color = WHITE,
            column_data=[
                ("Name", dp(60)),
                ("Status", dp(30)),
                ("Age", dp(30)),
                ("Restarts", dp(20))
            ],
            row_data=[],
            rows_num=100,
            background_color_selected_cell=DARK_GRAY,
        )
        self.pods_table.bind(on_row_press=self.pod_row_press)
        self.pods_container.add_widget(self.pods_table)
        self.left_panel.add_widget(self.pods_container)
        self.content.add_widget(self.left_panel)
        
        # Right panel: Command buttons (top 10%) and output (bottom 90%)
        self.right_panel = BoxLayout(orientation='vertical', size_hint=(0.7, 1))
        
        # Command buttons
        self.command_layout = BoxLayout(orientation='horizontal', size_hint_y=0.10, spacing=2)
        self.fetch_logs_button = MDRaisedButton(
            text='Fetch Logs',
            size_hint=(0.5, 1),
            disabled=True,
            md_bg_color=DARK_GRAY,
            text_color=WHITE,
        )
        self.fetch_logs_button.bind(on_press=self.get_logs_button_callback)
        self.describe_pod_button = MDRaisedButton(
            text='Describe Pod',
            size_hint=(0.5, 1),
            disabled=True,
            md_bg_color=DARK_GRAY,
            text_color=WHITE
        )
        self.describe_pod_button.bind(on_press=self.describe_pod_button_callback)
        self.command_layout.add_widget(self.fetch_logs_button)
        self.command_layout.add_widget(self.describe_pod_button)
        self.right_panel.add_widget(self.command_layout)
        
        # Output area: Filter + TextInput
        self.output_layout = BoxLayout(orientation='vertical', size_hint_y=0.90)
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
            self.pods_table.update_row_data(self.pods_table.column_data, [])
            self.pods_table.height = dp(48)  # Header only
            return
        
        # Update table with pod data
        row_data = [
            (pod["name"], pod["status"], pod["age"], str(pod["restarts"]))
            for pod in output
        ]
        if len(row_data) > 100:
            print(f"Warning: {len(row_data)} pods exceed table limit (100). Truncating to 100.")
            row_data = row_data[:100]
        self.pods_table.update_row_data([], row_data)


    def pod_row_press(self, instance_table, instance_row):
        """Handle row selection in the table."""
        # Get the row index and data
        row_index = int(instance_row.index / len(self.pods_table.column_data))
        if row_index >= 0 and row_index < len(self.pods_table.row_data):
            pod_name = self.pods_table.row_data[row_index][0]
            self.last_selected_pod = pod_name
        else:
            self.last_selected_pod = None
        self.check_get_logs_button_state()

    def check_get_logs_button_state(self):
        """Enable/disable command buttons based on pod selection."""
        self.fetch_logs_button.disabled = not bool(self.last_selected_pod)
        self.describe_pod_button.disabled = not bool(self.last_selected_pod)

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