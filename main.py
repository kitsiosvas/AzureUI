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
from ui.ColoredSpinner import ColoredSpinner
from ui.Ribbon import Ribbon
from data.colors import *
from data.DATA import *
from kubernetes.azure_client import AzureClient
from ui.tabs.deployments_tab import DeploymentsTab
from ui.tabs.merge_tab import MergeTab
from ui.tabs.pods_tab import PodsTab
from ui.tabs.secrets_tab import SecretsTab
from kivy.core.window import Window


class KubernetesInterface(BoxLayout):
    SPINNER_WIDTH = 0.8
    BUTTON_WIDTH = 0.2

    def __init__(self, **kwargs):
        super(KubernetesInterface, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.azure_client = AzureClient()
        self.selected_subscription = None
        self.last_selection = (None, None, None)
        self.progress_update_interval = 0.5
        self.progress_schedule = None
        self.merge_successful = False
        self.progress_bar = ProgressBar(max=100, size_hint_y=None, height=20)
        self.setup_ui()

    def setup_ui(self):
        # Create spinners and merge button
        self.region_spinner = ColoredSpinner(default_text=DEFAULT_TEXT_REGION_DROPDOWN, values=REGIONS, default_color=DARK_GRAY, selected_color=DROPDOWN_SELECTED_GREEN, height=40)
        self.environment_spinner = ColoredSpinner(default_text=DEFAULT_TEXT_ENVIRONMENT_DROPDOWN, values=ENVIRONMENTS, default_color=DARK_GRAY, selected_color=DROPDOWN_SELECTED_GREEN, height=40)
        self.subscription_spinner = ColoredSpinner(default_text=DEFAULT_TEXT_SUBSCRIPTION_DROPDOWN, values=[], default_color=DARK_GRAY, selected_color=DROPDOWN_SELECTED_GREEN, height=40)
        self.resource_group_spinner = ColoredSpinner(default_text=DEFAULT_TEXT_RESOURCE_GROUP_DROPDOWN, values=[], default_color=DARK_GRAY, selected_color=DROPDOWN_SELECTED_GREEN, height=40)
        self.cluster_spinner = ColoredSpinner(default_text=DEFAULT_TEXT_CLUSTER_DROPDOWN, values=[], default_color=DARK_GRAY, selected_color=DROPDOWN_SELECTED_GREEN, height=40)
        self.namespace_spinner = ColoredSpinner(default_text=DEFAULT_TEXT_NAMESPACE_DROPDOWN, values=[], default_color=DARK_BLUE, selected_color=DARK_BLUE, height=40)
        self.merge_button = Button(text='Merge', disabled=True)

        # Bind spinner selections
        self.region_spinner.bind(text=self.region_spinner_selection_callback)
        self.environment_spinner.bind(text=self.environment_spinner_selection_callback)
        self.subscription_spinner.bind(text=self.subscription_spinner_selection_callback)
        self.resource_group_spinner.bind(text=self.resource_group_spinner_selection_callback)
        self.cluster_spinner.bind(text=self.cluster_spinner_selection_callback)
        self.namespace_spinner.bind(text=self.namespace_spinner_selection_callback)
        self.merge_button.bind(on_press=self.merge_button_callback)

        # Create ribbon
        spinners = [
            self.region_spinner,
            self.environment_spinner,
            self.subscription_spinner,
            self.resource_group_spinner,
            self.cluster_spinner,
            self.namespace_spinner
        ]
        self.ribbon = Ribbon(spinners, self.merge_button, spinner_width=self.SPINNER_WIDTH, button_width=self.BUTTON_WIDTH)
        self.add_widget(self.ribbon)

        # Tabbed content area
        self.tab_panel = TabbedPanel(do_default_tab=False, tab_width=Window.width*0.2, tab_height=Window.height * 0.08, background_color=DARK_GRAY)

        # Tabs
        self.merge_tab = MergeTab()
        self.pods_tab = PodsTab(
            azure_client=self.azure_client,
            namespace_spinner=self.namespace_spinner,
            show_progress_popup=self.show_progress_popup,
            progress_schedule=self.progress_schedule
        )
        self.secrets_tab = SecretsTab(
            azure_client=self.azure_client,
            namespace_spinner=self.namespace_spinner,
            show_progress_popup=self.show_progress_popup,
            progress_schedule=self.progress_schedule
        )
        self.deployments_tab = DeploymentsTab(
            azure_client=self.azure_client,
            namespace_spinner=self.namespace_spinner,
            show_progress_popup=self.show_progress_popup,
            progress_schedule=self.progress_schedule
        )
        self.tab_panel.add_widget(self.merge_tab)
        self.tab_panel.add_widget(self.pods_tab)
        self.tab_panel.add_widget(self.secrets_tab)
        self.tab_panel.add_widget(self.deployments_tab)
        self.tab_panel.default_tab = self.merge_tab
        self.add_widget(self.tab_panel)

        # Merge success tracking
        self.merge_successful = False
        self.last_merged_subscription = None
        self.last_merged_resource_group = None
        self.last_merged_cluster = None

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
        self.check_command_buttons_state()

    def resource_group_spinner_selection_callback(self, spinner, text):
        """Update the cluster spinner based on the selected resource group."""
        if self.selected_subscription:
            self.cluster_spinner.values = self.selected_subscription.resource_groups.get(text, [])
            self.cluster_spinner.text = DEFAULT_TEXT_CLUSTER_DROPDOWN
            self.reset_merge_state()
        self.check_merge_button_state()
        self.check_command_buttons_state()

    def cluster_spinner_selection_callback(self, spinner, text):
        """Reset the merge state when the cluster selection changes."""
        self.reset_merge_state()
        self.check_merge_button_state()
        self.check_command_buttons_state()

    def namespace_spinner_selection_callback(self, spinner, text):
        """Reset the merge state when the namespace selection changes."""
        self.check_merge_button_state()
        self.check_command_buttons_state()

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
        return self.popup

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

    def display_merge_result(self, output, success):
        """Output the command result to the text box."""
        self.merge_tab.merge_output_text.text = output
        self.merge_successful = success
        if self.progress_schedule:
            self.progress_schedule.cancel()
        self.popup.dismiss()
        self.check_command_buttons_state()

    def check_command_buttons_state(self):
        """Enable/disable command buttons if namespace is selected and merge was successful."""
        namespace_selected = self.namespace_spinner.text != DEFAULT_TEXT_NAMESPACE_DROPDOWN
        buttons_enabled = namespace_selected and self.merge_successful
        self.pods_tab.get_pods_button.disabled = not buttons_enabled
        self.secrets_tab.get_secrets_button.disabled = not buttons_enabled
        self.deployments_tab.get_deployments_button.disabled = not buttons_enabled
        self.pods_tab.check_get_logs_button_state()


class KubernetesApp(App):
    def build(self):
        return KubernetesInterface()

if __name__ == '__main__':
    KubernetesApp().run()