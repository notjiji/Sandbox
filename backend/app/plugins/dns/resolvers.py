"""Multi-resolver DNS configuration."""

from dataclasses import dataclass

import dns.resolver


@dataclass(frozen=True)
class ResolverConfig:
    name: str
    nameservers: tuple[str, ...] | None = None


PUBLIC_RESOLVERS: tuple[ResolverConfig, ...] = (
    ResolverConfig(name="system", nameservers=None),
    ResolverConfig(name="cloudflare", nameservers=("1.1.1.1", "1.0.0.1")),
    ResolverConfig(name="google", nameservers=("8.8.8.8", "8.8.4.4")),
    ResolverConfig(name="quad9", nameservers=("9.9.9.9", "149.112.112.112")),
    ResolverConfig(name="opendns", nameservers=("208.67.222.222", "208.67.220.220")),
)


def make_resolver(config: ResolverConfig, timeout: float) -> dns.resolver.Resolver:
    resolver = dns.resolver.Resolver(configure=config.nameservers is None)
    if config.nameservers:
        resolver.nameservers = list(config.nameservers)
    resolver.lifetime = timeout
    return resolver
