from app.shared.schemas.base import BaseSchema


class PodSpec(BaseSchema):
    name: str
    privileged: bool


class KubernetesRawResponse(BaseSchema):
    cluster: str
    pods: list[PodSpec]


class KubernetesParsedData(BaseSchema):
    cluster: str
    privileged_pods: list[PodSpec]
