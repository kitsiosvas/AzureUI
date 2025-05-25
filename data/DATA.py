from kubernetes.entities import Subscription

SUBSCRIPTIONS = [
    Subscription("sub-apas-sit01", "APAC", "SIT", {
        "rg-apass-bsn0020539-01": ["aks-apass-bsn0020539-01"],
    }),
    Subscription("sub-nau2-sit01", "NA", "SIT", {
        "rg-nau2s-bsn0017692-01": ["aks-nau2s-bsn0017692-03"],
        "rg-nau2s-bsn0020579-01": ["aks-nau2s-bsn0020579-01"]
    }),
    Subscription("sub-eune-sit01", "EMEA", "SIT", {
        "rg-eunes-bsn0020578-01": ["aks-eunes-bsn0020578-01"],
    }),


    Subscription("sub-lau2-prod01", "LATAM", "PROD", {
        "rg-lau2p-bsn0020442-01": ["aks-lau2p-bsn0020442-01"],
    }),
    Subscription("sub-nau2-prod01", "NA", "PROD", {
        "rg-nau2p-bsn0020581-01": ["aks-nau2p-bsn0020581-01"],
    }),
    Subscription("sub-eune-prod01", "EMEA", "PROD", {
        "rg-eunep-bsn0020582-01": ["aks-eunep-bsn0020582-01"],
    }),
]


NAMESPACES = ["global-ai-mlops-sit", "global-ai-cgd-sit", "global-ai-cgd-pci-sit",
              "global-ai-mlops-prod", "global-ai-cgd-prod", "global-ai-cgd-pci-sit"]

ENVIRONMETS = ["SIT", "UAT", "PROD"]

REGIONS = ["APAC", "EMEA", "LATAM", "NA"]



DEFAULT_TEXT_REGION_DROPDOWN = "Select Region"
DEFAULT_TEXT_ENVIRONMET_DROPDOWN = "Select Environment"
DEFAULT_TEXT_SUBSCRIPTION_DROPDOWN = "Select Subscription"
DEFAULT_TEXT_RESOURCE_GROUP_DROPDOWN = "Select Resource Group"
DEFAULT_TEXT_CLUSTER_DROPDOWN = "Select Cluster"
DEFAULT_TEXT_NAMESPACE_DROPDOWN = "Select Namespace"