"""Subdomain takeover fingerprinting and HTTP verification."""

from __future__ import annotations

import re
import urllib.error
import urllib.request

# Expanded dangling-service fingerprints (suffix + HTTP body patterns)
DANGLING_CNAME_SUFFIXES = (
    ".github.io",
    ".herokuapp.com",
    ".azurewebsites.net",
    ".cloudfront.net",
    ".s3.amazonaws.com",
    ".s3-website",
    ".shopify.com",
    ".fastly.net",
    ".pantheonsite.io",
    ".zendesk.com",
    ".ghost.io",
    ".surge.sh",
    ".netlify.app",
    ".vercel.app",
    ".firebaseapp.com",
    ".web.app",
    ".azurefd.net",
    ".trafficmanager.net",
    ".cloudapp.azure.com",
    ".blob.core.windows.net",
    ".herokudns.com",
    ".readme.io",
    ".statuspage.io",
    ".unbouncepages.com",
    ".myshopify.com",
    ".wpengine.com",
    ".thinkific.com",
    ".tumblr.com",
    ".feedpress.me",
    ".helpjuice.com",
    ".helpscoutdocs.com",
    ".gitbooks.io",
    ".customercanvas.com",
)

HTTP_TAKEOVER_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("github", re.compile(r"There isn't a GitHub Pages site here", re.I)),
    ("heroku", re.compile(r"no such app|herokucdn.com/error", re.I)),
    ("shopify", re.compile(r"Sorry, this shop is currently unavailable", re.I)),
    ("fastly", re.compile(r"Fastly error: unknown domain", re.I)),
    ("azure", re.compile(r"404 Web Site not found|Microsoft Azure Web App", re.I)),
    ("s3", re.compile(r"NoSuchBucket|The specified bucket does not exist", re.I)),
    ("ghost", re.compile(r"The thing you were looking for is no longer here", re.I)),
    ("tumblr", re.compile(r"Whatever you were looking for doesn't currently exist", re.I)),
    ("wordpress", re.compile(r"Do you want to register", re.I)),
)


def is_dangling_cname_target(target: str) -> bool:
    lowered = target.lower().rstrip(".")
    return any(lowered.endswith(suffix) for suffix in DANGLING_CNAME_SUFFIXES)


def verify_takeover_http(subdomain: str, *, timeout: float = 8.0) -> str | None:
    for scheme in ("https", "http"):
        url = f"{scheme}://{subdomain}/"
        request = urllib.request.Request(url, headers={"User-Agent": "Sandbox-DNS-Scanner/3.0"})
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = response.read(8192).decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError):
            continue

        for service, pattern in HTTP_TAKEOVER_PATTERNS:
            if pattern.search(body):
                return f"{subdomain} HTTP fingerprint matches {service} takeover page"
    return None
