class Subscription:
    def __init__(self, name, region, environment, resource_groups):
        self.name = name
        self.region = region
        self.environment = environment
        self.resource_groups = resource_groups  # This should map resource group names to their details

    def __repr__(self):
        return f"Subscription(name={self.name}, region={self.region}, environment={self.environment})"