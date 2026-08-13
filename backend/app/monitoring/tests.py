from app.monitoring.enums import AlertSeverity
from app.monitoring.schemas import (
    AgentIngestRequest,
    DiskFilesystem,
    MetricsPayload,
    SecurityPayload,
    SshCheck,
)
from app.monitoring.services.alert_engine import evaluate_ingest


def test_alert_engine_cpu_and_ssh() -> None:
    payload = AgentIngestRequest(
        metrics=MetricsPayload(cpu_usage=91, cores=4, load_1m=2.1, ram_percent=10, disk_percent=10),
        security=SecurityPayload(
            ssh=SshCheck(
                permit_root_login=True,
                permit_root_login_raw="yes",
                password_authentication=True,
                password_authentication_raw="yes",
                pubkey_authentication=False,
                pubkey_authentication_raw="no",
                port=22,
                protocol="2",
            ),
        ),
    )
    codes = {item.code: item for item in evaluate_ingest(payload)}
    assert "CPU_HIGH" in codes
    assert codes["CPU_HIGH"].severity == AlertSeverity.HIGH
    assert "cores=4" in (codes["CPU_HIGH"].evidence or "")
    assert "SSH_ROOT_LOGIN" in codes
    assert "SSH_PASSWORD_AUTH" in codes
    assert codes["SSH_PASSWORD_AUTH"].severity == AlertSeverity.MEDIUM
    assert "Recommendation:" in codes["SSH_PASSWORD_AUTH"].message
    assert "SSH_PUBKEY_DISABLED" in codes
    assert "RAM_HIGH" not in codes


def test_alert_engine_fail2ban_not_installed() -> None:
    from app.monitoring.schemas import Fail2BanCheck

    payload = AgentIngestRequest(
        security=SecurityPayload(fail2ban=Fail2BanCheck(installed=False, enabled=False, running=False)),
    )
    codes = {item.code: item for item in evaluate_ingest(payload)}
    assert "FAIL2BAN_NOT_INSTALLED" in codes
    assert "FAIL2BAN_INACTIVE" not in codes


def test_alert_engine_disk_thresholds_per_filesystem() -> None:
    payload = AgentIngestRequest(
        metrics=MetricsPayload(
            disks=[
                DiskFilesystem(filesystem="/", usage_percent=72.0),
                DiskFilesystem(filesystem="/var", usage_percent=84.0),
                DiskFilesystem(filesystem="/data", usage_percent=96.0),
            ]
        )
    )
    codes = {item.code: item for item in evaluate_ingest(payload)}
    assert "DISK_WARN__var" in codes
    assert codes["DISK_WARN__var"].severity == AlertSeverity.MEDIUM
    assert "DISK_CRITICAL__data" in codes
    assert "DISK_HIGH__root" not in codes
    assert "DISK_CRITICAL__root" not in codes


def test_alert_engine_disk_critical_beats_high() -> None:
    payload = AgentIngestRequest(metrics=MetricsPayload(disk_percent=96))
    codes = [item.code for item in evaluate_ingest(payload)]
    assert codes == ["DISK_CRITICAL__root"]
