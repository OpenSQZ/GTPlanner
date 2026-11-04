"""Security tests for Quick PRD reference fetching (SSRF hardening).

All tests are offline: DNS is replaced by a fake resolver, HTTP by httpx.MockTransport,
and httpcore's real TCP connect is replaced by a recorder that never opens a socket.
These tests prove the logic, not production network behaviour.
"""
import asyncio
import socket
import ssl
import time
import types

import httpcore
import httpx
import pytest
from httpcore._backends.auto import AutoBackend

import gtplanner.agent.prd_generator as gen

PUBLIC_V4 = "93.184.216.34"
PUBLIC_V4_B = "1.1.1.1"
PUBLIC_V6 = "2606:2800:220:1:248:1893:25c8:1946"
HTML = b"<html><head><title>Toko Contoh</title><meta name='description' content='desc'></head><body><p>Halo dunia</p></body></html>"


# ---------------------------------------------------------------- fixtures ---

class Resolver:
    """Fake DNS: explicit mapping, else numeric-only parsing (AI_NUMERICHOST, no network)."""

    def __init__(self, mapping=None):
        self.mapping = mapping or {}
        self.calls = []

    async def __call__(self, host, port):
        self.calls.append((host, port))
        if host in self.mapping:
            value = self.mapping[host]
            return value(len([c for c in self.calls if c[0] == host])) if callable(value) else list(value)
        try:
            infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM, flags=socket.AI_NUMERICHOST)
        except socket.gaierror:
            raise socket.gaierror(f"fake resolver: no record for {host} (internal-dns.corp)")
        return [i[4][0] for i in infos]


class Site:
    """Fake web server behind httpx.MockTransport; records every request it receives."""

    def __init__(self, handler=None):
        self.handler = handler or (lambda req: html_response())
        self.requests = []

    def transport(self):
        def handle(request):
            self.requests.append(request)
            return self.handler(request)
        return httpx.MockTransport(handle)


def html_response(body=HTML, ctype="text/html; charset=utf-8", **kw):
    return httpx.Response(200, headers={"content-type": ctype, **kw.pop("headers", {})}, content=body, **kw)


@pytest.fixture
def connects(monkeypatch):
    """Replace the real TCP connect of httpcore: record and refuse (no socket is ever opened)."""
    calls = []

    async def fake_connect(self, host, port, timeout=None, local_address=None, socket_options=None):
        calls.append({"host": host, "port": port})
        raise httpcore.ConnectError("refused by test recorder")

    monkeypatch.setattr(AutoBackend, "connect_tcp", fake_connect)
    return calls


@pytest.fixture(autouse=True)
def isolated(monkeypatch, connects):
    """Every test starts with fetching enabled, no proxies, a fake resolver and a recording site."""
    for var in (gen.REFERENCE_FETCH_ENV, "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
        monkeypatch.delenv(var, raising=False)
    resolver = Resolver({"example.com": [PUBLIC_V4]})
    site = Site()
    monkeypatch.setattr(gen, "_resolve_host", resolver)
    monkeypatch.setattr(gen, "_build_transport", site.transport)
    return types.SimpleNamespace(resolver=resolver, site=site, connects=connects, monkeypatch=monkeypatch)


def use(isolated, mapping=None, handler=None):
    if mapping is not None:
        isolated.resolver.mapping = mapping
    if handler is not None:
        isolated.site.handler = handler
    return isolated


# ------------------------------------------------------ IP classification ---

BLOCKED_IPS = [
    "127.0.0.1", "127.255.255.254", "0.0.0.0", "0.1.2.3", "10.0.0.1", "172.16.0.1", "172.31.255.255",
    "192.168.1.1", "169.254.169.254", "169.254.0.1", "100.64.0.1", "100.100.100.200", "168.63.129.16",
    "192.0.0.1", "192.0.2.1", "198.18.0.1", "198.51.100.1", "203.0.113.1", "224.0.0.1", "239.255.255.250",
    "240.0.0.1", "255.255.255.255",
    "::", "::1", "::127.0.0.1", "fe80::1", "fe80::1%eth0", "fc00::1", "fd00:ec2::254", "fec0::1", "ff02::1",
    "::ffff:127.0.0.1", "::ffff:169.254.169.254", "::ffff:10.0.0.1",
    "64:ff9b::7f00:1", "64:ff9b::a9fe:a9fe", "64:ff9b:1::1",
    "2002:7f00:1::1", "2002:5db8:d822::1", "2001:0:4136:e378:8000:63bf:3fff:fdd2", "2001:db8::1", "100::1",
    "3fff::1", "not-an-ip", "",
]
PUBLIC_IPS = [PUBLIC_V4, PUBLIC_V4_B, "8.8.8.8", PUBLIC_V6, "2606:4700:4700::1111", "::ffff:93.184.216.34", "64:ff9b::808:808"]


@pytest.mark.parametrize("ip", BLOCKED_IPS)
def test_non_public_ips_are_blocked(ip):
    assert gen.is_public_ip(ip) is False


@pytest.mark.parametrize("ip", PUBLIC_IPS)
def test_public_ips_are_allowed(ip):
    assert gen.is_public_ip(ip) is True


def test_deny_list_does_not_rely_on_is_global():
    import ipaddress
    # These are reported as global by the stdlib but must still be blocked.
    for ip in ("168.63.129.16", "64:ff9b::7f00:1"):
        assert ipaddress.ip_address(ip).is_global is True
        assert gen.is_public_ip(ip) is False


# ------------------------------------------------------- URL validation ---

REJECTED_URLS = [
    ("file:///etc/passwd", "invalid_url"),
    ("ftp://example.com/x", "invalid_url"),
    ("gopher://example.com/", "invalid_url"),
    ("http://0177.0.0.1/", "invalid_url"),
    ("http://user:pw@example.com/", "blocked"),
    ("http://user@169.254.169.254/latest/meta-data/", "blocked"),
    ("http://example.com:22/", "blocked"),
    ("http://example.com:6379/", "blocked"),
    ("http://example.com:11211/health", "blocked"),
    ("http://example.com:8080/", "blocked"),
    ("https://example.com:8443/", "blocked"),
    ("http://localhost/", "blocked"),
    ("http://LOCALHOST/", "blocked"),
    ("http://localhost./", "blocked"),
    ("http://app.localhost/", "blocked"),
    ("http://metadata.google.internal/computeMetadata/v1/", "blocked"),
    ("http://db.internal/", "blocked"),
    ("http://printer.local/", "blocked"),
    ("http://intranet/", "blocked"),
    ("http://2130706433/", "blocked"),
    ("http://0x7f.1/", "blocked"),
    ("http://127.1/", "blocked"),
    ("http://127.0.0.1/", "blocked"),
    ("http://0.0.0.0:80/", "blocked"),
    ("http://169.254.169.254/latest/meta-data/", "blocked"),
    ("http://100.100.100.200/latest/meta-data/", "blocked"),
    ("http://168.63.129.16/", "blocked"),
    ("http://[::1]/", "blocked"),
    ("http://[::ffff:127.0.0.1]/", "blocked"),
    ("http://[fd00:ec2::254]/latest/meta-data/", "blocked"),
    ("http://[64:ff9b::a9fe:a9fe]/", "blocked"),
    ("http://[fe80::1]/", "blocked"),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("url,code", REJECTED_URLS)
async def test_rejected_urls_never_reach_the_network(isolated, url, code):
    result = await gen.fetch_reference(url)
    assert result == {"url": url, "ok": False, "error": gen._PUBLIC_ERRORS[code]}
    assert isolated.site.requests == []
    assert isolated.connects == []


# -------------------------------------------------- DNS resolution rules ---

@pytest.mark.asyncio
async def test_mixed_public_and_private_dns_answer_is_rejected(isolated):
    use(isolated, {"example.com": [PUBLIC_V4, "10.0.0.5"]})
    result = await gen.fetch_reference("https://example.com/")
    assert result["ok"] is False and result["error"] == gen._PUBLIC_ERRORS["blocked"]
    assert isolated.site.requests == []


@pytest.mark.asyncio
@pytest.mark.parametrize("bad", ["::1", "fd00:ec2::254", "::ffff:169.254.169.254", "169.254.169.254"])
async def test_any_non_public_ipv4_or_ipv6_record_is_rejected(isolated, bad):
    use(isolated, {"example.com": [PUBLIC_V6, PUBLIC_V4, bad]})
    result = await gen.fetch_reference("https://example.com/")
    assert result["error"] == gen._PUBLIC_ERRORS["blocked"]
    assert isolated.site.requests == []


@pytest.mark.asyncio
async def test_dns_failure_is_generic(isolated):
    result = await gen.fetch_reference("https://unknown.example/")
    assert result == {"url": "https://unknown.example/", "ok": False, "error": gen._PUBLIC_ERRORS["dns"]}
    assert "internal-dns.corp" not in str(result)


@pytest.mark.asyncio
async def test_public_answer_is_pinned_with_host_header_and_sni(isolated):
    result = await gen.fetch_reference("https://Example.com/produk?id=1")
    assert result["ok"] is True
    assert result["title"] == "Toko Contoh" and result["description"] == "desc" and "Halo dunia" in result["text"]
    (req,) = isolated.site.requests
    assert req.url.host == PUBLIC_V4 and req.url.path == "/produk" and req.url.query == b"id=1"
    assert req.headers["host"] == "example.com"
    assert req.extensions["sni_hostname"] == "example.com"
    assert isolated.resolver.calls == [("example.com", 443)]


@pytest.mark.asyncio
async def test_ipv6_answer_is_pinned(isolated):
    use(isolated, {"example.com": [PUBLIC_V6]})
    result = await gen.fetch_reference("http://example.com/")
    assert result["ok"] is True
    (req,) = isolated.site.requests
    assert req.url.host == PUBLIC_V6 and f"[{PUBLIC_V6}]" in str(req.url)
    assert req.headers["host"] == "example.com"
    assert "sni_hostname" not in req.extensions  # plain http


@pytest.mark.asyncio
async def test_dns_rebinding_cannot_switch_the_connected_ip(isolated):
    # 1st answer public, every later answer private (classic rebinding).
    use(isolated, {"example.com": lambda n: [PUBLIC_V4] if n == 1 else ["127.0.0.1"]})
    result = await gen.fetch_reference("https://example.com/")
    assert result["ok"] is True
    assert len(isolated.resolver.calls) == 1  # resolved exactly once for the hop
    assert [r.url.host for r in isolated.site.requests] == [PUBLIC_V4]


@pytest.mark.asyncio
async def test_rebinding_on_redirect_hop_is_rejected(isolated):
    use(isolated,
        {"example.com": lambda n: [PUBLIC_V4] if n == 1 else ["127.0.0.1"]},
        lambda req: httpx.Response(302, headers={"location": "/next"}))
    result = await gen.fetch_reference("https://example.com/start")
    assert result["error"] == gen._PUBLIC_ERRORS["blocked"]
    assert [r.url.path for r in isolated.site.requests] == ["/start"]
    assert len(isolated.resolver.calls) == 2


# ------------------------------------------------------------ redirects ---

@pytest.mark.asyncio
@pytest.mark.parametrize("location,code", [
    ("http://169.254.169.254/latest/meta-data/", "blocked"),
    ("http://[::1]/", "blocked"),
    ("http://[fd00:ec2::254]/", "blocked"),
    ("http://localhost/", "blocked"),
    ("http://internal.example/", "blocked"),
    ("http://2130706433/", "blocked"),
    ("http://user@example.com/", "blocked"),
    ("http://example.com:8080/", "blocked"),
    ("ftp://example.com/file", "invalid_url"),
    ("file:///etc/passwd", "invalid_url"),
])
async def test_each_redirect_is_validated_independently(isolated, location, code):
    use(isolated,
        {"example.com": [PUBLIC_V4], "internal.example": ["10.1.2.3"]},
        lambda req: httpx.Response(302, headers={"location": location}) if req.url.path == "/start" else html_response())
    result = await gen.fetch_reference("https://example.com/start")
    assert result["error"] == gen._PUBLIC_ERRORS[code]
    assert [r.url.path for r in isolated.site.requests] == ["/start"]
    assert all(r.url.host == PUBLIC_V4 for r in isolated.site.requests)


@pytest.mark.asyncio
async def test_relative_redirect_is_resolved_against_original_url(isolated):
    use(isolated, handler=lambda req: httpx.Response(301, headers={"location": "/next"}) if req.url.path == "/start" else html_response())
    result = await gen.fetch_reference("https://example.com/start")
    assert result["ok"] is True
    assert [(r.url.host, r.url.path, r.headers["host"]) for r in isolated.site.requests] == [
        (PUBLIC_V4, "/start", "example.com"), (PUBLIC_V4, "/next", "example.com")]
    assert len(isolated.resolver.calls) == 2  # re-resolved and re-validated per hop


@pytest.mark.asyncio
async def test_redirect_to_other_public_host_pins_new_ip_and_sni(isolated):
    use(isolated,
        {"example.com": [PUBLIC_V4], "other.example": [PUBLIC_V4_B]},
        lambda req: httpx.Response(307, headers={"location": "https://other.example/x"}) if req.headers["host"] == "example.com" else html_response())
    result = await gen.fetch_reference("https://example.com/")
    assert result["ok"] is True
    second = isolated.site.requests[1]
    assert (second.url.host, second.headers["host"], second.extensions["sni_hostname"]) == (PUBLIC_V4_B, "other.example", "other.example")


@pytest.mark.asyncio
async def test_too_many_redirects(isolated):
    use(isolated, handler=lambda req: httpx.Response(302, headers={"location": "/again"}))
    result = await gen.fetch_reference("https://example.com/")
    assert result["error"] == gen._PUBLIC_ERRORS["redirects"]
    assert len(isolated.site.requests) == gen.MAX_REFERENCE_REDIRECTS + 1


# ------------------------------------------------- content type & size ---

@pytest.mark.asyncio
@pytest.mark.parametrize("ctype", ["application/json", "image/png", "application/pdf", "application/octet-stream", ""])
async def test_unsupported_content_type_is_rejected(isolated, ctype):
    use(isolated, handler=lambda req: httpx.Response(200, headers={"content-type": ctype} if ctype else {}, content=b'{"secret": 1}'))
    result = await gen.fetch_reference("https://example.com/")
    assert result == {"url": "https://example.com/", "ok": False, "error": gen._PUBLIC_ERRORS["content_type"]}


@pytest.mark.asyncio
async def test_charset_from_header_is_used(isolated):
    body = "<title>Café</title><p>crème brûlée</p>".encode("iso-8859-1")
    use(isolated, handler=lambda req: html_response(body, "text/html; charset=iso-8859-1"))
    result = await gen.fetch_reference("https://example.com/")
    assert result["title"] == "Café" and "crème brûlée" in result["text"]


@pytest.mark.asyncio
async def test_http_error_status_is_generic(isolated):
    use(isolated, handler=lambda req: httpx.Response(500, headers={"content-type": "text/html"}, content=b"stack trace at 10.0.0.7"))
    result = await gen.fetch_reference("https://example.com/")
    assert result["error"] == gen._PUBLIC_ERRORS["http_status"] and "10.0.0.7" not in str(result)


def counting_body(chunk_size=64 * 1024, delay=0.0, counter=None):
    async def gen_body():
        while True:
            if delay:
                await asyncio.sleep(delay)
            counter["sent"] += chunk_size
            yield b"<p>" + b"a" * (chunk_size - 3)
    return gen_body()


@pytest.mark.asyncio
async def test_declared_oversized_body_is_rejected_before_reading(isolated):
    counter = {"sent": 0}
    use(isolated, handler=lambda req: httpx.Response(
        200, headers={"content-type": "text/html", "content-length": str(gen.MAX_REFERENCE_BYTES + 1)},
        content=counting_body(counter=counter)))
    result = await gen.fetch_reference("https://example.com/")
    assert result["error"] == gen._PUBLIC_ERRORS["too_large"]
    assert counter["sent"] == 0


@pytest.mark.asyncio
async def test_streamed_body_is_capped_at_limit(isolated):
    counter = {"sent": 0}
    chunk = 64 * 1024
    use(isolated, handler=lambda req: httpx.Response(200, headers={"content-type": "text/html"}, content=counting_body(chunk, counter=counter)))
    result = await gen.fetch_reference("https://example.com/")
    assert result["ok"] is True
    assert gen.MAX_REFERENCE_BYTES <= counter["sent"] <= gen.MAX_REFERENCE_BYTES + chunk
    assert len(result["text"]) <= gen.MAX_REFERENCE_CHARS


@pytest.mark.asyncio
async def test_read_limited_never_returns_more_than_limit(isolated, monkeypatch):
    monkeypatch.setattr(gen, "MAX_REFERENCE_BYTES", 1000)
    counter = {"sent": 0}
    resp = httpx.Response(200, headers={"content-type": "text/html"}, content=counting_body(300, counter=counter))
    data = await gen._read_limited(resp)
    assert len(data) == 1000 and counter["sent"] <= 1200


# ------------------------------------------------------------- timeouts ---

@pytest.mark.asyncio
async def test_total_timeout_stops_slow_drip(isolated, monkeypatch):
    monkeypatch.setattr(gen, "REFERENCE_TOTAL_TIMEOUT", 0.3)
    counter = {"sent": 0}
    use(isolated, handler=lambda req: httpx.Response(200, headers={"content-type": "text/html"}, content=counting_body(16, delay=0.05, counter=counter)))
    start = time.monotonic()
    result = await gen.fetch_reference("https://example.com/")
    assert result["error"] == gen._PUBLIC_ERRORS["timeout"]
    assert time.monotonic() - start < 2


def test_configured_limits():
    assert gen.REFERENCE_ALLOWED_PORTS == {80, 443}
    assert gen.MAX_REFERENCE_BYTES == 1_000_000
    assert gen.REFERENCE_TOTAL_TIMEOUT == 15.0
    assert gen.MAX_CONCURRENT_FETCHES == 4


# ---------------------------------------------------------- concurrency ---

@pytest.mark.asyncio
async def test_global_semaphore_limits_parallel_fetches(isolated):
    state = {"active": 0, "max": 0}
    release = asyncio.Event()

    async def slow_resolver(host, port):
        state["active"] += 1
        state["max"] = max(state["max"], state["active"])
        try:
            await release.wait()
        finally:
            state["active"] -= 1
        return [PUBLIC_V4]

    isolated.monkeypatch.setattr(gen, "_resolve_host", slow_resolver)
    tasks = [asyncio.create_task(gen.fetch_reference(f"https://example.com/{i}")) for i in range(7)]
    for _ in range(100):
        await asyncio.sleep(0.01)
        if state["active"] == gen.MAX_CONCURRENT_FETCHES:
            break
    await asyncio.sleep(0.05)
    assert state["active"] == gen.MAX_CONCURRENT_FETCHES
    release.set()
    results = await asyncio.gather(*tasks)
    assert all(r["ok"] for r in results)
    assert state["max"] == gen.MAX_CONCURRENT_FETCHES


class FakeLLM:
    def __init__(self):
        self.calls = []

    async def chat_completion_stream(self, messages=None, system_prompt=None, **kwargs):
        self.calls.append(messages)
        delta = types.SimpleNamespace(content="PRODUCT_NAME: X\n\n## 1. Overview\nok\n")
        yield types.SimpleNamespace(choices=[types.SimpleNamespace(delta=delta)])


async def run_stream(monkeypatch, request):
    llm = FakeLLM()
    monkeypatch.setattr(gen, "get_openai_client", lambda: llm)
    events = [e async for e in gen.stream_prd(request, template="general")]
    return events, llm.calls[0][0]["content"]


@pytest.mark.asyncio
async def test_stream_prd_fetches_concurrently_and_keeps_event_order(isolated):
    urls = ["https://a.example/", "https://b.example/", "https://c.example/"]
    started, all_started = [], asyncio.Event()

    async def fake_fetch(url):
        started.append(url)
        if len(started) == len(urls):
            all_started.set()
        await asyncio.wait_for(all_started.wait(), 2)  # deadlocks (times out) if sequential
        await asyncio.sleep(0.01 * (len(urls) - urls.index(url)))  # finish in reverse order
        return {"url": url, "ok": True, "title": url, "description": "", "text": ""}

    isolated.monkeypatch.setattr(gen, "fetch_reference", fake_fetch)
    events, _ = await run_stream(isolated.monkeypatch, "Mirip " + " dan ".join(urls + urls[:1]))  # duplicate is dropped
    refs = [e for e in events if e["type"] == "reference"]
    assert [r["url"] for r in refs] == urls and all(r["ok"] for r in refs)


@pytest.mark.asyncio
async def test_stream_prd_metadata_url_is_blocked_end_to_end(isolated):
    events, prompt = await run_stream(isolated.monkeypatch, "Buat app seperti http://169.254.169.254/latest/meta-data/iam/security-credentials/")
    (ref,) = [e for e in events if e["type"] == "reference"]
    assert ref["ok"] is False and ref["error"] == gen._PUBLIC_ERRORS["blocked"]
    assert isolated.site.requests == [] and isolated.connects == [] and isolated.resolver.calls == []
    assert "Page text" not in prompt and "could not be loaded" in prompt
    assert events[-1]["type"] == "done"


@pytest.mark.asyncio
async def test_internal_errors_are_not_sent_to_client(isolated):
    def boom(req):
        raise httpx.ConnectError("connect to 10.9.8.7:443 refused; token=s3cr3t")
    use(isolated, handler=boom)
    events, prompt = await run_stream(isolated.monkeypatch, "lihat https://example.com/")
    (ref,) = [e for e in events if e["type"] == "reference"]
    assert ref["error"] == gen._PUBLIC_ERRORS["failed"]
    blob = str(events) + prompt
    assert "10.9.8.7" not in blob and "s3cr3t" not in blob and "ConnectError" not in blob


@pytest.mark.asyncio
async def test_unexpected_exception_is_generic(isolated):
    async def broken(host, port):
        raise RuntimeError("resolver crashed at /etc/secret path")
    isolated.monkeypatch.setattr(gen, "_resolve_host", broken)
    result = await gen.fetch_reference("https://example.com/")
    assert result["error"] == gen._PUBLIC_ERRORS["dns"] and "secret" not in str(result)


# ------------------------------------------------------- disabled switch ---

@pytest.mark.asyncio
@pytest.mark.parametrize("value", ["0", "false", "no", "off", "OFF", " False "])
async def test_disabled_fetch_performs_no_network_access(isolated, value):
    isolated.monkeypatch.setenv(gen.REFERENCE_FETCH_ENV, value)
    result = await gen.fetch_reference("https://example.com/")
    assert result["error"] == gen._PUBLIC_ERRORS["disabled"]
    events, prompt = await run_stream(isolated.monkeypatch, "Mirip https://example.com/ dan http://169.254.169.254/")
    refs = [e for e in events if e["type"] == "reference"]
    assert [r["error"] for r in refs] == [gen._PUBLIC_ERRORS["disabled"]] * 2
    assert not any(e["type"] == "status" and "Reading reference" in e["message"] for e in events)
    assert isolated.resolver.calls == [] and isolated.site.requests == [] and isolated.connects == []


@pytest.mark.asyncio
async def test_enabled_by_default(isolated):
    assert gen.reference_fetch_enabled() is True
    assert (await gen.fetch_reference("https://example.com/"))["ok"] is True


# ------------------------------- real connection layer (no sockets opened) ---

class RecordingStream:
    """Stands in for the TCP stream httpcore gets back; records the TLS upgrade and aborts."""

    def __init__(self, record):
        self.record = record

    async def start_tls(self, ssl_context, server_hostname=None, timeout=None):
        self.record.update(ssl_context=ssl_context, server_hostname=server_hostname)
        raise httpcore.ConnectError("stopped by test before any I/O")

    async def write(self, buffer, timeout=None):
        raise httpcore.WriteError("stopped by test before any I/O")

    async def read(self, max_bytes, timeout=None):
        raise httpcore.ReadError("stopped by test before any I/O")

    async def aclose(self):
        pass

    def get_extra_info(self, info):
        return None


@pytest.fixture
def real_transport(isolated, monkeypatch):
    """Use the production transport (httpx default) but with a recording, socket-free connect."""
    monkeypatch.setattr(gen, "_build_transport", lambda: None)
    record = {"connects": []}

    async def fake_connect(self, host, port, timeout=None, local_address=None, socket_options=None):
        record["connects"].append((host, port))
        return RecordingStream(record)

    monkeypatch.setattr(AutoBackend, "connect_tcp", fake_connect)
    return record


@pytest.mark.asyncio
async def test_actual_connection_goes_to_pinned_ip_with_tls_verification_and_sni(real_transport):
    result = await gen.fetch_reference("https://example.com/")
    assert result == {"url": "https://example.com/", "ok": False, "error": gen._PUBLIC_ERRORS["failed"]}
    assert real_transport["connects"] == [(PUBLIC_V4, 443)]
    assert real_transport["server_hostname"] == "example.com"
    ctx = real_transport["ssl_context"]
    assert ctx.verify_mode == ssl.CERT_REQUIRED and ctx.check_hostname is True


@pytest.mark.asyncio
async def test_actual_ipv6_connection_is_pinned(isolated, real_transport):
    use(isolated, {"example.com": [PUBLIC_V6]})
    await gen.fetch_reference("https://example.com/")
    assert [(h.strip("[]"), p) for h, p in real_transport["connects"]] == [(PUBLIC_V6, 443)]
    assert real_transport["server_hostname"] == "example.com"


@pytest.mark.asyncio
async def test_environment_proxies_are_ignored(isolated, real_transport):
    for var in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
        isolated.monkeypatch.setenv(var, "http://proxy.example:3128")
    await gen.fetch_reference("https://example.com/")
    await gen.fetch_reference("http://example.com/")
    assert [c for c in real_transport["connects"]] == [(PUBLIC_V4, 443), (PUBLIC_V4, 80)]
