from app.shared.schemas.base import BaseSchema


class InstalledPackage(BaseSchema):
    name: str
    version: str
    cve_ids: list[str]
    cvss: float | None = None


class CveRawResponse(BaseSchema):
    host: str
    packages: list[InstalledPackage]


class CveParsedData(BaseSchema):
    host: str
    vulnerable_packages: list[InstalledPackage]
