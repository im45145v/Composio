"""The page reader must refuse private addresses and unsafe redirects."""

from __future__ import annotations

import ipaddress
from urllib.parse import urlsplit

import httpx
import pytest

from app.research.errors import UnsafeURL
from app.research.reader import PageReader
from app.research.safety import screen_url


class StaticResolver:
    def __init__(self, mapping: dict[str, str]) -> None:
        self.mapping = mapping

    def resolve(self, host: str):
        if host not in self.mapping:
            raise UnsafeURL("The host could not be resolved.", code="unresolved_host")
        return [ipaddress.ip_address(self.mapping[host])]


def test_screen_blocks_shorthand_and_multicast_addresses():
    for raw in (
        "http://127.1/",
        "http://10.1/",
        "http://192.168.1/",
        "http://172.16.1/",
        "http://0177.0.0.1/",
        "http://0x7f.0x0.0x0.0x1/",
        "http://224.0.0.1/",
        "http://0300.0250.0001.0001/",
    ):
        with pytest.raises(UnsafeURL):
            screen_url(raw)


def test_screen_blocks_private_metadata_and_unsupported_schemes():
    for raw in (
        "http://127.0.0.1/secret",
        "http://2130706433/",
        "http://0x7f000001/",
        "http://169.254.169.254/latest/meta-data",
        "http://10.1.2.3/",
        "http://192.168.0.5/",
        "http://172.16.0.4/",
        "http://[::1]/",
        "http://localhost/admin",
        "http://metadata.google.internal/computeMetadata/v1/",
        "http://user:pass@docs.example/oauth",
        "file:///etc/passwd",
        "gopher://docs.example/",
        "http://docs.example:22/",
    ):
        with pytest.raises(UnsafeURL):
            screen_url(raw)


def test_reader_does_not_follow_a_redirect_to_a_private_address():
    requested: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested.append(request)
        return httpx.Response(302, headers={"location": "http://127.0.0.1/secret"})

    reader = PageReader(
        resolver=StaticResolver({"docs.example": "93.184.216.34"}),
        transport=httpx.MockTransport(handler),
        max_redirects=3,
    )
    with pytest.raises(UnsafeURL) as caught:
        reader.read("https://docs.example/oauth")
    assert caught.value.code == "unsafe_redirect"
    assert [str(request.url) for request in requested] == ["https://93.184.216.34/oauth"]
    assert requested[0].headers["host"] == "docs.example"
    assert requested[0].extensions["sni_hostname"] == "docs.example"
    assert all("127.0.0.1" not in str(request.url) for request in requested)


def test_reader_pins_each_redirect_and_keeps_the_public_url():
    requested: list[tuple[str, str | None]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested.append((str(request.url), request.headers.get("host")))
        host = urlsplit(str(request.url)).hostname
        if host == "93.184.216.34" and request.url.path == "/oauth":
            return httpx.Response(302, headers={"location": "/start"})
        if host == "93.184.216.34":
            return httpx.Response(302, headers={"location": "https://developer.vendor.example/docs"})
        return httpx.Response(
            200,
            headers={"content-type": "text/plain"},
            text="Create an OAuth app in the developer settings.",
        )

    reader = PageReader(
        resolver=StaticResolver(
            {"docs.example": "93.184.216.34", "developer.vendor.example": "1.1.1.1"}
        ),
        transport=httpx.MockTransport(handler),
    )
    page = reader.read("https://docs.example/oauth")
    assert page.url == "https://developer.vendor.example/docs"
    assert "Create an OAuth app" in page.text
    assert requested == [
        ("https://93.184.216.34/oauth", "docs.example"),
        ("https://93.184.216.34/start", "docs.example"),
        ("https://1.1.1.1/docs", "developer.vendor.example"),
    ]


def test_reader_skips_script_text_and_limits_size():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/oauth":
            html = "<html><head><title>OAuth</title><script>alert(1)</script></head><body><p>Create an OAuth app.</p></body></html>"
            return httpx.Response(200, headers={"content-type": "text/html; charset=utf-8"}, text=html)
        return httpx.Response(200, headers={"content-type": "text/plain"}, content=b"x" * 50)

    reader = PageReader(
        resolver=StaticResolver({"docs.example": "93.184.216.34"}),
        transport=httpx.MockTransport(handler),
        max_bytes=20,
    )
    page = PageReader(
        resolver=StaticResolver({"docs.example": "93.184.216.34"}),
        transport=httpx.MockTransport(handler),
    ).read("https://docs.example/oauth")
    assert page.url == "https://docs.example/oauth"
    assert page.title == "OAuth"
    assert "Create an OAuth app." in page.text
    assert "alert" not in page.text

    from app.research.errors import ReaderError

    with pytest.raises(ReaderError) as caught:
        reader.read("https://docs.example/big")
    assert caught.value.code == "page_too_large"


def test_reader_refuses_a_hostname_that_resolves_privately():
    def handler(_request: httpx.Request) -> httpx.Response:
        raise AssertionError("private DNS result must not be fetched")

    reader = PageReader(
        resolver=StaticResolver({"evil.example": "10.0.0.5"}),
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(UnsafeURL) as caught:
        reader.read("https://evil.example/docs")
    assert caught.value.code == "blocked_address"
