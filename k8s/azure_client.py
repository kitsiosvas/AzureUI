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

    def safe_load_kube_config(self):
        """Load Kubernetes config from ~/.kube/config set by az aks get-credentials."""
        import sys
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        try:
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
            config.load_kube_config()

            self.core_v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
        finally:
            sys.stdout = original_stdout
            sys.stderr = original_stderr

    def execute_merge(self, subscription, resource_group, cluster_name):
        """Execute the merge command asynchronously and dispatch event."""
        import subprocess
        command = f"az aks get-credentials --subscription {subscription} --resource-group {resource_group} --name {cluster_name}"
        thread = threading.Thread(target=self._run_merge, args=(command,))
        thread.start()

    def _run_merge(self, command):
        """Run the merge command in a separate thread."""
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        output = stdout.decode() if stdout else stderr.decode()
        success = "Merged" in output and "error" not in output.lower()
        Clock.schedule_once(lambda dt: self.dispatch('on_merge_output', output, success), 0)

    def on_merge_output(self, output, success):
        """Event handler for merge output."""
        pass

    def get_pods(self, namespace):
        """Fetch pods in the specified namespace using Kubernetes SDK asynchronously."""
        def fetch_pods():
            try:
                pods = self.core_v1.list_namespaced_pod(namespace)
                output = "\n".join(pod.metadata.name for pod in pods.items)
                Clock.schedule_once(lambda dt: self.dispatch('on_pods_output', output), 0)
            except ApiException as e:
                error_output = f"Error fetching pods: {e.reason} ({e.status})"
                Clock.schedule_once(lambda dt: self.dispatch('on_pods_output', error_output), 0)
            except Exception as e:
                error_output = f"Error fetching pods: {str(e)}"
                Clock.schedule_once(lambda dt: self.dispatch('on_pods_output', error_output), 0)

        thread = threading.Thread(target=fetch_pods)
        thread.start()

    def on_pods_output(self, output):
        """Event handler for pods output."""
        pass

    def get_logs(self, pod, namespace):
        """Fetch logs for a specific pod in the specified namespace using Kubernetes SDK asynchronously."""
        def fetch_logs():
            try:
                logs = self.core_v1.read_namespaced_pod_log(name=pod, namespace=namespace)
                Clock.schedule_once(lambda dt: self.dispatch('on_logs_output', logs), 0)
            except ApiException as e:
                error_output = f"Error fetching logs: {e.reason} ({e.status})"
                Clock.schedule_once(lambda dt: self.dispatch('on_logs_output', error_output), 0)
            except Exception as e:
                error_output = f"Error fetching logs: {str(e)}"
                Clock.schedule_once(lambda dt: self.dispatch('on_logs_output', error_output), 0)

        thread = threading.Thread(target=fetch_logs)
        thread.start()

    def on_logs_output(self, output):
        """Event handler for logs output."""
        pass

    def get_secrets(self, namespace):
        """Fetch secrets in the specified namespace using Kubernetes SDK asynchronously."""
        def fetch_secrets():
            try:
                secrets = self.core_v1.list_namespaced_secret(namespace)
                output = "\n".join(secret.metadata.name for secret in secrets.items)
                Clock.schedule_once(lambda dt: self.dispatch('on_secrets_output', output), 0)
            except ApiException as e:
                error_output = f"Error fetching secrets: {e.reason} ({e.status})"
                Clock.schedule_once(lambda dt: self.dispatch('on_secrets_output', error_output), 0)
            except Exception as e:
                error_output = f"Error fetching secrets: {str(e)}"
                Clock.schedule_once(lambda dt: self.dispatch('on_secrets_output', error_output), 0)

        thread = threading.Thread(target=fetch_secrets)
        thread.start()

    def on_secrets_output(self, output):
        """Event handler for secrets output."""
        pass

    def get_deployments(self, namespace):
        """Fetch deployments in the specified namespace using Kubernetes SDK asynchronously."""
        def fetch_deployments():
            try:
                deployments = self.apps_v1.list_namespaced_deployment(namespace)
                output = "\n".join(deployment.metadata.name for deployment in deployments.items)
                Clock.schedule_once(lambda dt: self.dispatch('on_deployments_output', output), 0)
            except ApiException as e:
                error_output = f"Error fetching deployments: {e.reason} ({e.status})"
                Clock.schedule_once(lambda dt: self.dispatch('on_deployments_output', error_output), 0)
            except Exception as e:
                error_output = f"Error fetching deployments: {str(e)}"
                Clock.schedule_once(lambda dt: self.dispatch('on_deployments_output', error_output), 0)

        thread = threading.Thread(target=fetch_deployments)
        thread.start()

    def on_deployments_output(self, output):
        """Event handler for deployments output."""
        pass