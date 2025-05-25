from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
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
            Color(*color)  # Set the background color
            self.rect = Rectangle(size=self.size, pos=self.pos)

        self.bind(size=self._update_rect, pos=self._update_rect)

    def _update_rect(self, instance, value):
        self.rect.size = self.size
        self.rect.pos = self.pos


class ColoredSpinner(Spinner):
    def __init__(self, default_text, default_color, selected_color, **kwargs):
        super(ColoredSpinner, self).__init__(**kwargs)

        self.default_text = default_text
        self.default_color = default_color
        self.selected_color = selected_color

        # Set initial states
        self.background_color = self.default_color
        self.text = self.default_text

        # Bind events to change color
        self.bind(text=self.on_text_change)
        self.bind(on_drop_down=self.on_drop_down)

    def on_drop_down(self, spinner, dropdown):
        # Logic for dropdown behavior
        if isinstance(dropdown, DropDown):
            dropdown.canvas.before.clear()
            with dropdown.canvas.before:
                Color(*self.background_color)
                self.rect = Rectangle(size=dropdown.size, pos=dropdown.pos)
            dropdown.bind(pos=self._update_rect, size=self._update_rect)

    def on_text_change(self, spinner, text):
        """Change color based on selected text."""
        if text != self.default_text:  # Use default_text for conditions
            self.background_color = self.selected_color  # Change to selected color
        else:
            self.background_color = self.default_color  # Revert to default color

    def _update_rect(self, instance, value):
        self.rect.size = self.size
        self.rect.pos = self.pos


class KubernetesInterface(GridLayout):
    def __init__(self, **kwargs):
        super(KubernetesInterface, self).__init__(**kwargs)
        self.cols = 3
        self.azure_client = AzureClient()
        self.selected_subscription = None

        self.left_column = ColoredBoxLayout(color=DARK_GRAY, orientation='vertical')
        self.second_column = ColoredBoxLayout(color=LIGHT_GRAY, orientation='vertical')
        self.third_column = ColoredBoxLayout(color=DARK_BLUE, orientation='vertical')
        
        self.add_widget(self.left_column)
        self.add_widget(self.second_column)
        self.add_widget(self.third_column)

        # Progress Bar
        self.progress_bar = ProgressBar(max=100, size_hint_y=None, height=20)
        self.add_widget(self.progress_bar)

        # Store last selection values
        self.last_selection = (None, None, None)

        self.setup_left_column()
        self.setup_second_column()
        self.setup_third_column()

    def setup_left_column(self):
        # Dropdowns
        self.environment_spinner    = ColoredSpinner(default_text=DEFAULT_TEXT_ENVIRONMET_DROPDOWN,     values=ENVIRONMETS, default_color=DARK_GRAY, selected_color=DROPDOWN_SELECTED_GREEN, size_hint_y=None, height=40)
        self.region_spinner         = ColoredSpinner(default_text=DEFAULT_TEXT_REGION_DROPDOWN,         values=REGIONS,     default_color=DARK_GRAY, selected_color=DROPDOWN_SELECTED_GREEN, size_hint_y=None, height=40)
        self.subscription_spinner   = ColoredSpinner(default_text=DEFAULT_TEXT_SUBSCRIPTION_DROPDOWN,   values=[],          default_color=DARK_GRAY, selected_color=DROPDOWN_SELECTED_GREEN, size_hint_y=None, height=40)
        self.resource_group_spinner = ColoredSpinner(default_text=DEFAULT_TEXT_RESOURCE_GROUP_DROPDOWN, values=[],          default_color=DARK_GRAY, selected_color=DROPDOWN_SELECTED_GREEN, size_hint_y=None, height=40)
        self.cluster_spinner        = ColoredSpinner(default_text=DEFAULT_TEXT_CLUSTER_DROPDOWN,        values=[],          default_color=DARK_GRAY, selected_color=DROPDOWN_SELECTED_GREEN, size_hint_y=None, height=40)
        self.namespace_spinner      = ColoredSpinner(default_text=DEFAULT_TEXT_NAMESPACE_DROPDOWN,      values=[],          default_color=DARK_BLUE, selected_color=DARK_BLUE,               size_hint_y=None, height=40)

        # Bind selection changes
        self.region_spinner.bind(text=self.region_spinner_selection_callback)
        self.environment_spinner.bind(text=self.environment_spinner_selection_callback)
        self.subscription_spinner.bind(text=self.subscription_spinner_selection_callback)
        self.resource_group_spinner.bind(text=self.resource_group_spinner_selection_callback)
        self.cluster_spinner.bind(text=self.cluster_spinner_selection_callback)
        self.namespace_spinner.bind(text=self.namespace_spinner_selection_callback)

        # Add dropdowns
        self.left_column.add_widget(self.region_spinner)
        self.left_column.add_widget(self.environment_spinner)
        self.left_column.add_widget(self.subscription_spinner)
        self.left_column.add_widget(self.resource_group_spinner)
        self.left_column.add_widget(self.cluster_spinner)
        self.left_column.add_widget(self.namespace_spinner)


        # Merge Button
        self.merge_button = Button(text='Merge', disabled=True, size_hint_y=None, height=40)
        self.merge_button.bind(on_press=self.merge_button_callback)
        self.left_column.add_widget(self.merge_button)

        # Merge Command Output Text Box
        self.merge_output_text = TextInput(multiline=True, readonly=True, size_hint_y=None, height=120)
        self.left_column.add_widget(self.merge_output_text)

    def setup_second_column(self):
        # Merge Success Tracking
        self.merge_successful = False
        self.last_merged_subscription = None
        self.last_merged_resource_group = None
        self.last_merged_cluster = None

        # Get Pods Button
        self.get_pods_button = Button(text='Get Pods', size_hint_y=None, height=40)
        self.get_pods_button.bind(on_press=self.get_pods_button_callback)
        self.get_pods_button.disabled = True
        self.second_column.add_widget(self.get_pods_button)

        # Container for Pods
        self.pods_container = ScrollView(size_hint=(1, 1))
        self.pods_grid = GridLayout(cols=1, size_hint_y=None)
        self.pods_grid.bind(minimum_height=self.pods_grid.setter('height'))
        self.pods_container.add_widget(self.pods_grid)
        self.second_column.add_widget(self.pods_container)

        # Fetch Logs Button
        self.fetch_logs_button = Button(text='Fetch Logs', size_hint_y=None, height=40, disabled=True)
        self.fetch_logs_button.bind(on_press=self.fetch_logs_button_callback)
        self.second_column.add_widget(self.fetch_logs_button)

    def setup_third_column(self):
        # New TextInput for Log Output
        self.logs_output = TextInput(multiline=True, readonly=True)
        self.third_column.add_widget(self.logs_output)

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

        if region_selected != DEFAULT_TEXT_REGION_DROPDOWN and environment_selected != DEFAULT_TEXT_ENVIRONMET_DROPDOWN:
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

        if environment_selected == DEFAULT_TEXT_ENVIRONMET_DROPDOWN:
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

    def show_progress_popup(self, title):
        """Show progress popup."""
        self.progress_bar.value = 0
        self.popup = Popup(title=title,
                           content=Label(text="Please wait..."),
                           size_hint=(None, None), size=(400, 200))
        self.popup.open()

    def merge_button_callback(self, instance):
        """Execute the merge command using AzureClient."""
        subscription = self.subscription_spinner.text
        resource_group = self.resource_group_spinner.text
        cluster = self.cluster_spinner.text
        self.show_progress_popup("Executing")
        self.azure_client.execute_merge(subscription, resource_group, cluster, self.display_merge_result)

        # Store the current selection as the last merged values
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
        self.check_get_pods_button_state()
        self.popup.dismiss()

    def display_get_pods_result(self, output):
        """Update pods based on the command result."""
        self.pods_grid.clear_widgets()
        pods_output = output.strip()
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
        self.show_progress_popup("Getting Pods")
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
            self.show_progress_popup("Fetching Logs")
            self.azure_client.get_logs(selected_pod, namespace, self.display_get_logs_result)

    def display_get_logs_result(self, output):
        """Update logs display based on the command result."""
        self.logs_output.text = output
        self.popup.dismiss()

class KubernetesApp(App):
    def build(self):
        return KubernetesInterface()


if __name__ == '__main__':
    KubernetesApp().run()