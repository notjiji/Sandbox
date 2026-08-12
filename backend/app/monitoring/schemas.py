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


class MetricsPayload(AgentPayloadSchema):
    cpu_percent: float | None = Field(default=None, ge=0, le=100)
    ram_percent: float | None = Field(default=None, ge=0, le=100)
    ram_used_mb: float | None = Field(default=None, ge=0)
    ram_total_mb: float | None = Field(default=None, ge=0)
    disk_percent: float | None = Field(default=None, ge=0, le=100)
    disk_used_gb: float | None = Field(default=None, ge=0)
    disk_total_gb: float | None = Field(default=None, ge=0)
    uptime_seconds: int | None = Field(default=None, ge=0)
    load_avg: list[float] | None = None
    process_count: int | None = Field(default=None, ge=0)
    processes: list[ProcessInfo] = Field(default_factory=list)


class FirewallCheck(AgentPayloadSchema):
    enabled: bool | None = None
    backend: str | None = None
    default_incoming: str | None = None


class SshCheck(AgentPayloadSchema):
    permit_root_login: bool | None = None
    password_authentication: bool | None = None
    port: int | None = None


class Fail2BanCheck(AgentPayloadSchema):
    enabled: bool | None = None
    jails: list[str] = Field(default_factory=list)


class DockerCheck(AgentPayloadSchema):
    installed: bool | None = None
    running: bool | None = None
    containers: int | None = None


class UpdatesCheck(AgentPayloadSchema):
    available: int | None = None
    security: int | None = None


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
    next_interval_seconds: int = 60


class EnrollmentResponse(BaseSchema):
    agent_id: str
    asset_id: str
    token: str
    status: AgentStatus
    install_command: str
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
    uptime_seconds: int | None = None
    process_count: int | None = None


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


class OrgMonitoringServer(BaseSchema):
    asset_id: str
    asset_name: str
    project_id: str
    status: AgentStatus
    hostname: str | None = None
    cpu_percent: float | None = None
    ram_percent: float | None = None
    disk_percent: float | None = None
    open_alerts: int = 0
    last_seen_at: datetime | None = None


class OrgMonitoringOverview(BaseSchema):
    agents_online: int = 0
    agents_offline: int = 0
    agents_pending: int = 0
    open_alerts: int = 0
    servers: list[OrgMonitoringServer] = Field(default_factory=list)
