from app.shared.schemas.base import BaseSchema


class BucketPolicyStatement(BaseSchema):
    effect: str
    principal: str
    action: str


class CloudRawResponse(BaseSchema):
    resource_id: str
    policy_statements: list[BucketPolicyStatement]


class CloudParsedData(BaseSchema):
    resource_id: str
    public_read_allowed: bool
