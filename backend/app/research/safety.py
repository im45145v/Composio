"""Public-URL checks. Fetches never follow a private, local, or metadata address."""

from __future__ import annotations

import ipaddress
import re
import socket
from urllib.parse import urlsplit

from app.research.errors import UnsafeURL

ALLOWED_SCHEMES = {"http", "https"}
ALLOWED_PORTS = {None, 80, 443}
BLOCKED_HOSTS = {
    "localhost",
    "localhost.localdomain",
    "metadata",
    "metadata.google.internal",
    "metadata.google.com",
    "host.docker.internal",
    "gateway.docker.internal",
}
BLOCKED_SUFFIXES = (".localhost", ".local", ".internal", ".localdomain")
EXTRA_BLOCKED = (
    ipaddress.ip_network("100.100.100.200/32"),
    ipaddress.ip_network("fd00:ec2::254/128"),
)
OCTAL_HOST = re.compile(r"(?:0\d+\.){3}0\d+")
HEX_HOST = re.compile(r"0x[0-9a-f]+", re.IGNORECASE)


class Resolver:
    def resolve(self, host: str) -> list[ipaddress.IPv4Address | ipaddress.IPv6Address]:
        raise NotImplementedError


class SystemResolver(Resolver):
    def resolve(self, host: str) -> list[ipaddress.IPv4Address | ipaddress.IPv6Address]:
        try:
            infos = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
        except socket.gaierror as exc:
            raise UnsafeURL("The host could not be resolved.", code="unresolved_host") from exc
        addresses: list[ipaddress.IPv4Address | ipaddress.IPv6Address] = []
        for info in infos:
            addresses.append(ipaddress.ip_address(info[4][0]))
        if not addresses:
            raise UnsafeURL("The host could not be resolved.", code="unresolved_host")
        return addresses


def ip_literal(host: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    try:
        parsed: ipaddress.IPv4Address | ipaddress.IPv6Address | None = ipaddress.ip_address(host)
    except ValueError:
        parsed = None
    if parsed is None and host.isdigit():
        number = int(host)
        if 0 <= number <= 0xFFFFFFFF:
            parsed = ipaddress.IPv4Address(number)
    if isinstance(parsed, ipaddress.IPv6Address) and parsed.ipv4_mapped is not None:
        parsed = parsed.ipv4_mapped
    return parsed


def is_public_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped
    if any(ip in network for network in EXTRA_BLOCKED):
        return False
    return bool(ip.is_global)


def screen_url(raw: str) -> str:
    """Reject schemes, credentials, ports, and addresses that are unsafe before DNS."""

    candidate = raw.strip()
    if not candidate or any(ord(char) < 32 or ord(char) == 127 for char in candidate):
        raise UnsafeURL("Enter an http or https URL.")
    parsed = urlsplit(candidate)
    scheme = parsed.scheme.lower()
    if scheme not in ALLOWED_SCHEMES:
        raise UnsafeURL("Only http and https URLs can be read.", code="unsupported_protocol")
    if parsed.username or parsed.password:
        raise UnsafeURL("URLs with embedded credentials are not accepted.")
    host = parsed.hostname
    if not host:
        raise UnsafeURL("The URL needs a public host.")
    host = host.lower().rstrip(".")
    try:
        host_ascii = host.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise UnsafeURL("The host name is not valid.") from exc
    if host_ascii in BLOCKED_HOSTS or host_ascii.endswith(BLOCKED_SUFFIXES):
        raise UnsafeURL("That address is not a public website.", code="blocked_address")
    if OCTAL_HOST.fullmatch(host_ascii) or HEX_HOST.fullmatch(host_ascii):
        raise UnsafeURL("That address is not a public website.", code="blocked_address")
    if parsed.port not in ALLOWED_PORTS:
        raise UnsafeURL("Only ports 80 and 443 can be read.")
    literal = ip_literal(host_ascii)
    if literal is not None and not is_public_ip(literal):
        raise UnsafeURL("That address is not a public website.", code="blocked_address")
    path = parsed.path or "/"
    query = f"?{parsed.query}" if parsed.query else ""
    return f"{scheme}://{host_ascii}{path}{query}"


def assert_resolves_public(url: str, resolver: Resolver) -> None:
    host = urlsplit(url).hostname or ""
    if ip_literal(host) is not None:
        return
    addresses = resolver.resolve(host)
    if any(not is_public_ip(ip) for ip in addresses):
        raise UnsafeURL("That host resolves to a non-public address.", code="blocked_address")
