import subprocess
import threading
from kivy.clock import Clock
from kivy.event import EventDispatcher
from kubernetes import client, config
from kubernetes.client.rest import ApiException

import logging
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('http.client').setLevel(logging.WARNING)
logging.getLogger('kubernetes').setLevel(logging.WARNING)

class AzureClient(EventDispatcher):
    def __init__(self):
        super().__init__()
        self.register_event_type('on_merge_output')
        self.register_event_type('on_pods_output')
        self.register_event_type('on_logs_output')
        self.register_event_type('on_secrets_output')
        self.register_event_type('on_deployments_output')
        self.k8s_config_loaded = False

    def _safe_load_kube_config(self):
        """Load Kubernetes config from ~/.kube/config set by az aks get-credentials."""
        import sys
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        if not self.k8s_config_loaded:
            try:
                # Patch stdout and stderr to avoid issues with Kivy's FILENO error
                sys.stdout = sys.__stdout__
                sys.stderr = sys.__stderr__
                config.load_kube_config()
                self.k8s_config_loaded = True
            except Exception as e:
                Clock.schedule_once(lambda dt: self.dispatch('on_pods_output', f"Error loading kubeconfig: {str(e)}", False), 0)
            finally:
                sys.stdout = original_stdout
                sys.stderr = original_stderr

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

    def get_pods_cli(self, namespace):
        """Execute the command to get pods in the specified namespace."""
        command = f"kubectl get pods -n {namespace}"
        self.execute_command(command, 'on_pods_output')

    def get_pods_sdk(self, namespace):
        """Execute the command to get pods in the specified namespace using Kubernetes SDK asynchronously."""
        def fetch_pods():
            try:
                self._safe_load_kube_config()
                v1 = client.CoreV1Api()
                pods = v1.list_namespaced_pod(namespace)
                output = "\n".join(pod.metadata.name for pod in pods.items)
                Clock.schedule_once(lambda dt: self.dispatch('on_pods_output', output, True), 0)
            except ApiException as e:
                error_output = f"Error fetching pods: {e.reason} ({e.status})"
                Clock.schedule_once(lambda dt: self.dispatch('on_pods_output', error_output, False), 0)
            except Exception as e:
                error_output = f"Error fetching pods: {str(e)}"
                Clock.schedule_once(lambda dt: self.dispatch('on_pods_output', error_output, False), 0)

        thread = threading.Thread(target=fetch_pods)
        thread.start()

    def on_pods_output(self, output, is_sdk_output=False):
        """Event handler for pods output (default implementation)."""
        pass

    def get_logs(self, pod, namespace):
        """Execute the command to get logs for a specific pod in the specified namespace."""
        command = f"kubectl logs {pod} -n {namespace}"
        self.execute_command(command, 'on_logs_output')

    def on_logs_output(self, output):
        """Event handler for logs output (default implementation)."""
        pass

    def get_secrets(self, namespace):
        """Execute the command to get secrets in the specified namespace."""
        command = f"kubectl get secrets -n {namespace}"
        self.execute_command(command, 'on_secrets_output')

    def on_secrets_output(self, output):
        """Event handler for secrets output (default implementation)."""
        pass

    def get_deployments(self, namespace):
        """Execute the command to get deployments in the specified namespace."""
        command = f"kubectl get deployments -n {namespace}"
        self.execute_command(command, 'on_deployments_output')

    def on_deployments_output(self, output):
        """Event handler for deployments output (default implementation)."""
        pass