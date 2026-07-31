"""Report generation engine — builds reports from findings and risk data."""


class ReportEngine:
    def generate(self, *, report_id: str) -> dict:
        raise NotImplementedError("Report engine not implemented yet")
