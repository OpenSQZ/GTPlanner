"""Tests for the Quick PRD generator (LLM is mocked)."""
import types

import pytest

import gtplanner.agent.prd_generator as gen


class FakeClient:
    """Streams a canned answer in small pieces, like the OpenAI SDK."""

    def __init__(self, answer: str):
        self.answer = answer
        self.calls = []

    async def chat_completion_stream(self, messages=None, system_prompt=None, **kwargs):
        self.calls.append({"messages": messages, "system_prompt": system_prompt})
        for i in range(0, len(self.answer), 7):
            delta = types.SimpleNamespace(content=self.answer[i:i + 7])
            yield types.SimpleNamespace(choices=[types.SimpleNamespace(delta=delta)])


async def collect(**kwargs):
    events = [e async for e in gen.stream_prd(**kwargs)]
    done = [e for e in events if e["type"] == "done"]
    streamed = "".join(e["content"] for e in events if e["type"] == "chunk")
    return events, done[0]["content"], streamed


ANSWER = "PRODUCT_NAME: TokoKu\n\n## 1. Ringkasan & tujuan\n- **Nama produk:** TokoKu\n\n## 11. Aturan untuk AI agent\n- Baca docs/PRD.md\n"


@pytest.mark.asyncio
async def test_fullstack_template_wraps_llm_output(monkeypatch):
    fake = FakeClient(ANSWER)
    monkeypatch.setattr(gen, "get_openai_client", lambda: fake)
    monkeypatch.setenv("NGODINGPAKEAI_TOKEN", "ngpk_test_token")

    _, doc, streamed = await collect(request="Buat toko online", template="fullstack_nextjs")

    assert doc.startswith("# PRD: TokoKu\n")
    assert "PRODUCT_NAME" not in doc
    # Fixed parts are inserted verbatim, in order
    order = [doc.index(h) for h in ("## Cara pakai", "## 0. Setup proyek", "## 1. Ringkasan & tujuan",
                                     "## 11. Aturan untuk AI agent", "## Lampiran: prompt pembuka")]
    assert order == sorted(order)
    assert "--token ngpk_test_token" in doc
    assert "{{" not in doc
    # What the client streams equals the final document (modulo blank lines)
    squash = lambda t: "\n".join(line for line in t.splitlines() if line.strip())
    assert squash(streamed) == squash(doc)
    # The skeleton is part of the system prompt
    assert "## 6. Fitur & user story dengan acceptance criteria" in fake.calls[0]["system_prompt"]


@pytest.mark.asyncio
async def test_missing_token_leaves_clear_placeholder(monkeypatch):
    monkeypatch.setattr(gen, "get_openai_client", lambda: FakeClient(ANSWER))
    monkeypatch.delenv("NGODINGPAKEAI_TOKEN", raising=False)

    _, doc, _ = await collect(request="Buat toko online")

    assert "NGODINGPAKEAI_TOKEN" in doc


@pytest.mark.asyncio
async def test_revision_sends_only_generated_sections(monkeypatch):
    monkeypatch.setattr(gen, "get_openai_client", lambda: FakeClient(ANSWER))
    _, first, _ = await collect(request="Buat toko online")

    fake = FakeClient(ANSWER.replace("Baca docs/PRD.md", "Baca docs/PRD.md dengan teliti"))
    monkeypatch.setattr(gen, "get_openai_client", lambda: fake)
    _, revised, _ = await collect(request="tambahkan voucher", previous_prd=first)

    sent = fake.calls[0]["messages"][0]["content"]
    assert "## 1. Ringkasan & tujuan" in sent
    assert "## 0. Setup proyek" not in sent and "## Lampiran" not in sent
    assert "tambahkan voucher" in sent
    assert revised.count("## Lampiran: prompt pembuka") == 1
    assert "dengan teliti" in revised


@pytest.mark.asyncio
async def test_general_template_and_missing_name_line(monkeypatch):
    monkeypatch.setattr(gen, "get_openai_client", lambda: FakeClient("## 1. Overview\nText\n"))

    _, doc, _ = await collect(request="Make an app", template="general")

    assert doc.startswith("# PRD: Produk\n")
    assert "## 1. Overview" in doc
    assert "## 0. Setup proyek" not in doc


def test_strip_header_removes_fixed_parts():
    header = gen.render_header("fullstack_nextjs", "X")
    body = "## 1. Ringkasan & tujuan\nisi\n"
    assert gen.strip_header(header + body + gen.render_footer("fullstack_nextjs")).strip() == body.strip()
