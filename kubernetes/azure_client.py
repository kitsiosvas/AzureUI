import subprocess
import threading
from kivy.clock import Clock
from kivy.event import EventDispatcher

class AzureClient(EventDispatcher):
    def __init__(self):
        super().__init__()
        self.register_event_type('on_merge_output')

    def execute_command(self, command, event_name=None):
        """Execute a command asynchronously and dispatch event if specified."""
        thread = threading.Thread(target=self._execute_in_background, args=(command, event_name))
        thread.start()

    def _execute_in_background(self, command, event_name):
        """Execute the command in a separate thread."""
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        output = stdout.decode() if stdout else stderr.decode()
        
        if event_name == 'on_merge_output':
            success = "Merged" in output and "error" not in output.lower()
            Clock.schedule_once(lambda dt: self.dispatch(event_name, output, success), 0)
        elif event_name:
            Clock.schedule_once(lambda dt: self.dispatch(event_name, output), 0)

    def execute_merge(self, subscription, resource_group, cluster_name):
        """Execute the merge command asynchronously and dispatch event."""
        command = f"az aks get-credentials --subscription {subscription} --resource-group {resource_group} --name {cluster_name}"
        self.execute_command(command, 'on_merge_output')

    def on_merge_output(self, output, success):
        """Event handler for merge output (default implementation)."""
        pass

    def get_pods(self, namespace, callback):
        """ Execute the command to get pods in the specified namespace. """
        command = f"kubectl get pods -n {namespace}"
        self.execute_command(command, callback)

    def get_logs(self, pod, namespace, callback):
        """ Execute the command to get logs for a specific pod in the specified namespace. """
        command = f"kubectl logs {pod} -n {namespace}"
        self.execute_command(command, callback)
    
    def get_secrets(self, namespace, callback):
        """Execute the command to get secrets in the specified namespace."""
        command = f"kubectl get secrets -n {namespace}"
        self.execute_command(command, callback)

    def get_deployments(self, namespace, callback):
        """Execute the command to get deployments in the specified namespace."""
        command = f"kubectl get deployments -n {namespace}"
        self.execute_command(command, callback)