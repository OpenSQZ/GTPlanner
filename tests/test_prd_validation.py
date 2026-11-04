"""Tests for the automatic post-generation checks of the Quick PRD generator (LLM is mocked)."""
import types

import pytest

import gtplanner.agent.prd_generator as gen

TOKEN = "ngpk_UnitTestToken0123456789"
BODY_SECTIONS = "\n\n".join(f"## {n}. Bagian {n}\nIsi konkret." for n in range(1, 13))
TAIL = "\n\n## Hasil pengecekan silang\n1. Tidak ada temuan\n\n## Pertanyaan terbuka\n1. Warna brand?\n"
GOOD_SEQ = """```mermaid
sequenceDiagram
  participant U as Pengguna
  actor A as Admin
  participant BE as Backend
  U->>BE: POST /api/checkout
  BE-->>U: 201
  A->>+BE: approve
  BE-->>-A: 200
  BE->>BE: Verifikasi signature
  Note over U, BE: catatan -> bukan panah
```"""


@pytest.fixture(autouse=True)
def fixed_token(monkeypatch):
    monkeypatch.setenv("NGODINGPAKEAI_TOKEN", TOKEN)


def full_doc(body=BODY_SECTIONS + TAIL):
    return gen.render_header("fullstack_nextjs", "TokoKu") + body + gen.render_footer("fullstack_nextjs")


def check(doc, cid, template="fullstack_nextjs", token=TOKEN):
    return next(c for c in gen.validate_prd(doc, template, token=token) if c["id"] == cid)


def test_complete_document_passes_every_check():
    checks = gen.validate_prd(full_doc(BODY_SECTIONS + "\n\n" + GOOD_SEQ + TAIL), "fullstack_nextjs", token=TOKEN)
    assert [c["id"] for c in checks] == ["placeholders", "headings", "code_fences", "sequence_participants", "repo_token"]
    assert all(c["ok"] for c in checks), checks


# ------------------------------------------------------------ placeholders ---

@pytest.mark.parametrize("line", [
    "- [ ] Given form valid, when submit, then 201",
    "- [x] Tidak ada placeholder — Bukti: bagian 1",
    "Route dinamis /produk/[slug] dan /api/orders/[id]/pay",
    "Lihat [dokumentasi Midtrans](https://docs.midtrans.com)",
    "Response `{data[], total}` dan `items[0]`",
    "Ganti semua [...] dengan perintah asli sebelum dipakai",
    "Referensi footnote [1] dan array data[]",
])
def test_non_placeholder_brackets_pass(line):
    assert check(full_doc(BODY_SECTIONS + "\n" + line + TAIL), "placeholders")["ok"] is True


def test_brackets_inside_code_blocks_pass():
    body = BODY_SECTIONS + "\n```text\nIsi template untuk aplikasi: [deskripsi singkat]\n```\n" + TAIL
    assert check(full_doc(body), "placeholders")["ok"] is True


@pytest.mark.parametrize("line,expected", [
    ("- **Nama produk:** [nama]", "[nama]"),
    ("- Dev: [salin dari AGENTS.md]", "[salin dari AGENTS.md]"),
    ("| Deploy | [Docker / Vercel / VM] | Ya |", "[Docker / Vercel / VM]"),
    ("Batas penyedia: [isi untuk produk ini]", "[isi untuk produk ini]"),
])
def test_leftover_placeholder_fails_with_line_number(line, expected):
    doc = full_doc(BODY_SECTIONS + "\n" + line + TAIL)
    result = check(doc, "placeholders")
    assert result["ok"] is False
    line_no = doc.splitlines().index(line) + 1
    assert f"baris {line_no}: {expected}" in result["detail"]


def test_raw_skeleton_is_flagged():
    doc = full_doc(gen._read_template_file("fullstack_nextjs", "skeleton.md"))
    assert len(gen.find_placeholders(doc)) > 50
    assert check(doc, "placeholders")["ok"] is False


# ---------------------------------------------------------------- headings ---

def test_all_headings_present_pass():
    assert check(full_doc(), "headings")["ok"] is True


@pytest.mark.parametrize("removed,label", [
    ("## 7. Bagian 7", "## 7."),
    ("## 12. Bagian 12", "## 12."),
    ("## Hasil pengecekan silang", "## Hasil pengecekan silang"),
    ("## Pertanyaan terbuka", "## Pertanyaan terbuka"),
])
def test_missing_heading_fails(removed, label):
    result = check(full_doc().replace(removed + "\n", "Bukan judul\n"), "headings")
    assert result["ok"] is False and label in result["detail"]


def test_heading_without_setup_section_fails():
    doc = gen.repo_version(full_doc())  # section 0 removed
    result = check(doc, "headings")
    assert result["ok"] is False and "## 0." in result["detail"]


def test_heading_only_inside_code_block_does_not_count():
    doc = full_doc().replace("## 5. Bagian 5\n", "```\n## 5. Bagian 5\n```\n")
    assert "## 5." in check(doc, "headings")["detail"]


def test_heading_number_must_match_exactly():
    doc = full_doc().replace("## 1. Bagian 1\n", "## 10a. Salah\n")
    assert "## 1." in check(doc, "headings")["detail"]


def test_general_template_headings():
    body = "# PRD: X\n\n" + "\n\n".join(f"## {n}. S" for n in range(1, 16))
    assert check(body, "headings", template="general")["ok"] is True
    result = check(body.replace("## 9. S", "S"), "headings", template="general")
    assert result["ok"] is False and "## 9." in result["detail"]


# ------------------------------------------------------------- code fences ---

def test_even_fences_pass():
    assert check(full_doc(BODY_SECTIONS + "\n" + GOOD_SEQ + TAIL), "code_fences")["ok"] is True


def test_odd_fences_fail():
    result = check(full_doc(BODY_SECTIONS + "\n```mermaid\nerDiagram\n  a ||--o{ b : x\n" + TAIL), "code_fences")
    assert result["ok"] is False and "tidak ditutup" in result["detail"]


def test_inline_triple_backtick_is_not_a_fence():
    body = BODY_SECTIONS + "\nTulis dalam blok ``` mermaid di tengah kalimat tidak dihitung.\n" + TAIL
    assert check(full_doc(body), "code_fences")["ok"] is True


# ------------------------------------------------------ sequence diagrams ---

def test_declared_participants_pass():
    result = check(full_doc(BODY_SECTIONS + "\n" + GOOD_SEQ + TAIL), "sequence_participants")
    assert result["ok"] is True and "1 diagram dicek" in result["detail"]


def test_no_sequence_diagram_passes_with_note():
    result = check(full_doc(), "sequence_participants")
    assert result["ok"] is True and "Tidak ada blok sequenceDiagram" in result["detail"]


def test_undeclared_actor_fails_and_names_it():
    bad = GOOD_SEQ.replace("BE-->>U: 201", "BE->>PAY: Buat transaksi\n  PAY-->>BE: token\n  CRON-)BE: expire")
    result = check(full_doc(BODY_SECTIONS + "\n" + GOOD_SEQ + "\n\n" + bad + TAIL), "sequence_participants")
    assert result["ok"] is False
    assert result["detail"] == "diagram ke-2: PAY, CRON"


def test_alias_is_not_a_declaration():
    seq = "```mermaid\nsequenceDiagram\n  participant U as Pengguna\n  Pengguna->>U: hai\n```"
    result = check(full_doc(BODY_SECTIONS + "\n" + seq + TAIL), "sequence_participants")
    assert result["ok"] is False and "Pengguna" in result["detail"]


def test_other_mermaid_diagrams_are_ignored():
    er = "```mermaid\nerDiagram\n  users ||--o{ orders : places\n```\n```mermaid\nflowchart TD\n  A-->B\n```"
    assert check(full_doc(BODY_SECTIONS + "\n" + er + TAIL), "sequence_participants")["ok"] is True


# ------------------------------------------------------------ repo token ---

def test_repo_version_without_token_passes():
    doc = full_doc()
    assert TOKEN in doc  # section 0 carries it
    assert check(doc, "repo_token")["ok"] is True
    assert TOKEN not in gen.repo_version(doc) and "## 0." not in gen.repo_version(doc)


def test_token_value_outside_section_0_fails_without_echoing_it():
    other_token = "abc-not-ngpk-secret-42"
    doc = full_doc(BODY_SECTIONS.replace("## 4. Bagian 4\nIsi konkret.", f"## 4. Bagian 4\nCLI token {other_token}") + TAIL)
    result = check(doc, "repo_token", token=other_token)
    assert result["ok"] is False and "nilai NGODINGPAKEAI_TOKEN" in result["detail"]
    assert other_token not in str(result)


def test_ngpk_string_outside_section_0_fails():
    doc = full_doc(BODY_SECTIONS + "\nJalankan create --token ngpk_lain123" + TAIL)
    result = check(doc, "repo_token")
    assert result["ok"] is False and "ngpk_" in result["detail"] and "ngpk_lain123" not in result["detail"]


def test_token_stays_when_section_1_is_missing():
    # Truncated/odd document: section 0 cannot be cut off, so the repo version still holds the token.
    doc = gen.render_header("fullstack_nextjs", "X") + "## 2. Bagian 2\nisi"
    assert check(doc, "repo_token")["ok"] is False


def test_repo_version_matches_web_ui_regex():
    # Same pattern as stripSetupSection() in static/index.html.
    html = open("static/index.html", encoding="utf-8").read()
    assert r'.replace(/^## 0\.[^\n]*\n[\s\S]*?(?=^## 1\.)/m, "")' in html


# ------------------------------------------------- finish_reason / stream ---

class FakeClient:
    def __init__(self, answer, finish_reason="stop", max_tokens=None, final_empty_chunk=False):
        self.answer, self.finish_reason, self.final_empty_chunk = answer, finish_reason, final_empty_chunk
        self.config = types.SimpleNamespace(max_tokens=max_tokens)

    async def chat_completion_stream(self, messages=None, system_prompt=None, **kwargs):
        pieces = [self.answer[i:i + 50] for i in range(0, len(self.answer), 50)]
        for i, p in enumerate(pieces):
            last = i == len(pieces) - 1 and not self.final_empty_chunk
            choice = types.SimpleNamespace(delta=types.SimpleNamespace(content=p), finish_reason=self.finish_reason if last else None)
            yield types.SimpleNamespace(choices=[choice])
        if self.final_empty_chunk:
            choice = types.SimpleNamespace(delta=types.SimpleNamespace(content=None), finish_reason=self.finish_reason)
            yield types.SimpleNamespace(choices=[choice])
            yield types.SimpleNamespace(choices=[])  # usage-only chunk


async def run(monkeypatch, client):
    monkeypatch.setattr(gen, "get_openai_client", lambda: client)
    events = [e async for e in gen.stream_prd("Buat toko online")]
    return events, next(e for e in events if e["type"] == "validation"), events[-1]


ANSWER = "PRODUCT_NAME: TokoKu\n\n" + BODY_SECTIONS + TAIL


@pytest.mark.asyncio
async def test_stop_reason_is_complete_and_valid(monkeypatch):
    events, v, done = await run(monkeypatch, FakeClient(ANSWER, "stop", max_tokens=16000))
    assert v["finish_reason"] == "stop" and v["truncated"] is False and v["max_tokens"] == 16000
    assert v["valid"] is True and done == {"type": "done", "content": done["content"], "truncated": False, "valid": True}
    assert [e["type"] for e in events][-2:] == ["validation", "done"]


@pytest.mark.asyncio
@pytest.mark.parametrize("reason", ["length", "max_tokens"])
async def test_token_limit_marks_truncated_and_not_valid(monkeypatch, reason):
    _, v, done = await run(monkeypatch, FakeClient(ANSWER[:400], reason, max_tokens=4096))
    assert v["truncated"] is True and v["finish_reason"] == reason and v["max_tokens"] == 4096
    assert v["valid"] is False and done["truncated"] is True and done["valid"] is False
    assert any(c["id"] == "headings" and not c["ok"] for c in v["checks"])


@pytest.mark.asyncio
async def test_truncated_even_if_all_checks_pass(monkeypatch):
    _, v, done = await run(monkeypatch, FakeClient(ANSWER, "length"))
    assert all(c["ok"] for c in v["checks"]) and v["truncated"] is True and done["valid"] is False


@pytest.mark.asyncio
async def test_finish_reason_on_separate_final_chunk(monkeypatch):
    _, v, _ = await run(monkeypatch, FakeClient(ANSWER, "length", final_empty_chunk=True))
    assert v["finish_reason"] == "length" and v["truncated"] is True


@pytest.mark.asyncio
async def test_missing_finish_reason_and_max_tokens_are_reported_as_none(monkeypatch):
    client = FakeClient(ANSWER, None)
    del client.config
    _, v, done = await run(monkeypatch, client)
    assert v["finish_reason"] is None and v["max_tokens"] is None and v["truncated"] is False
    assert done["valid"] is True


@pytest.mark.asyncio
async def test_failed_check_makes_done_not_valid(monkeypatch):
    _, v, done = await run(monkeypatch, FakeClient(ANSWER.replace("## 3. Bagian 3", "## 3. [isi judul]"), "stop"))
    assert v["truncated"] is False and done["valid"] is False
    assert next(c for c in v["checks"] if c["id"] == "placeholders")["ok"] is False
