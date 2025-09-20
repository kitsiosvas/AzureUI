import subprocess
import threading
from kivy.clock import Clock
from kivy.event import EventDispatcher
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from datetime import datetime, timezone
from humanize import naturaltime
import logging
import json


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
        self.register_event_type('on_describe_output')

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
                now = datetime.now(timezone.utc)
                pod_data = [
                    {
                        "name": pod.metadata.name,
                        "status": pod.status.phase,
                        "age": naturaltime(now - pod.metadata.creation_timestamp.replace(tzinfo=timezone.utc)),
                        "restarts": sum(
                            status.restart_count for status in (pod.status.container_statuses or [])
                        )
                    }
                    for pod in pods.items
                ]
                Clock.schedule_once(lambda dt: self.dispatch('on_pods_output', pod_data), 0)
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

    def get_describe_pod(self, pod, namespace):
        """Fetch detailed description of a pod using Kubernetes SDK asynchronously."""
        def fetch_describe():
            try:
                # Get pod details
                pod_obj = self.core_v1.read_namespaced_pod(name=pod, namespace=namespace)
                
                # Build formatted output like kubectl describe
                lines = []
                lines.append(f"Name:         {pod_obj.metadata.name}")
                lines.append(f"Namespace:    {pod_obj.metadata.namespace}")
                lines.append(f"Priority:     {getattr(pod_obj, 'priority', 0) or 0}")
                if pod_obj.spec.node_name:
                    lines.append(f"Node:         {pod_obj.spec.node_name}/{pod_obj.status.host_ip or 'N/A'}")
                lines.append(f"Start Time:   {pod_obj.metadata.creation_timestamp}")
                lines.append(f"Labels:       {json.dumps(pod_obj.metadata.labels) or '<none>':10}")
                lines.append(f"Annotations:  {json.dumps(pod_obj.metadata.annotations) or '<none>':10}")
                lines.append(f"Status:       {pod_obj.status.phase}")
                if pod_obj.status.pod_ip:
                    lines.append(f"IP:           {pod_obj.status.pod_ip}")
                lines.append("IPs:")
                lines.append(f"  IP:  {pod_obj.status.pod_ip or 'N/A'}")
                
                # Containers
                lines.append("Containers:")
                for container in pod_obj.spec.containers:
                    lines.append(f"  {container.name}:")
                    lines.append(f"    Container ID:   {pod_obj.status.container_statuses[0].container_id if pod_obj.status.container_statuses else 'N/A'}")  # Simplify for single; extend for multi
                    lines.append(f"    Image:          {container.image}")
                    # State (Running/Waiting/Terminated)
                    if pod_obj.status.container_statuses:
                        state = pod_obj.status.container_statuses[0].state  # Assume first; loop for multi
                        if state.running:
                            lines.append(f"    State:          Running")
                            lines.append(f"      Started:      {state.running.started_at}")
                        elif state.waiting:
                            lines.append(f"    State:          Waiting")
                            lines.append(f"      Reason:        {state.waiting.reason}")
                        elif state.terminated:
                            lines.append(f"    State:          Terminated")
                            lines.append(f"      Reason:        {state.terminated.reason}")
                    lines.append(f"    Ready:          {pod_obj.status.container_statuses[0].ready if pod_obj.status.container_statuses else 'False'}")
                    lines.append(f"    Restart Count:  {pod_obj.status.container_statuses[0].restart_count if pod_obj.status.container_statuses else 0}")
                    lines.append("    Environment:    <none>")
                    lines.append("    Mounts:")
                    for volume_mount in container.volume_mounts or []:
                        lines.append(f"      {volume_mount.mount_path} from {volume_mount.name} ({'ro' if volume_mount.read_only else 'rw'})")
                
                # Conditions
                lines.append("Conditions:")
                lines.append("  Type              Status")
                for cond in pod_obj.status.conditions or []:
                    status = "True " if cond.status == "True" else "False" if cond.status == "False" else cond.status
                    lines.append(f"  {cond.type:<18} {status:<6}")
                
                # Volumes
                if pod_obj.spec.volumes:
                    lines.append("Volumes:")
                    for vol in pod_obj.spec.volumes:
                        lines.append(f"  {vol.name}:")
                        lines.append(f"    Type:            {type(vol).__name__} ({vol.__dict__})")  # Simplified; expand as needed
                
                lines.append(f"QoS Class:           {getattr(pod_obj, 'qos_class', '<none>')}")
                lines.append("Node-Selectors:      <none>")
                lines.append("Tolerations:         <none>")  # Add parsing if needed
                
                output = "\n".join(lines)
                Clock.schedule_once(lambda dt: self.dispatch('on_describe_output', output), 0)
            except ApiException as e:
                error_output = f"Error describing pod: {e.reason} ({e.status})"
                Clock.schedule_once(lambda dt: self.dispatch('on_describe_output', error_output), 0)
            except Exception as e:
                error_output = f"Error describing pod: {str(e)}"
                Clock.schedule_once(lambda dt: self.dispatch('on_describe_output', error_output), 0)

        thread = threading.Thread(target=fetch_describe)
        thread.start()

    def on_describe_output(self, output):
        """Event handler for describe output."""
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