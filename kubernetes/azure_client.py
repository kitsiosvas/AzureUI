import subprocess
import threading
from kivy.clock import Clock

class AzureClient:
    def execute_command(self, command, callback):
        """ Execute a command and capture its output asynchronously. """
        thread = threading.Thread(target=self._execute_in_background, args=(command, callback))
        thread.start()

    def _execute_in_background(self, command, callback):
        """ Execute the command in a separate thread. """
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        output = stdout.decode() if stdout else stderr.decode()
        
        # Call the provided callback function to process the output
        Clock.schedule_once(lambda dt: callback(output), 0)

    def execute_merge(self, subscription, resource_group, cluster_name, callback):
        """Execute the merge command asynchronously and return output and success status."""
        command = f"az aks get-credentials --subscription {subscription} --resource-group {resource_group} --name {cluster_name}"
        def wrapped_callback(output):
            # Determine success based on output (e.g., "Merged" indicates success)
            success = "Merged" in output and "error" not in output.lower()
            callback(output, success)
        self.execute_command(command, wrapped_callback)

    def get_pods(self, namespace, callback):
        """ Execute the command to get pods in the specified namespace. """
        command = f"kubectl get pods -n {namespace}"
        self.execute_command(command, callback)

    def get_logs(self, pod, namespace, callback):
        """ Execute the command to get logs for a specific pod in the specified namespace. """
        command = f"kubectl logs {pod} -n {namespace}"
        self.execute_command(command, callback)