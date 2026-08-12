from app.monitoring.enums import AlertSeverity
from app.monitoring.schemas import AgentIngestRequest, MetricsPayload, SecurityPayload, SshCheck
from app.monitoring.services.alert_engine import evaluate_ingest


def test_alert_engine_cpu_and_ssh() -> None:
    payload = AgentIngestRequest(
        metrics=MetricsPayload(cpu_percent=91, ram_percent=10, disk_percent=10),
        security=SecurityPayload(
            ssh=SshCheck(permit_root_login=True, password_authentication=True),
        ),
    )
    codes = {item.code: item for item in evaluate_ingest(payload)}
    assert "CPU_HIGH" in codes
    assert codes["CPU_HIGH"].severity == AlertSeverity.HIGH
    assert "SSH_ROOT_LOGIN" in codes
    assert "SSH_PASSWORD_AUTH" in codes
    assert "RAM_HIGH" not in codes


def test_alert_engine_disk_critical_beats_high() -> None:
    payload = AgentIngestRequest(metrics=MetricsPayload(disk_percent=96))
    codes = [item.code for item in evaluate_ingest(payload)]
    assert codes == ["DISK_CRITICAL"]
