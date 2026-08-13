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


def test_alert_engine_security_updates_medium() -> None:
    from app.monitoring.schemas import UpdatesCheck

    payload = AgentIngestRequest(
        security=SecurityPayload(
            updates=UpdatesCheck(available=17, security=12, manager="apt", reboot_required=False),
        ),
    )
    codes = {item.code: item for item in evaluate_ingest(payload)}
    assert "SECURITY_UPDATES_PENDING" in codes
    assert codes["SECURITY_UPDATES_PENDING"].severity == AlertSeverity.MEDIUM
    assert codes["SECURITY_UPDATES_PENDING"].title == "12 security updates pending"
    assert "UPDATES_AVAILABLE" not in codes


def test_alert_engine_non_security_updates_low() -> None:
    from app.findings.constants import FINDING_SOURCE_MONITORING, MONITORING_PLUGIN
    from app.findings.enums import FindingStatus
    from app.findings.services.monitoring_finding_sync import sync_monitoring_findings
    from app.monitoring.schemas import UpdatesCheck

    payload = AgentIngestRequest(
        security=SecurityPayload(updates=UpdatesCheck(available=5, security=0, manager="apt")),
    )
    codes = {item.code: item for item in evaluate_ingest(payload)}
    assert "UPDATES_AVAILABLE" in codes
    assert codes["UPDATES_AVAILABLE"].severity == AlertSeverity.LOW
    assert "SECURITY_UPDATES_PENDING" not in codes


def test_sync_monitoring_finding_shape() -> None:
    from app.findings.services.monitoring_finding_sync import (
        _category_for_code,
        _description_from_message,
        _extract_recommendation,
    )
    from app.monitoring.services.alert_engine import AlertCandidate

    candidate = AlertCandidate(
        code="SSH_PASSWORD_AUTH",
        title="SSH Password Authentication Enabled",
        message=(
            "Current: PasswordAuthentication yes\n\n"
            "Recommendation: Disable password authentication and use key-based authentication."
        ),
        severity=AlertSeverity.MEDIUM,
        evidence="PasswordAuthentication=yes",
    )

    assert _category_for_code("SSH_PASSWORD_AUTH") == "server_security"
    assert _extract_recommendation(candidate.message) == (
        "Disable password authentication and use key-based authentication."
    )
    assert _description_from_message(candidate.message) == "Current: PasswordAuthentication yes"


def test_normalize_metrics_uses_shared_shape() -> None:
    from app.monitoring.metric_types import CPU_USAGE, DISK_USAGE, LOAD_AVERAGE, MEMORY_USAGE, UPTIME
    from app.monitoring.services.metric_normalizer import normalize_metrics

    points = normalize_metrics(
        MetricsPayload(
            cpu_usage=73.4,
            load_1m=2.14,
            cores=4,
            total_mb=8192,
            used_mb=5412,
            available_mb=2780,
            usage_percent=66.1,
            disks=[
                DiskFilesystem(filesystem="/", usage_percent=72.0, used_gb=72.0, total_gb=100.0, available_gb=28.0),
                DiskFilesystem(filesystem="/var", usage_percent=84.0, used_gb=42.0, total_gb=50.0, available_gb=8.0),
            ],
            uptime_seconds=1480320,
        )
    )
    by_type = {(item.metric_type, (item.labels or {}).get("filesystem")): item for item in points}
    assert by_type[(CPU_USAGE, None)].value == 73.4
    assert by_type[(CPU_USAGE, None)].unit == "percent"
    assert by_type[(MEMORY_USAGE, None)].value == 66.1
    assert by_type[(LOAD_AVERAGE, None)].value == 2.14
    assert by_type[(UPTIME, None)].unit == "seconds"
    assert by_type[(DISK_USAGE, "/")].value == 72.0
    assert by_type[(DISK_USAGE, "/var")].value == 84.0


