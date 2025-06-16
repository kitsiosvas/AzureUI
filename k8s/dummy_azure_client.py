from kivy.event import EventDispatcher
from kivy.clock import Clock
from datetime import datetime, timezone, timedelta
from humanize import naturaltime
import random

class DummyAzureClient(EventDispatcher):
    def __init__(self):
        super().__init__()
        self.register_event_type('on_merge_output')
        self.register_event_type('on_pods_output')
        self.register_event_type('on_logs_output')
        self.register_event_type('on_secrets_output')
        self.register_event_type('on_deployments_output')

    def safe_load_kube_config(self):
        """Mock loading kube config (no-op)."""
        pass

    def execute_merge(self, subscription, resource_group, cluster_name):
        """Mock merge command, dispatching event with success."""
        def _run_merge(dt):
            output = f"Merged \"{cluster_name}\" as current context in kubeconfig"
            success = True
            self.dispatch('on_merge_output', output, success)
        Clock.schedule_once(_run_merge, 1)  # Simulate async delay

    def on_merge_output(self, output, success):
        """Event handler for merge output."""
        pass

    def get_pods(self, namespace):
        """Mock fetching pods, returning random pod data."""
        def fetch_pods(dt):
            try:
                # Generate 5–50 random pods
                pod_count = random.randint(5, 50)
                now = datetime.now(timezone.utc)
                statuses = ["Running", "Pending", "Failed", "Succeeded"]
                pod_data = [
                    {
                        "name": f"pod-{i+1}",
                        "status": random.choice(statuses),
                        "age": naturaltime(now - timedelta(days=random.randint(0, 7), hours=random.randint(0, 23))),
                        "restarts": random.randint(0, 5)
                    }
                    for i in range(pod_count)
                ]
                self.dispatch('on_pods_output', pod_data)
            except Exception as e:
                self.dispatch('on_pods_output', f"Error fetching pods: {str(e)}")
        Clock.schedule_once(fetch_pods, 1)  # Simulate async delay

    def on_pods_output(self, output):
        """Event handler for pods output."""
        pass

    def get_logs(self, pod, namespace):
        """Mock fetching logs for a pod."""
        def fetch_logs(dt):
            try:
                logs = f"Mock logs for {pod} in namespace {namespace}\n" + \
                       "Sample log line 1\nSample log line 2\n" + \
                       f"Generated at {datetime.now(timezone.utc).isoformat()}"
                self.dispatch('on_logs_output', logs)
            except Exception as e:
                self.dispatch('on_logs_output', f"Error fetching logs: {str(e)}")
        Clock.schedule_once(fetch_logs, 1)  # Simulate async delay

    def on_logs_output(self, output):
        """Event handler for logs output."""
        pass

    def get_secrets(self, namespace):
        """Mock fetching secrets in a namespace."""
        def fetch_secrets(dt):
            try:
                secrets = "\n".join([f"secret-{i+1}" for i in range(random.randint(1, 10))])
                self.dispatch('on_secrets_output', secrets)
            except Exception as e:
                self.dispatch('on_secrets_output', f"Error fetching secrets: {str(e)}")
        Clock.schedule_once(fetch_secrets, 1)  # Simulate async delay

    def on_secrets_output(self, output):
        """Event handler for secrets output."""
        pass

    def get_deployments(self, namespace):
        """Mock fetching deployments in a namespace."""
        def fetch_deployments(dt):
            try:
                deployments = "\n".join([f"deployment-{i+1}" for i in range(random.randint(1, 5))])
                self.dispatch('on_deployments_output', deployments)
            except Exception as e:
                self.dispatch('on_deployments_output', f"Error fetching deployments: {str(e)}")
        Clock.schedule_once(fetch_deployments, 1)  # Simulate async delay

    def on_deployments_output(self, output):
        """Event handler for deployments output."""
        pass