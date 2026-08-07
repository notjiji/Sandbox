"""Port scanner unit tests."""

from app.plugins.base.plugin import ScanTarget
from app.plugins.ports.banners import extract_from_banner
from app.plugins.ports.nmap_probe import _parse_nmap_xml
from app.plugins.ports.parser import parse
from app.plugins.ports.rules import evaluate_rules, rule_rdp_exposed
from app.plugins.ports.schemas import NmapServiceRaw, PortProbeRaw, PortsRawResponse
from app.plugins.ports.scanner import merge_nmap_into_probes

ASSET = ScanTarget(asset_id="1", identifier="203.0.113.10", asset_type="public_ip")


def test_extract_openssh_banner() -> None:
    service, product, version = extract_from_banner(22, "SSH-2.0-OpenSSH_9.2p1 Debian-2+deb12u2")
    assert service == "ssh"
    assert product == "OpenSSH"
    assert version == "9.2p1"


def test_parser_maps_ssh_service() -> None:
    raw = PortsRawResponse(
        host="203.0.113.10",
        probes=[
            PortProbeRaw(port=22, open=True, banner="SSH-2.0-OpenSSH_9.2p1", version="9.2p1"),
        ],
        nmap_services=[
            NmapServiceRaw(port=22, service_name="ssh", product="OpenSSH", version="9.2"),
        ],
        nmap_used=True,
    )
    parsed = parse(raw)
    ssh = parsed.service_on_port(22)
    assert ssh is not None
    assert ssh.service == "ssh"
    assert ssh.product == "OpenSSH"
    assert ssh.version == "9.2"


def test_rules_flag_rdp_exposed() -> None:
    raw = PortsRawResponse(
        host="203.0.113.10",
        probes=[PortProbeRaw(port=3389, open=True)],
    )
    parsed = parse(raw)
    finding = rule_rdp_exposed(parsed, ASSET, "ports")
    assert finding is not None
    assert finding.rule_id == "PORT_RDP_EXPOSED"


def test_rules_flag_mysql_redis_mongodb() -> None:
    raw = PortsRawResponse(
        host="203.0.113.10",
        probes=[
            PortProbeRaw(port=3306, open=True, banner="5.7.33-log"),
            PortProbeRaw(port=6379, open=True, banner="+PONG"),
            PortProbeRaw(port=27017, open=True),
        ],
    )
    parsed = parse(raw)
    findings = evaluate_rules(parsed, ASSET, plugin_id="ports")
    codes = {finding.rule_id for finding in findings}
    assert "PORT_MYSQL_PUBLIC" in codes
    assert "PORT_REDIS_PUBLIC" in codes
    assert "PORT_MONGODB_PUBLIC" in codes


def test_parse_nmap_xml() -> None:
    xml = """
    <nmaprun>
      <host><ports>
        <port protocol="tcp" portid="22"><state state="open"/>
          <service name="ssh" product="OpenSSH" version="9.2"/>
        </port>
      </ports></host>
    </nmaprun>
    """
    services = _parse_nmap_xml(xml)
    assert services[0].port == 22
    assert services[0].product == "OpenSSH"


def test_merge_nmap_into_probes() -> None:
    probes = [PortProbeRaw(port=22, open=True, banner="SSH-2.0-OpenSSH_9.2p1")]
    merged = merge_nmap_into_probes(
        probes,
        [NmapServiceRaw(port=22, service_name="ssh", product="OpenSSH", version="9.2")],
    )
    assert merged[0].version == "9.2"
