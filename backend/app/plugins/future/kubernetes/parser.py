from app.plugins.future.kubernetes.schemas import KubernetesParsedData, KubernetesRawResponse


def parse(raw: KubernetesRawResponse) -> KubernetesParsedData:
    privileged = [pod for pod in raw.pods if pod.privileged]
    return KubernetesParsedData(cluster=raw.cluster, privileged_pods=privileged)
