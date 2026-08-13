from datetime import datetime

from pydantic import ConfigDict, Field

from app.monitoring.enums import AgentStatus, AlertSeverity, AlertStatus
from app.shared.schemas.base import BaseSchema


class AgentPayloadSchema(BaseSchema):
    """Agent payloads ignore unknown fields so older/newer agents keep working."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")


class ProcessInfo(AgentPayloadSchema):
    pid: int | None = None
    name: str = ""
    cpu: float | None = None
    rss_mb: float | None = None
    user: str | None = None


class DiskFilesystem(AgentPayloadSchema):
    filesystem: str
    total_gb: float | None = Field(default=None, ge=0)
    used_gb: float | None = Field(default=None, ge=0)
    available_gb: float | None = Field(default=None, ge=0)
    usage_percent: float | None = Field(default=None, ge=0, le=100)


class ServiceInfo(AgentPayloadSchema):
    """Linux systemd unit fact — status only, no malice classification."""

    name: str = Field(max_length=255)
    status: str = Field(default="UNKNOWN", max_length=32)


class MetricsPayload(AgentPayloadSchema):
    cpu_usage: float | None = Field(default=None, ge=0, le=100)
    cpu_percent: float | None = Field(default=None, ge=0, le=100)
    load_1m: float | None = Field(default=None, ge=0)
    load_avg: list[float] | None = None
    cores: int | None = Field(default=None, ge=1)
    total_mb: float | None = Field(default=None, ge=0)
    used_mb: float | None = Field(default=None, ge=0)
    available_mb: float | None = Field(default=None, ge=0)
    usage_percent: float | None = Field(default=None, ge=0, le=100)
    ram_percent: float | None = Field(default=None, ge=0, le=100)
    ram_used_mb: float | None = Field(default=None, ge=0)
    ram_total_mb: float | None = Field(default=None, ge=0)
    disks: list[DiskFilesystem] = Field(default_factory=list)
    disk_percent: float | None = Field(default=None, ge=0, le=100)
    disk_used_gb: float | None = Field(default=None, ge=0)
    disk_total_gb: float | None = Field(default=None, ge=0)
    uptime_seconds: int | None = Field(default=None, ge=0)
    boot_time: datetime | None = None
    last_reboot_at: datetime | None = None
    process_count: int | None = Field(default=None, ge=0)
    processes: list[ProcessInfo] = Field(default_factory=list)
    services: list[ServiceInfo] = Field(default_factory=list)
    network_rx_bytes_sec: float | None = Field(default=None, ge=0)
    network_tx_bytes_sec: float | None = Field(default=None, ge=0)


class FirewallCheck(AgentPayloadSchema):
    enabled: bool | None = None
    backend: str | None = None
    default_incoming: str | None = None
    default_outgoing: str | None = None


class SshCheck(AgentPayloadSchema):
    permit_root_login: bool | None = None
    permit_root_login_raw: str | None = None
    password_authentication: bool | None = None
    password_authentication_raw: str | None = None
    pubkey_authentication: bool | None = None
    pubkey_authentication_raw: str | None = None
    port: int | None = None
    protocol: str | None = None
    config_source: str | None = None


class Fail2BanCheck(AgentPayloadSchema):
    installed: bool | None = None
    enabled: bool | None = None
    running: bool | None = None
    jails: list[str] = Field(default_factory=list)
    jail_count: int | None = Field(default=None, ge=0)
    banned_ips: int | None = Field(default=None, ge=0)


class DockerContainerInfo(AgentPayloadSchema):
    name: str = ""
    status: str | None = None
    image: str | None = None
    cpu_percent: float | None = None
    memory_mb: float | None = None
    restart_count: int | None = Field(default=None, ge=0)


class DockerCheck(AgentPayloadSchema):
    installed: bool | None = None
    running: bool | None = None
    version: str | None = None
    containers: int | None = Field(default=None, ge=0)
    containers_running: int | None = Field(default=None, ge=0)
    containers_stopped: int | None = Field(default=None, ge=0)
    images: int | None = Field(default=None, ge=0)
    container_list: list[DockerContainerInfo] = Field(default_factory=list)


class UpdatesCheck(AgentPayloadSchema):
    available: int | None = Field(default=None, ge=0)
    security: int | None = Field(default=None, ge=0)
    manager: str | None = None
    reboot_required: bool | None = None


class SystemInfo(AgentPayloadSchema):
    os: str | None = None
    kernel: str | None = None
    arch: str | None = None
    hostname: str | None = None


class SecurityPayload(AgentPayloadSchema):
    firewall: FirewallCheck | None = None
    ssh: SshCheck | None = None
    fail2ban: Fail2BanCheck | None = None
    docker: DockerCheck | None = None
    updates: UpdatesCheck | None = None
    system: SystemInfo | None = None


class AgentIngestRequest(AgentPayloadSchema):
    collected_at: datetime | None = None
    agent_version: str | None = Field(default=None, max_length=32)
    hostname: str | None = Field(default=None, max_length=255)
    metrics: MetricsPayload = Field(default_factory=MetricsPayload)
    security: SecurityPayload = Field(default_factory=SecurityPayload)


class AgentIngestResponse(BaseSchema):
    accepted: bool = True
    agent_status: AgentStatus
    alerts_open: int = 0
    next_interval_seconds: int = 30


class AgentRegisterRequest(AgentPayloadSchema):
    enrollment_token: str = Field(min_length=8, max_length=255)
    hostname: str | None = Field(default=None, max_length=255)
    agent_version: str | None = Field(default=None, max_length=32)


class AgentRegisterResponse(BaseSchema):
    agent_id: str
    asset_id: str
    credential: str
    next_interval_seconds: int = 30


class EnrollmentResponse(BaseSchema):
    agent_id: str
    asset_id: str
    enrollment_token: str
    expires_at: datetime
    status: AgentStatus
    install_command: str
    python_command: str
    api_url: str


class AgentSummary(BaseSchema):
    id: str
    asset_id: str
    asset_name: str | None = None
    project_id: str
    status: AgentStatus
    hostname: str | None = None
    agent_version: str | None = None
    last_seen_at: datetime | None = None
    enrolled_at: datetime | None = None


class SnapshotSummary(BaseSchema):
    collected_at: datetime
    cpu_percent: float | None = None
    ram_percent: float | None = None
    disk_percent: float | None = None
    load_1m: float | None = None
    network_rx_bytes_sec: float | None = None
    network_tx_bytes_sec: float | None = None
    uptime_seconds: int | None = None
    process_count: int | None = None


class MetricSample(BaseSchema):
    collected_at: datetime
    value: float


class MetricSeries(BaseSchema):
    metric_type: str
    unit: str
    points: list[MetricSample] = Field(default_factory=list)


class MetricsHistoryResponse(BaseSchema):
    hours: int
    series: list[MetricSeries] = Field(default_factory=list)


class AlertSummary(BaseSchema):
    id: str
    alert_code: str
    title: str
    message: str | None = None
    evidence: str | None = None
    severity: AlertSeverity
    status: AlertStatus
    first_seen_at: datetime
    last_seen_at: datetime
    resolved_at: datetime | None = None


class MonitoringOverview(BaseSchema):
    agent: AgentSummary | None = None
    latest: SnapshotSummary | None = None
    metrics: MetricsPayload | None = None
    security: SecurityPayload | None = None
    alerts: list[AlertSummary] = Field(default_factory=list)
    history: list[SnapshotSummary] = Field(default_factory=list)


class OrgServerSecurityCheck(BaseSchema):
    status: str = "unknown"
    detail: str | None = None


class OrgServerSecuritySummary(BaseSchema):
    ssh: OrgServerSecurityCheck = Field(default_factory=OrgServerSecurityCheck)
    firewall: OrgServerSecurityCheck = Field(default_factory=OrgServerSecurityCheck)
    fail2ban: OrgServerSecurityCheck = Field(default_factory=OrgServerSecurityCheck)
    updates: OrgServerSecurityCheck = Field(default_factory=OrgServerSecurityCheck)
    docker: OrgServerSecurityCheck = Field(default_factory=OrgServerSecurityCheck)


class OrgMonitoringServer(BaseSchema):
    asset_id: str
    asset_name: str
    project_id: str
    status: AgentStatus
    hostname: str | None = None
    cpu_percent: float | None = None
    ram_percent: float | None = None
    disk_percent: float | None = None
    uptime_seconds: int | None = None
    open_alerts: int = 0
    last_seen_at: datetime | None = None
    security: OrgServerSecuritySummary = Field(default_factory=OrgServerSecuritySummary)


class OrgMonitoringOverview(BaseSchema):
    agents_online: int = 0
    agents_delayed: int = 0
    agents_offline: int = 0
    agents_pending: int = 0
    open_alerts: int = 0
    servers: list[OrgMonitoringServer] = Field(default_factory=list)
