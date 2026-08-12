from __future__ import annotations

from agent.collectors import collect_docker, collect_system
from agent.security import fail2ban, firewall, ssh, updates


def collect_security() -> dict:
    return {
        "firewall": firewall.collect(),
        "ssh": ssh.collect(),
        "fail2ban": fail2ban.collect(),
        "docker": collect_docker(),
        "updates": updates.collect(),
        "system": collect_system(),
    }
