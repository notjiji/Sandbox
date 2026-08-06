from app.plugins.future.cve.schemas import CveParsedData, CveRawResponse


def parse(raw: CveRawResponse) -> CveParsedData:
    vulnerable = [pkg for pkg in raw.packages if pkg.cve_ids]
    return CveParsedData(host=raw.host, vulnerable_packages=vulnerable)
