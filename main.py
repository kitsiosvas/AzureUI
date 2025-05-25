from kivy.clock import Clock
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.graphics import Color, Rectangle
from data.colors import *
from kivy.uix.spinner import Spinner
from kivy.uix.dropdown import DropDown
from data.DATA import *
from kubernetes.azure_client import AzureClient

class ColoredBoxLayout(BoxLayout):
    def __init__(self, color, **kwargs):
        super(ColoredBoxLayout, self).__init__(**kwargs)
        with self.canvas.before:
            Color(*color)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)
    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

class ColoredSpinner(Spinner):
    def __init__(self, default_text, values, default_color, selected_color, **kwargs):
        super(ColoredSpinner, self).__init__(**kwargs)
        self.text = default_text
        self.default_text = default_text  # Store default text for comparison
        self.values = values
        self.default_color = default_color
        self.selected_color = selected_color
        self.bind(text=self._on_text)
        self.background_color = default_color
        self.dropdown_cls = type('CustomDropDown', (DropDown,), {'max_height': 200})
    def _on_text(self, instance, value):
        self.background_color = self.selected_color if value != self.default_text else self.default_color
        
class KubernetesInterface(BoxLayout):
    def __init__(self, **kwargs):
        super(KubernetesInterface, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.azure_client = AzureClient()
        self.selected_subscription = None
        self.last_selection = (None, None, None)
        self.progress_update_interval = 0.5
        self.progress_schedule = None
        self.progress_bar = ProgressBar(max=100, size_hint_y=None, height=20)
        self.setup_ui()

    def setup_ui(self):
        # Ribbon (two rows of spinners + merge button)
        self.ribbon = BoxLayout(orientation='vertical', size_hint_y=None, height=80)
        with self.ribbon.canvas.before:
            Color(*LIGHT_GRAY)
            self.ribbon.rect = Rectangle(size=self.ribbon.size, pos=self.ribbon.pos)
            Color(*SHADOW_GRAY)
            self.ribbon.shadow = Rectangle(size=(self.ribbon.size[0], self.ribbon.size[1]+5), pos=(self.ribbon.pos[0], self.ribbon.pos[1]-5))
        self.ribbon.bind(size=self._update_ribbon_rect, pos=self._update_ribbon_rect)

        # Row 1: Region, Environment, Subscription
        row1 = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        self.region_spinner = ColoredSpinner(default_text=DEFAULT_TEXT_REGION_DROPDOWN, values=REGIONS, default_color=DARK_GRAY, selected_color=DROPDOWN_SELECTED_GREEN, size_hint_x=0.33, height=40)
        self.environment_spinner = ColoredSpinner(default_text=DEFAULT_TEXT_ENVIRONMENT_DROPDOWN, values=ENVIRONMENTS, default_color=DARK_GRAY, selected_color=DROPDOWN_SELECTED_GREEN, size_hint_x=0.33, height=40)
        self.subscription_spinner = ColoredSpinner(default_text=DEFAULT_TEXT_SUBSCRIPTION_DROPDOWN, values=[], default_color=DARK_GRAY, selected_color=DROPDOWN_SELECTED_GREEN, size_hint_x=0.33, height=40)
        row1.add_widget(self.region_spinner)
        row1.add_widget(self.environment_spinner)
        row1.add_widget(self.subscription_spinner)

        # Row 2: Resource Group, Cluster, Namespace, Merge Button
        row2 = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        self.resource_group_spinner = ColoredSpinner(default_text=DEFAULT_TEXT_RESOURCE_GROUP_DROPDOWN, values=[], default_color=DARK_GRAY, selected_color=DROPDOWN_SELECTED_GREEN, size_hint_x=0.33, height=40)
        self.cluster_spinner = ColoredSpinner(default_text=DEFAULT_TEXT_CLUSTER_DROPDOWN, values=[], default_color=DARK_GRAY, selected_color=DROPDOWN_SELECTED_GREEN, size_hint_x=0.33, height=40)
        self.namespace_spinner = ColoredSpinner(default_text=DEFAULT_TEXT_NAMESPACE_DROPDOWN, values=[], default_color=DARK_BLUE, selected_color=DARK_BLUE, size_hint_x=0.33, height=40)
        self.merge_button = Button(text='Merge', disabled=True, size_hint=(None, None), width=100, height=40)
        row2.add_widget(self.resource_group_spinner)
        row2.add_widget(self.cluster_spinner)
        row2.add_widget(self.namespace_spinner)
        row2.add_widget(self.merge_button)

        self.ribbon.add_widget(row1)
        self.ribbon.add_widget(row2)

        # Bind spinner selections
        self.region_spinner.bind(text=self.region_spinner_selection_callback)
        self.environment_spinner.bind(text=self.environment_spinner_selection_callback)
        self.subscription_spinner.bind(text=self.subscription_spinner_selection_callback)
        self.resource_group_spinner.bind(text=self.resource_group_spinner_selection_callback)
        self.cluster_spinner.bind(text=self.cluster_spinner_selection_callback)
        self.namespace_spinner.bind(text=self.namespace_spinner_selection_callback)
        self.merge_button.bind(on_press=self.merge_button_callback)

        # Tabbed content area
        self.tab_panel = TabbedPanel(do_default_tab=False, tab_height=40, background_color=DARK_GRAY)
        
        # Pods Tab
        pods_tab = TabbedPanelItem(text='Pods')
        pods_content = BoxLayout(orientation='vertical')
        self.get_pods_button = Button(text='Get Pods', size_hint_y=None, height=40, disabled=True)
        self.get_pods_button.bind(on_press=self.get_pods_button_callback)
        pods_content.add_widget(self.get_pods_button)
        
        self.pods_container = ScrollView(size_hint_y=0.5)
        self.pods_grid = GridLayout(cols=1, size_hint_y=None)
        self.pods_grid.bind(minimum_height=self.pods_grid.setter('height'))
        self.pods_container.add_widget(self.pods_grid)
        pods_content.add_widget(self.pods_container)
        
        logs_layout = BoxLayout(orientation='horizontal', size_hint_y=0.4)
        self.logs_output = TextInput(multiline=True, readonly=True, size_hint_x=0.7)
        self.fetch_logs_button = Button(text='Fetch Logs', size_hint=(0.3, None), height=40, disabled=True)
        self.fetch_logs_button.bind(on_press=self.fetch_logs_button_callback)
        logs_layout.add_widget(self.logs_output)
        logs_layout.add_widget(self.fetch_logs_button)
        pods_content.add_widget(logs_layout)
        
        pods_tab.content = pods_content
        self.tab_panel.add_widget(pods_tab)

        # Merge Tab
        merge_tab = TabbedPanelItem(text='Merge')
        merge_content = BoxLayout(orientation='vertical')
        self.merge_output_text = TextInput(multiline=True, readonly=True, size_hint_y=1)
        merge_content.add_widget(self.merge_output_text)
        merge_tab.content = merge_content
        self.tab_panel.add_widget(merge_tab)

        # Placeholder Tab
        placeholder_tab = TabbedPanelItem(text='Future Commands')
        placeholder_content = BoxLayout(orientation='vertical')
        placeholder_content.add_widget(Label(text='Coming soon: Secrets, Deployments, Ingress, etc.'))
        placeholder_tab.content = placeholder_content
        self.tab_panel.add_widget(placeholder_tab)

        # Set default tab
        self.tab_panel.default_tab = pods_tab

        # Add ribbon and tabs to root
        self.add_widget(self.ribbon)
        self.add_widget(self.tab_panel)

        # Merge success tracking
        self.merge_successful = False
        self.last_merged_subscription = None
        self.last_merged_resource_group = None
        self.last_merged_cluster = None

    def _update_ribbon_rect(self, instance, value):
        self.ribbon.rect.pos = instance.pos
        self.ribbon.rect.size = instance.size
        self.ribbon.shadow.pos = (instance.pos[0], instance.pos[1]-5)
        self.ribbon.shadow.size = (instance.size[0], instance.size[1]+5)

    def region_spinner_selection_callback(self, spinner, text):
        """Update the subscription spinner based on selected region."""
        self.update_subscription_spinner()

    def environment_spinner_selection_callback(self, spinner, text):
        """Update the subscription and namespace spinners based on selected environment."""
        self.update_subscription_spinner()
        self.update_namespace_spinner()

    def update_subscription_spinner(self):
        region_selected = self.region_spinner.text
        environment_selected = self.environment_spinner.text
        if region_selected != DEFAULT_TEXT_REGION_DROPDOWN and environment_selected != DEFAULT_TEXT_ENVIRONMENT_DROPDOWN:
            # Filter subscriptions based on selected region and environment
            filtered_subscriptions = [
                sub for sub in SUBSCRIPTIONS
                if sub.region == region_selected and sub.environment == environment_selected
            ]
            self.subscription_spinner.values = [sub.name for sub in filtered_subscriptions]
            self.subscription_spinner.text = DEFAULT_TEXT_SUBSCRIPTION_DROPDOWN  # Reset to default

            # Reset resource group and cluster spinners since subscription has changed
            self.resource_group_spinner.values = []
            self.cluster_spinner.values = []
            self.resource_group_spinner.text = DEFAULT_TEXT_RESOURCE_GROUP_DROPDOWN
            self.cluster_spinner.text = DEFAULT_TEXT_CLUSTER_DROPDOWN

    def update_namespace_spinner(self):
        """Update the namespace spinner based on the selected environment."""
        environment_selected = self.environment_spinner.text
        current_namespace = self.namespace_spinner.text
        if environment_selected == DEFAULT_TEXT_ENVIRONMENT_DROPDOWN:
            self.namespace_spinner.values = []
            self.namespace_spinner.text = DEFAULT_TEXT_NAMESPACE_DROPDOWN
        else:
            filtered_namespaces = [ns.name for ns in NAMESPACES if ns.environment == environment_selected]
            self.namespace_spinner.values = filtered_namespaces
            if current_namespace in filtered_namespaces:
                self.namespace_spinner.text = current_namespace
            else:
                self.namespace_spinner.text = DEFAULT_TEXT_NAMESPACE_DROPDOWN

    def subscription_spinner_selection_callback(self, spinner, text):
        """Update the resource group spinner based on the selected subscription."""
        self.selected_subscription = next((sub for sub in SUBSCRIPTIONS if sub.name == text), None)
        if self.selected_subscription:
            self.resource_group_spinner.values = list(self.selected_subscription.resource_groups.keys())
            self.resource_group_spinner.text = DEFAULT_TEXT_RESOURCE_GROUP_DROPDOWN
            self.reset_merge_state()
        self.check_merge_button_state()
        self.check_get_pods_button_state()

    def resource_group_spinner_selection_callback(self, spinner, text):
        """Update the cluster spinner based on the selected resource group."""
        if self.selected_subscription:
            self.cluster_spinner.values = self.selected_subscription.resource_groups.get(text, [])
            self.cluster_spinner.text = DEFAULT_TEXT_CLUSTER_DROPDOWN
            self.reset_merge_state()
        self.check_merge_button_state()
        self.check_get_pods_button_state()

    def cluster_spinner_selection_callback(self, spinner, text):
        """Reset the merge state when the cluster selection changes."""
        self.reset_merge_state()
        self.check_merge_button_state()
        self.check_get_pods_button_state()

    def namespace_spinner_selection_callback(self, spinner, text):
        """Reset the merge state when the namespace selection changes."""
        self.check_merge_button_state()
        self.check_get_pods_button_state()

    def reset_merge_state(self):
        """Reset the merge_successful state if any dropdown selection changes."""
        self.merge_successful = False

    def check_merge_button_state(self, *args):
        """Enable the Merge button if all required selections are made."""
        subscription = self.subscription_spinner.text
        resource_group = self.resource_group_spinner.text
        cluster = self.cluster_spinner.text
        if subscription != DEFAULT_TEXT_SUBSCRIPTION_DROPDOWN and resource_group != DEFAULT_TEXT_RESOURCE_GROUP_DROPDOWN and cluster != DEFAULT_TEXT_CLUSTER_DROPDOWN:
            self.merge_button.disabled = False
        else:
            self.merge_button.disabled = True

        # Disable the button if selections haven't changed
        if (
            self.last_selection[0] == subscription and
            self.last_selection[1] == resource_group and
            self.last_selection[2] == cluster
        ):
            self.merge_button.disabled = True

    def update_progress(self, dt):
        """Update progress bar value for animation."""
        self.progress_bar.value = (self.progress_bar.value + 5) % 100

    def show_progress_popup(self, title, message):
        """Show progress popup with custom message and start animation."""
        self.progress_bar.value = 0
        self.popup = Popup(title=title,
                           content=Label(text=message),
                           size_hint=(None, None), size=(400, 200))
        self.popup.open()
        if self.progress_schedule:
            self.progress_schedule.cancel()
        self.progress_schedule = Clock.schedule_interval(self.update_progress, self.progress_update_interval)

    def merge_button_callback(self, instance):
        """Execute the merge command using AzureClient."""
        subscription = self.subscription_spinner.text
        resource_group = self.resource_group_spinner.text
        cluster = self.cluster_spinner.text
        self.show_progress_popup("Executing", "Merging cluster...")
        self.azure_client.execute_merge(subscription, resource_group, cluster, self.display_merge_result)
        self.last_merged_subscription = subscription
        self.last_merged_resource_group = resource_group
        self.last_merged_cluster = cluster

    def check_get_pods_button_state(self):
        """Enable the Get Pods button if the namespace is selected and merge was successful."""
        namespace_selected = self.namespace_spinner.text != DEFAULT_TEXT_NAMESPACE_DROPDOWN
        self.get_pods_button.disabled = not (namespace_selected and self.merge_successful)

    def display_merge_result(self, output):
        """Output the command result to the text box."""
        self.merge_output_text.text = output
        self.merge_successful = "error" not in output.lower()
        if self.progress_schedule:
            self.progress_schedule.cancel()
        self.popup.dismiss()
        self.check_get_pods_button_state()

    def display_get_pods_result(self, output):
        """Update pods based on the command result."""
        self.pods_grid.clear_widgets()
        pods_output = output.strip()
        if self.progress_schedule:
            self.progress_schedule.cancel()
        if pods_output:
            pods_lines = pods_output.split('\n')[1:]
            for line in pods_lines:
                if line:
                    pod_name = line.split()[0]
                    radio_button = ToggleButton(text=pod_name, group='pods', size_hint_y=None, height=40)
                    radio_button.bind(on_press=self.pod_button_callback)
                    self.pods_grid.add_widget(radio_button)
        self.popup.dismiss()
        self.check_get_logs_button_state()

    def pod_button_callback(self, toggle_button):
        """Handle the state change of the pod selection toggle button."""
        self.check_get_logs_button_state()

    def get_pods_button_callback(self, instance):
        """Get pods using AzureClient."""
        namespace = self.namespace_spinner.text
        self.show_progress_popup("Getting Pods", "Fetching pods...")
        self.azure_client.get_pods(namespace, callback=self.display_get_pods_result)

    def check_get_logs_button_state(self):
        """Enable or disable the Fetch Logs button based on the selected pod."""
        self.fetch_logs_button.disabled = True
        for widget in self.pods_grid.children:
            if isinstance(widget, ToggleButton) and widget.state == 'down':
                self.fetch_logs_button.disabled = False
                break

    def fetch_logs_button_callback(self, instance):
        """Fetch logs using AzureClient."""
        selected_pod = None
        for widget in self.pods_grid.children:
            if isinstance(widget, ToggleButton) and widget.state == 'down':
                selected_pod = widget.text
                break
        namespace = self.namespace_spinner.text
        if selected_pod:
            self.show_progress_popup("Fetching Logs", "Fetching logs...")
            self.azure_client.get_logs(selected_pod, namespace, self.display_get_logs_result)

    def display_get_logs_result(self, output):
        """Update logs display based on the command result."""
        self.logs_output.text = output
        if self.progress_schedule:
            self.progress_schedule.cancel()
        self.popup.dismiss()

class KubernetesApp(App):
    def build(self):
        return KubernetesInterface()

if __name__ == '__main__':
    KubernetesApp().run()