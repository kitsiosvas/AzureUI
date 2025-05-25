from kubernetes.entities import Subscription

SUBSCRIPTIONS = [
    Subscription("sub-apac-sit", "APAC", "SIT", {
        "rg-apac-sit-01": ["aks-apac-sit-1"],
    }),
    Subscription("sub-na-sit", "NA", "SIT", {
        "rg-na-sit-02": ["aks-na-sit-2"],
        "rg-na-sit-01": ["aks-na-sit-1", "aks-na-sit-3"]
    }),
    Subscription("sub-eune-sit", "EMEA", "SIT", {
        "rg-eune-sit-01": ["aks-eune-sit-1"],
    }),

    Subscription("sub-la-prod", "LATAM", "PROD", {
        "rg-la-prod-01": ["aks-la-prod-1"],
    }),
    Subscription("sub-na-prod", "NA", "PROD", {
        "rg-na-prod-01": ["aks-na-prod-1"],
    }),
    Subscription("sub-eune-prod", "EMEA", "PROD", {
        "rg-eune-prod-01": ["aks-eune-prod-01"],
    }),
]


NAMESPACES = ["global-ai-mlops-sit", "global-ai-cgd-sit", "global-ai-mlops-prod", 
              "global-ai-cgd-prod", "global-ai-cgd-pci-sit"]

ENVIRONMETS = ["SIT", "UAT", "PROD"]

REGIONS = ["APAC", "EMEA", "LATAM", "NA"]



DEFAULT_TEXT_REGION_DROPDOWN = "Select Region"
DEFAULT_TEXT_ENVIRONMET_DROPDOWN = "Select Environment"
DEFAULT_TEXT_SUBSCRIPTION_DROPDOWN = "Select Subscription"
DEFAULT_TEXT_RESOURCE_GROUP_DROPDOWN = "Select Resource Group"
DEFAULT_TEXT_CLUSTER_DROPDOWN = "Select Cluster"
DEFAULT_TEXT_NAMESPACE_DROPDOWN = "Select Namespace"