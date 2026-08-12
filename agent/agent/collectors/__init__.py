from __future__ import annotations

from agent.collectors import cpu, disk, docker, memory, processes, services, system, uptime


def collect_metrics() -> dict:
    payload: dict = {}
    payload.update(cpu.collect())
    payload.update(memory.collect())
    payload.update(disk.collect())
    payload.update(uptime.collect())
    payload.update(processes.collect())
    payload.update(services.collect())
    return payload


def collect_system() -> dict:
    return system.collect()


def collect_docker() -> dict | None:
    return docker.collect()
