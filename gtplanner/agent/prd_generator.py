"""
Quick PRD generator

Generates a complete Product Requirements Document in a single streaming LLM
call, following a selectable template:

- "fullstack_nextjs" (default): the "PRD Full Stack untuk AI Coding (Starter
  Next JS)" framework. Its fixed parts (usage notes and the section 0 setup
  prompt) live in prd_templates/fullstack_nextjs/header.md and are inserted
  verbatim; the LLM fills in the skeleton in prd_templates/fullstack_nextjs/skeleton.md.
- "general": a general product/architecture PRD.

Reference websites mentioned in the request are read and passed as context,
and an existing PRD can be revised with a follow-up request.
"""

import asyncio
import ipaddress
import logging
import os
import re
import socket
import weakref
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import AsyncIterator, Dict, List, Optional, Tuple

import httpx

from gtplanner.utils.openai_client import get_openai_client

try:  # make NGODINGPAKEAI_TOKEN and friends from .env available
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover
    pass

TEMPLATES_DIR = Path(__file__).parent / "prd_templates"
DEFAULT_TEMPLATE = "fullstack_nextjs"

LANGUAGE_NAMES = {
    "en": "English",
    "id": "Indonesian (Bahasa Indonesia)",
    "zh": "Simplified Chinese",
    "ja": "Japanese",
    "es": "Spanish",
    "fr": "French",
}

URL_PATTERN = re.compile(r"https?://[^\s<>\"')\]]+", re.IGNORECASE)
MAX_REFERENCE_CHARS = 8000
MAX_REFERENCES = 3

# --- Reference fetching limits (SSRF hardening) ---
REFERENCE_ALLOWED_PORTS = frozenset({80, 443})
MAX_REFERENCE_BYTES = 1_000_000          # decoded body bytes read per page
REFERENCE_TOTAL_TIMEOUT = 15.0           # seconds per URL, all hops included
MAX_CONCURRENT_FETCHES = 4               # global, across all requests
MAX_REFERENCE_REDIRECTS = 3
REFERENCE_HTTP_TIMEOUT = httpx.Timeout(connect=5.0, read=10.0, write=5.0, pool=5.0)
REFERENCE_CONTENT_TYPES = frozenset({"text/html", "application/xhtml+xml", "text/plain"})
REFERENCE_FETCH_ENV = "PRD_REFERENCE_FETCH"  # set to 0/false/no/off to disable all fetching

logger = logging.getLogger(__name__)
NAME_LINE = re.compile(r"^\s*PRODUCT_NAME\s*:\s*(.+?)\s*$", re.IGNORECASE)
MONTHS_ID = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]

FULLSTACK_SYSTEM_PROMPT = """You are a senior product manager and software architect who writes PRDs for AI coding \
agents (Claude Code, Cursor, Codex). A PRD for AI is not a business document but an executable specification: \
every sentence must be convertible into code or a test without the AI guessing.

The product will be built on top of the "Starter Next JS" (NgodingPakeAI) template, which already provides \
authentication (user/session/account tables and auth routes), layout and a local database setup. The PRD only adds \
features on top of it; never ask to rebuild auth, layout or the database setup.

Fill in the TEMPLATE below for the user's product. Rules:

OUTPUT FORMAT
1. The very first line must be exactly `PRODUCT_NAME: <short product name>` (no Markdown), then a blank line.
2. Then output sections "## 1. Ringkasan & tujuan" through "## 12. Checklist sebelum PRD diberikan ke AI", in exactly \
the template's order, with exactly the template's headings, sub-headings (###), intro sentences, table columns and formats.
3. After section 12 add "## Hasil pengecekan silang" (see rule 14), then "## Pertanyaan terbuka": a numbered list of information the user must still decide or provide \
(only real unknowns, not things you could reasonably assume). Then stop.
4. Do NOT output a document title, the "Cara pakai" section, section 0 or the "Lampiran" (they are added automatically). \
GitHub-flavored Markdown only. No preamble, no closing remarks, no code fence around the whole answer.

CONTENT
5. Replace EVERY [placeholder] with concrete content for this product; no "[...]" may remain (Next.js dynamic route \
segments such as /produk/[slug] are fine). Remove rows/bullets that don't apply; repeat blocks (entities, features, \
integrations, rules) as often as needed. Keep the template's fixed guidance sentences (e.g. "Wajib dijawab per entitas", \
the "Tabel pendukung yang sering terlupa" table, the "Aturan constraint" list) and answer them for THIS product right below.
6. Be explicit: real table names, field names, data types, enum values, defaults (one value each), route paths and \
endpoint paths. Money is stored as integer (smallest currency unit), never float.
7. IDs: features F-00 (login/auth from the template), F-01, F-02, ...; business rules BR-01, BR-02, ... (including status \
transition rules). Reference them everywhere (features, milestones).
8. Section 4: the template's exact AGENTS.md is not available, so use the usual Starter Next JS stack (Next.js App Router + \
TypeScript, Tailwind CSS + shadcn/ui, Server Actions/Route Handlers + Zod, Prisma + PostgreSQL, template auth) with \
"Sudah dari template?" = Ya, decide the remaining rows for this product, and add right under the table: \
"> ⚠️ Cocokkan tabel ini dengan AGENTS.md template setelah setup (bagian 0); jika berbeda, ikuti AGENTS.md." \
Pick one deploy target (default: Vercel for production, local Docker/PostgreSQL for dev, unless the user says otherwise), \
keep the "Cek kecocokan dengan target deploy" table and write the consequences in the Catatan column (file storage, \
hosted database, cron authentication and frequency limits, function timeouts), for dev and production if they differ. \
Fill "Diagram arsitektur" with a valid Mermaid flowchart of THIS product: every component in the tech stack table and vice \
versa, labelled arrows, and an arrow from every third party that calls back (webhook/callback) to the backend.
9. Section 5 must contain, for this product:
   - one table per entity (id, createdAt, updatedAt; deletedAt where data must not be lost), Relasi and BR-xx rules;
   - the "Wajib dijawab per entitas" answers: derived fields (computed at query time or stored + when updated), the exact \
mechanism for sequential numbers (counter table updated in the same transaction), single default values;
   - "Siklus hidup sumber daya" table filled for every consumable resource (stock, voucher quota, cart, slots, balance), \
with "Dikembalikan saat" covering EVERY final status (cancelled, expired, rejected, refund, partial refund, return), and \
a "used" marker on the transaction (e.g. stockDeducted or deducted quantity per item) that every give-back reads instead of \
guessing from the status;
   - "Konkurensi & idempotensi" with the concrete contested operations and how each is prevented (transaction, atomic \
conditional update, unique constraint, row lock), and how webhooks/submit buttons/cron jobs are made idempotent \
following the "Aturan idempotensi" (client idempotency key with a FULL unique (userId, idempotencyKey), never a partial \
unique on a changing status; webhook dedup by processedAt so failed events can be reprocessed);
   - "Balapan antara timer internal dan event eksternal": the provider-side expiry value (≤ internal expiry), that the \
user sees the provider deadline (stored separately, e.g. paymentExpiresAt vs expiresAt, pay button hidden after it), that \
an internal cancellation also calls the provider's cancel/expire API (or says late payments go to the late-event path), and \
exactly what happens when a success event arrives for expired/cancelled data (record + needs-manual-refund flag + audit log);
   - "Tabel bawaan template": extend the template user table (write "user — cocokkan dengan schema template setelah setup"), \
never create a second users table or redefine passwordHash/sessions;
   - every supporting table that the features need (status histories, provider notifications with the raw provider ID \
externalId and a NULLABLE FK, voucher redemptions, document counters, audit_logs, snapshot columns) as full entity tables, \
and for every follow-up flag (needs refund/review/verification) the columns resolvedAt, resolvedById, resolutionNote;
   - "Aturan constraint": unique + soft delete decision per unique column (partial unique index WHERE "deletedAt" IS NULL \
when values may be reused), no unique on a foreign key unless the relation is truly one-to-one (put it on the join table \
instead, e.g. orderId in redemptions), partial unique only on stable columns (deletedAt or a truly inactive status), \
configurable limits (perUserLimit, maxPerOrder) checked by a count inside the transaction and never locked by a unique \
constraint, an owner column (e.g. userId, null = public) on every personal/user-owned entity, maxDiscount for percentage discounts, total never negative, and the list of indexes for every filter/sort/join column \
used in section 7;
   - third-party tokens/URLs that must be reused (paymentToken, paymentRedirectUrl, paymentExpiresAt) as columns;
   - a complete Mermaid erDiagram in a ```mermaid code block: every entity table appears in the diagram and vice versa.
10. Section 6: every feature uses the full block: Prioritas, User story, Alur, Acceptance criteria as \
"- [ ] Given ..., when ..., then ..." (at least 3: success, validation error, authorization; more for money/stock logic), \
Edge case, Bergantung pada, Efek samping, Input lengkap, Nilai yang dihitung server, Status yang boleh, Fitur bertahap \
(which part in which milestone and the behaviour before it is active, e.g. 400 or fallback), Potensi penyalahgunaan \
(for value-granting features such as voucher, reward, points, credit, trial: a hard-to-fake trigger such as first paid \
order, or explicit limits per user/day/total; "–" otherwise), Konsistensi AC dengan API. Status codes and behaviour in the \
acceptance criteria must be identical to the section 7 table. Fill "Sequence diagram alur kritis" with one valid Mermaid \
sequenceDiagram per flow that involves money, stock/quota, a third party or several tables in one transaction (all \
participants declared first, BEGIN/COMMIT/ROLLBACK and third-party calls relative to the commit, every failure branch from \
the acceptance criteria as alt/else with the section 7 status code, and what happens if the third party fails after commit).
11. Section 7: every endpoint used by the features; no endpoint accepts price, subtotal, discount, total or role from the \
client; every response field exists in a table or is described as a derived field; mark template routes "(template) — ikuti \
route template, jangan buat ulang". Keep the "Kelengkapan endpoint" list and satisfy it: every endpoint is a row of the \
table (including health check, upload, export, cron and webhook; never only in bullets or notes), full \
list/create/update/delete for every admin-managed entity (or "dikelola lewat seed saja"), public read endpoints for master \
data used as public filters, a row for every upload/export/cron action, every returned token/redirect URL stored in \
section 5, and an endpoint that resolves every follow-up flag. For each third-party integration fill the "Integrasi \
eksternal" block with values from its official documentation as you know it, include the official docs link, the \
provider-side expiry parameter, the provider's cancel/expire API, whether the same transaction ID may be sent again (if \
not, store and reuse the first token/URL), redirect URLs, map ALL webhook statuses (including rare ones) to the internal \
status with the same meaning (expire → EXPIRED, not CANCELLED) and say for each whether the money is captured, only \
held/pending, or already returned by the provider (a provider refund is "sudah dikembalikan", not "perlu refund manual"), \
what happens for late success events on final data, which payload field is the provider's ID and how it is matched, \
describe signature verification exactly, idempotency with reprocessing of failed events and local testing via a tunnel; add the line \
"> ⚠️ Verifikasi endpoint, auth, dan daftar status dengan dokumentasi resmi sebelum coding." under each integration.
12. Sections 8–10: every page/route with role and components; every route mentioned in section 6 is in the section 8 \
table and every entity with admin endpoints has a management page (or "dikelola lewat seed saja"); milestones reference \
feature IDs and say in which milestone a webhook tunnel is set up.
13. Section 11: keep the rules verbatim. For "Perintah penting" write the usual commands (npm run dev, npm test, \
npm run lint, npx prisma migrate dev) followed by " (cocokkan dengan AGENTS.md)".
14. Section 12: evaluate your own document. Mark an item "- [x]" only with evidence: append " — Bukti: <section/row that \
satisfies it>". An item without evidence stays "- [ ]" with " — <what is missing or what the user must do>" appended (the \
items that need verification against official docs or AGENTS.md stay unchecked with that note; the item about section 0 \
stays unchecked with " — pakai tombol "Download untuk repo" di GTPlanner lalu cek isi file-nya"). \
Then, under "## Hasil pengecekan silang", report six numbered checks with concrete findings (or "Tidak ada temuan"): \
(1) every unique constraint in section 5 re-read against the business rules for contradictions or for locking a \
configurable limit, (2) status codes in every acceptance criterion compared with the API table, (3) every endpoint/page \
mentioned in the features but missing as a row in section 7 or 8, (4) every give-back action (stock, quota, balance) traced \
along all paths for giving back something that was never taken, (5) for every deadline and cancellation: what the user sees \
and whether the external provider is informed, (6) every "personal", "milik user" or "perlu ..." flag checked for its owner \
column / resolution columns. Fix any finding in the document itself before writing it, and say that it was fixed.
15. If reference website content is provided, infer its product type, features, page structure and business model and \
design an equivalent product (do not copy its branding or text). Never ask questions inside the document body: make \
reasonable assumptions, record them under "Asumsi", and put real unknowns in "Pertanyaan terbuka".

TEMPLATE:
<template>
{skeleton}
</template>
"""

GENERAL_SYSTEM_PROMPT = """You are a senior product manager and software architect. You write complete, \
implementation-ready Product Requirements Documents (PRDs) that a development team, or an AI coding \
assistant such as Claude Code, Cursor or Copilot, can build from directly.

Rules:
- The very first line must be exactly `PRODUCT_NAME: <short product name>` (no Markdown), then a blank line.
- Produce the full document in one answer. Do not ask clarifying questions; when information is missing, \
make reasonable, industry-standard assumptions and list them in the "Assumptions" section.
- Cover every layer the product needs: customer-facing frontend, admin/back-office, backend services, \
database, integrations (payments, shipping, email/WhatsApp, etc.), security and deployment.
- Be concrete: name the screens, entities, fields, API endpoints, statuses and business rules. Avoid vague filler.
- If reference website content is provided, infer its product type, main features, page structure and \
business model from it, and design an equivalent (not a copy of its branding or text).
- After the PRODUCT_NAME line, output GitHub-flavored Markdown only, starting with "## 1. Overview" \
(the document title is added automatically). No preamble or closing remarks.

Sections:
## 1. Overview (problem, vision, goals, KPIs)
## 2. Target Users & Personas
## 3. Scope (MVP, later phases, out of scope)
## 4. User Roles & Permissions (table)
## 5. Features & Functional Requirements (per module: description, user stories, acceptance criteria, business rules)
## 6. Key User Flows (with a Mermaid flowchart for the main flow)
## 7. Pages / Screens (customer-facing and admin)
## 8. Data Model (entity tables + Mermaid erDiagram)
## 9. API Specification (endpoint table + key request/response examples)
## 10. System Architecture & Tech Stack (with reasons + Mermaid diagram)
## 11. Integrations
## 12. Non-Functional Requirements
## 13. Milestones & Roadmap
## 14. Risks & Mitigations
## 15. Assumptions & Open Questions
"""

TEMPLATES = {
    "fullstack_nextjs": "PRD Full Stack untuk AI Coding (Starter Next JS)",
    "general": "PRD umum (produk & arsitektur)",
}


def _read_template_file(template: str, name: str) -> str:
    return (TEMPLATES_DIR / template / name).read_text(encoding="utf-8")


def _today() -> str:
    now = datetime.now()
    return f"{now.day} {MONTHS_ID[now.month - 1]} {now.year}"


def system_prompt_for(template: str) -> str:
    if template == "fullstack_nextjs":
        return FULLSTACK_SYSTEM_PROMPT.replace("{skeleton}", _read_template_file(template, "skeleton.md"))
    return GENERAL_SYSTEM_PROMPT


def render_header(template: str, product_name: str) -> str:
    """Return the fixed part of the document that precedes the LLM output."""
    if template == "fullstack_nextjs":
        token = os.getenv("NGODINGPAKEAI_TOKEN") or "[TOKEN_NGODINGPAKEAI — isi NGODINGPAKEAI_TOKEN di .env]"
        return (
            _read_template_file(template, "header.md")
            .replace("{{PRODUCT_NAME}}", product_name)
            .replace("{{DATE}}", _today())
            .replace("{{NGODINGPAKEAI_TOKEN}}", token)
        )
    return f"# PRD: {product_name}\n{_today()}\n\n"


def render_footer(template: str) -> str:
    """Return the fixed part of the document appended after the LLM output."""
    path = TEMPLATES_DIR / template / "footer.md"
    return "\n\n" + path.read_text(encoding="utf-8") if path.exists() else ""


def strip_header(prd: str) -> str:
    """Remove the fixed header (title, Cara pakai, section 0) and footer (Lampiran) from a previous PRD."""
    m = re.search(r"^## 1\.", prd, re.MULTILINE)
    body = prd[m.start():] if m else prd
    f = re.search(r"^## Lampiran", body, re.MULTILINE)
    return body[:f.start()].rstrip() if f else body


def product_name_of(prd: str) -> str:
    m = re.search(r"^#\s*PRD\s*:\s*(.+)$", prd or "", re.MULTILINE)
    return m.group(1).strip() if m else "Produk"


# ---------------------------------------------------------------------------
# Post-generation validation
# ---------------------------------------------------------------------------

TRUNCATION_REASONS = frozenset({"length", "max_tokens"})  # OpenAI-style and Anthropic-style names

# Must stay identical to stripSetupSection() in static/index.html ("Download untuk repo").
_SETUP_SECTION = re.compile(r"^## 0\.[^\n]*\n.*?(?=^## 1\.)", re.MULTILINE | re.DOTALL)
_FENCE = re.compile(r"^\s{0,3}```")
_INLINE_CODE = re.compile(r"`[^`\n]*`")
# [text] not preceded by a word char, "/", "!" or "]" (array index, /route/[slug], image, ref link)
# and not followed by "(", "[" or ":" (link, reference link, link definition).
_PLACEHOLDER = re.compile(r"(?<![\w/!\]])\[([^\[\]\n]{1,200})\](?![(\[:])")
_SEQ_DECL = re.compile(r"^\s*(?:create\s+)?(?:participant|actor)\s+(.+?)(?:\s+as\s+.*)?\s*$", re.IGNORECASE)
_SEQ_ARROW = re.compile(
    r"^\s*([^\s:;+<>-][^:;]*?)\s*(<<-->>|<<->>|-->>|->>|--x|-x|--\)|-\)|-->|->)\s*[+-]?\s*([^\s:;+<>-][^:;]*?)\s*:"
)

_REQUIRED_HEADINGS = {
    "fullstack_nextjs": [(rf"{n}\.", f"## {n}.") for n in range(0, 13)]
    + [("Hasil pengecekan silang", "## Hasil pengecekan silang"), ("Pertanyaan terbuka", "## Pertanyaan terbuka")],
    "general": [(rf"{n}\.", f"## {n}.") for n in range(1, 16)],
}


def repo_version(prd: str) -> str:
    """The text that "Download untuk repo" saves: the document without section 0 (which holds the token)."""
    return _SETUP_SECTION.sub("", prd or "", count=1)


def _split_code(prd: str) -> Tuple[List[Tuple[int, str]], List[Tuple[str, List[str]]], int]:
    """Return (prose lines with line numbers, fenced blocks as (info, lines), number of fence lines)."""
    prose: List[Tuple[int, str]] = []
    blocks: List[Tuple[str, List[str]]] = []
    fences = 0
    current: Optional[Tuple[str, List[str]]] = None
    for no, line in enumerate((prd or "").splitlines(), 1):
        if _FENCE.match(line):
            fences += 1
            if current is None:
                current = (line.strip()[3:].strip().lower(), [])
            else:
                blocks.append(current)
                current = None
            continue
        if current is None:
            prose.append((no, line))
        else:
            current[1].append(line)
    if current is not None:  # unclosed block still counts as code
        blocks.append(current)
    return prose, blocks, fences


def find_placeholders(prd: str) -> List[Tuple[int, str]]:
    """Leftover "[...]" placeholders outside code blocks and inline code, as (line number, match)."""
    found = []
    prose, _, _ = _split_code(prd)
    for no, line in prose:
        for m in _PLACEHOLDER.finditer(_INLINE_CODE.sub("", line)):
            inner = m.group(1).strip()
            if inner in ("", "x", "X", "...", "…"):  # task-list checkboxes; "[...]" used as a word in guidance text
                continue
            if not re.search(r"[^\W\d_]", inner):  # no letters: [1], [0-9], [*]
                continue
            found.append((no, m.group(0)))
    return found


def missing_headings(prd: str, template: str) -> List[str]:
    prose, _, _ = _split_code(prd)
    text = "\n".join(line for _, line in prose)
    return [label for pattern, label in _REQUIRED_HEADINGS.get(template, [])
            if not re.search(rf"^##\s+{pattern}(?:\s|$)", text, re.MULTILINE)]


def undeclared_sequence_actors(prd: str) -> List[Tuple[int, List[str]]]:
    """For each mermaid sequenceDiagram block (1-based index), actors used in arrows but never declared."""
    problems = []
    seq_index = 0
    for info, lines in _split_code(prd)[1]:
        if info.split()[:1] != ["mermaid"]:
            continue
        body = [l for l in lines if l.strip() and not l.strip().startswith("%%")]
        if not body or not body[0].strip().startswith("sequenceDiagram"):
            continue
        seq_index += 1
        declared, used = set(), []
        for line in body[1:]:
            d = _SEQ_DECL.match(line)
            if d:
                declared.add(d.group(1).strip().strip('"'))
                continue
            a = _SEQ_ARROW.match(line)
            if a:
                for actor in (a.group(1).strip(), a.group(3).strip()):
                    if actor not in used:
                        used.append(actor)
        missing = [a for a in used if a not in declared]
        if missing:
            problems.append((seq_index, missing))
    return problems


def _sequence_block_count(prd: str) -> int:
    return sum(
        1 for info, lines in _split_code(prd)[1]
        if info.split()[:1] == ["mermaid"]
        and next((l.strip() for l in lines if l.strip()), "").startswith("sequenceDiagram")
    )


def validate_prd(prd: str, template: str, token: Optional[str] = None) -> List[Dict[str, object]]:
    """Run the automatic checks on a finished PRD. Each item: {id, label, ok, detail}."""
    if token is None:
        token = os.getenv("NGODINGPAKEAI_TOKEN") or ""
    checks: List[Dict[str, object]] = []

    placeholders = find_placeholders(prd)
    checks.append({
        "id": "placeholders",
        "label": "Tidak ada sisa placeholder [ ... ] di luar code block",
        "ok": not placeholders,
        "detail": "; ".join(f"baris {no}: {text}" for no, text in placeholders[:10])
        + (f" (+{len(placeholders) - 10} lagi)" if len(placeholders) > 10 else ""),
    })

    missing = missing_headings(prd, template)
    checks.append({
        "id": "headings",
        "label": "Semua judul bagian wajib ada"
        + (" (0–12, Hasil pengecekan silang, Pertanyaan terbuka)" if template == "fullstack_nextjs" else " (1–15)"),
        "ok": not missing,
        "detail": ("Tidak ada: " + ", ".join(missing)) if missing else "",
    })

    fences = _split_code(prd)[2]
    checks.append({
        "id": "code_fences",
        "label": "Jumlah code fence ``` genap",
        "ok": fences % 2 == 0,
        "detail": f"{fences} fence" + ("" if fences % 2 == 0 else " (ada blok yang tidak ditutup)"),
    })

    undeclared = undeclared_sequence_actors(prd)
    seq_blocks = _sequence_block_count(prd)
    checks.append({
        "id": "sequence_participants",
        "label": "Semua aktor di panah sequenceDiagram sudah dideklarasikan sebagai participant",
        "ok": not undeclared,
        "detail": "; ".join(f"diagram ke-{i}: {', '.join(names)}" for i, names in undeclared)
        if undeclared else (f"{seq_blocks} diagram dicek" if seq_blocks else "Tidak ada blok sequenceDiagram"),
    })

    repo = repo_version(prd)
    leaks = []
    if "ngpk_" in repo:
        leaks.append("string ngpk_")
    if token and token in repo:
        leaks.append("nilai NGODINGPAKEAI_TOKEN")
    checks.append({
        "id": "repo_token",
        "label": "Versi untuk repo (tanpa bagian 0) tidak mengandung token",
        "ok": not leaks,
        "detail": ("Ditemukan " + " dan ".join(leaks)) if leaks else "",  # never echo the token itself
    })
    return checks


class _TextExtractor(HTMLParser):
    """Collect visible text, title and meta description from an HTML page."""

    SKIP = {"script", "style", "noscript", "svg", "template", "iframe"}

    def __init__(self):
        super().__init__()
        self.parts: List[str] = []
        self.title = ""
        self.description = ""
        self._skip_depth = 0
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self._skip_depth += 1
        elif tag == "title":
            self._in_title = True
        elif tag == "meta":
            a = dict(attrs)
            if (a.get("name") or a.get("property") or "").lower() in ("description", "og:description"):
                self.description = self.description or (a.get("content") or "")

    def handle_endtag(self, tag):
        if tag in self.SKIP and self._skip_depth:
            self._skip_depth -= 1
        elif tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._skip_depth:
            return
        text = " ".join(data.split())
        if not text:
            return
        if self._in_title:
            self.title += text
        else:
            self.parts.append(text)


# ---------------------------------------------------------------------------
# Reference fetching (SSRF-hardened)
#
# Every hop (initial URL and each redirect) is validated independently:
#   1. scheme http/https, no userinfo, port 80/443, no internal-looking host name;
#   2. the host is resolved once and EVERY returned address must be public;
#   3. the connection goes to that resolved IP (pinned), with the original Host
#      header and TLS SNI/certificate verification against the original host name,
#      so a second DNS answer (rebinding) can never be used.
# Proxies from the environment are ignored (trust_env=False). Only short, generic
# error messages leave this module; details go to the server log.
# ---------------------------------------------------------------------------

_PUBLIC_ERRORS = {
    "disabled": "Reference fetching is disabled on this server",
    "invalid_url": "Invalid or unsupported URL",
    "blocked": "Address not allowed",
    "dns": "Host could not be resolved",
    "redirects": "Too many redirects",
    "http_status": "The website returned an error",
    "content_type": "Unsupported content type",
    "too_large": "Page is too large",
    "timeout": "Timed out",
    "failed": "Could not be loaded",
}

_BLOCKED_HOSTNAMES = frozenset({"localhost", "metadata", "metadata.google.internal", "instance-data"})
_BLOCKED_HOST_SUFFIXES = (".localhost", ".local", ".internal", ".localdomain", ".home.arpa")

# Explicit deny lists; `is_global` alone is not trusted (e.g. 168.63.129.16 and
# NAT64 addresses are reported as global).
_BLOCKED_V4 = tuple(ipaddress.ip_network(n) for n in (
    "0.0.0.0/8", "10.0.0.0/8", "100.64.0.0/10", "127.0.0.0/8", "169.254.0.0/16",
    "172.16.0.0/12", "192.0.0.0/24", "192.0.2.0/24", "192.88.99.0/24", "192.168.0.0/16",
    "198.18.0.0/15", "198.51.100.0/24", "203.0.113.0/24", "224.0.0.0/4", "240.0.0.0/4",
    "168.63.129.16/32",   # Azure WireServer / platform metadata
    "100.100.100.200/32",  # Alibaba Cloud metadata (also inside 100.64/10)
))
_BLOCKED_V6 = tuple(ipaddress.ip_network(n) for n in (
    "::/96",          # unspecified, loopback, IPv4-compatible (deprecated)
    "::ffff:0:0/96",  # IPv4-mapped (handled by unwrapping as well)
    "64:ff9b:1::/48",  # local-use NAT64
    "100::/64",        # discard-only
    "2001::/23",       # IETF protocol assignments (Teredo, benchmarking, ORCHID, ...)
    "2001:db8::/32",   # documentation
    "2002::/16",       # 6to4
    "3fff::/20",       # documentation
    "fc00::/7",        # unique local (includes AWS fd00:ec2::254)
    "fe80::/10",       # link-local
    "fec0::/10",       # site-local (deprecated)
    "ff00::/8",        # multicast
))
_NAT64_WKP = ipaddress.ip_network("64:ff9b::/96")


class _FetchError(Exception):
    """Internal error with a public category; `detail` is only logged."""

    def __init__(self, code: str, detail: str = ""):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def reference_fetch_enabled() -> bool:
    return os.getenv(REFERENCE_FETCH_ENV, "1").strip().lower() not in {"0", "false", "no", "off"}


def is_public_ip(address: str) -> bool:
    """True only for globally routable unicast addresses that are not on a deny list."""
    try:
        ip = ipaddress.ip_address(address.split("%", 1)[0])
    except ValueError:
        return False
    if isinstance(ip, ipaddress.IPv6Address):
        if ip.ipv4_mapped is not None:
            return is_public_ip(str(ip.ipv4_mapped))
        if ip in _NAT64_WKP:  # 64:ff9b::a.b.c.d -> judge the embedded IPv4 address
            return is_public_ip(str(ipaddress.IPv4Address(int(ip) & 0xFFFFFFFF)))
        blocked = _BLOCKED_V6
    else:
        blocked = _BLOCKED_V4
    if any(ip in net for net in blocked):
        return False
    return bool(
        ip.is_global
        and not ip.is_private
        and not ip.is_loopback
        and not ip.is_link_local
        and not ip.is_multicast
        and not ip.is_reserved
        and not ip.is_unspecified
    )


def _validate_url(url: str) -> Tuple[httpx.URL, str, int]:
    """Static checks on one URL. Returns (url, host, port)."""
    try:
        u = httpx.URL(url)
    except Exception as e:
        raise _FetchError("invalid_url", repr(e))
    if u.scheme not in ("http", "https"):
        raise _FetchError("invalid_url", f"scheme {u.scheme!r}")
    if u.userinfo:
        raise _FetchError("blocked", "userinfo in URL")
    host = (u.host or "").rstrip(".").lower()
    if not host:
        raise _FetchError("invalid_url", "empty host")
    port = u.port or (443 if u.scheme == "https" else 80)
    if port not in REFERENCE_ALLOWED_PORTS:
        raise _FetchError("blocked", f"port {port}")
    try:
        ipaddress.ip_address(host.split("%", 1)[0])
        is_literal = True
    except ValueError:
        is_literal = False
    if not is_literal:
        if host in _BLOCKED_HOSTNAMES or host.endswith(_BLOCKED_HOST_SUFFIXES):
            raise _FetchError("blocked", f"host {host!r}")
        if "." not in host:  # single-label names resolve via internal search domains
            raise _FetchError("blocked", f"single-label host {host!r}")
    return u, host, port


async def _resolve_host(host: str, port: int) -> List[str]:
    """Resolve a host name to the list of addresses the OS would connect to."""
    loop = asyncio.get_running_loop()
    infos = await loop.getaddrinfo(host, port, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)
    return [info[4][0] for info in infos]


async def _resolve_public(host: str, port: int) -> str:
    """Resolve once; reject if ANY address is non-public; return the address to pin."""
    try:
        literal = ipaddress.ip_address(host.split("%", 1)[0])
    except ValueError:
        literal = None
    if literal is not None:  # IP literal: no DNS lookup needed
        if not is_public_ip(str(literal)):
            raise _FetchError("blocked", f"non-public literal {literal}")
        return str(literal)
    try:
        addresses = await _resolve_host(host, port)
    except _FetchError:
        raise
    except Exception as e:
        raise _FetchError("dns", repr(e))
    addresses = list(dict.fromkeys(a.split("%", 1)[0] for a in addresses))
    if not addresses:
        raise _FetchError("dns", "no addresses")
    bad = [a for a in addresses if not is_public_ip(a)]
    if bad:
        raise _FetchError("blocked", f"{host} resolves to non-public {bad}")
    return addresses[0]


def _build_transport() -> Optional[httpx.AsyncBaseTransport]:
    """Transport for reference fetching; None = httpx default (TLS verification on). Tests replace this."""
    return None


_semaphores: "weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, asyncio.Semaphore]" = weakref.WeakKeyDictionary()


def _fetch_semaphore() -> asyncio.Semaphore:
    """One global limiter per event loop (a Semaphore must not be shared across loops)."""
    loop = asyncio.get_running_loop()
    sem = _semaphores.get(loop)
    if sem is None:
        sem = _semaphores[loop] = asyncio.Semaphore(MAX_CONCURRENT_FETCHES)
    return sem


async def _read_limited(resp: httpx.Response) -> bytes:
    declared = resp.headers.get("content-length")
    if declared is not None:
        try:
            if int(declared) > MAX_REFERENCE_BYTES:
                raise _FetchError("too_large", f"content-length {declared}")
        except ValueError:
            pass
    body = bytearray()
    async for chunk in resp.aiter_bytes():  # decoded bytes, so compression bombs are capped too
        body.extend(chunk)
        if len(body) >= MAX_REFERENCE_BYTES:
            del body[MAX_REFERENCE_BYTES:]
            break
    return bytes(body)


async def _fetch_page(url: str) -> Tuple[str, str]:
    """Fetch one page with per-hop validation and IP pinning. Returns (final_url, text)."""
    current = url
    async with httpx.AsyncClient(
        transport=_build_transport(),
        trust_env=False,
        follow_redirects=False,
        verify=True,
        timeout=REFERENCE_HTTP_TIMEOUT,
        headers={"User-Agent": "Mozilla/5.0 (GTPlanner PRD generator)"},
    ) as client:
        for _hop in range(MAX_REFERENCE_REDIRECTS + 1):
            u, host, port = _validate_url(current)
            ip = await _resolve_public(host, port)
            request = client.build_request(
                "GET",
                u.copy_with(host=ip),
                headers={"Host": u.netloc.decode("ascii")},
                extensions={"sni_hostname": u.host} if u.scheme == "https" else {},
            )
            resp = await client.send(request, stream=True)
            try:
                if resp.status_code in (301, 302, 303, 307, 308):
                    location = resp.headers.get("location")
                    if not location:
                        raise _FetchError("http_status", f"redirect without location ({resp.status_code})")
                    current = str(u.join(location))  # resolve against the ORIGINAL url, not the pinned one
                    continue
                if resp.status_code >= 400:
                    raise _FetchError("http_status", f"HTTP {resp.status_code}")
                ctype = resp.headers.get("content-type", "").split(";", 1)[0].strip().lower()
                if ctype not in REFERENCE_CONTENT_TYPES:
                    raise _FetchError("content_type", ctype or "missing")
                raw = await _read_limited(resp)
                encoding = resp.charset_encoding or "utf-8"
                try:
                    text = raw.decode(encoding, errors="replace")
                except LookupError:
                    text = raw.decode("utf-8", errors="replace")
                return current, text
            finally:
                await resp.aclose()
    raise _FetchError("redirects", f"more than {MAX_REFERENCE_REDIRECTS}")


def _failure(url: str, code: str) -> Dict[str, str]:
    return {"url": url, "ok": False, "error": _PUBLIC_ERRORS.get(code, _PUBLIC_ERRORS["failed"])}


async def fetch_reference(url: str) -> Dict[str, str]:
    """Download a public reference web page and return a compact text summary of it.

    Never raises (except cancellation); failures return {"ok": False, "error": <generic message>}.
    """
    if not reference_fetch_enabled():
        return _failure(url, "disabled")
    try:
        async with _fetch_semaphore():
            async with asyncio.timeout(REFERENCE_TOTAL_TIMEOUT):
                _final_url, html = await _fetch_page(url)
    except _FetchError as e:
        logger.warning("Reference fetch rejected/failed for %s: %s (%s)", url, e.code, e.detail)
        return _failure(url, e.code)
    except TimeoutError:
        logger.warning("Reference fetch timed out for %s", url)
        return _failure(url, "timeout")
    except httpx.TimeoutException as e:
        logger.warning("Reference fetch timed out for %s: %r", url, e)
        return _failure(url, "timeout")
    except Exception as e:  # network errors must not block PRD generation or leak details
        logger.warning("Reference fetch failed for %s: %r", url, e)
        return _failure(url, "failed")

    parser = _TextExtractor()
    try:
        parser.feed(html)
        parser.close()
    except Exception as e:  # pragma: no cover - HTMLParser is lenient
        logger.warning("Reference parse failed for %s: %r", url, e)
    text = " | ".join(parser.parts)
    return {
        "url": url,
        "ok": True,
        "title": parser.title.strip(),
        "description": parser.description.strip(),
        "text": text[:MAX_REFERENCE_CHARS],
    }




def build_messages(
    request: str,
    language: str,
    references: List[Dict[str, str]],
    previous_prd: Optional[str] = None,
) -> List[Dict[str, str]]:
    """Build the user message for a new PRD or a revision."""
    if language and language != "auto":
        lang_rule = f"Write the content in {LANGUAGE_NAMES.get(language, language)} (keep the template headings as they are)."
    else:
        lang_rule = "Write the content in the same language as the user's request (keep the template headings as they are)."

    ref_block = ""
    for ref in references:
        if ref.get("ok"):
            ref_block += (
                f"\n\n### Reference website: {ref['url']}\n"
                f"Title: {ref.get('title', '')}\n"
                f"Description: {ref.get('description', '')}\n"
                f"Page text (truncated):\n{ref.get('text', '')}"
            )
        else:
            ref_block += f"\n\n(Reference website {ref['url']} could not be loaded: {ref.get('error')}. Rely on general knowledge of similar products.)"

    if previous_prd:
        content = (
            f"Here is the current PRD (product name: {product_name_of(previous_prd)}):\n\n"
            f"<current_prd>\n{strip_header(previous_prd)}\n</current_prd>\n\n"
            f"Revise it according to this request: {request}\n\n"
            "Return the complete updated document in the required output format (PRODUCT_NAME line first, then all "
            f"sections, not only the changes). Keep feature and rule IDs stable; add new ones with the next free number. {lang_rule}"
        )
    else:
        content = f"Write the PRD for the following product request:\n\n{request}\n\n{lang_rule}"

    if ref_block:
        content += "\n\nReference material:" + ref_block

    return [{"role": "user", "content": content}]


async def stream_prd(
    request: str,
    language: str = "auto",
    previous_prd: Optional[str] = None,
    template: str = DEFAULT_TEMPLATE,
) -> AsyncIterator[Dict[str, object]]:
    """
    Generate a PRD and yield events:
    {"type": "status", "message": str}
    {"type": "reference", "url": str, "ok": bool, "title"/"error": str}
    {"type": "chunk", "content": str}
    {"type": "validation", "finish_reason": str|None, "truncated": bool, "max_tokens": int|None,
     "checks": [{"id", "label", "ok", "detail"}], "valid": bool}
    {"type": "done", "content": str, "truncated": bool, "valid": bool}
    """
    if template not in TEMPLATES:
        template = DEFAULT_TEMPLATE

    urls = list(dict.fromkeys(URL_PATTERN.findall(request)))[:MAX_REFERENCES]
    references: List[Dict[str, str]] = []
    if urls:
        if reference_fetch_enabled():
            for url in urls:
                yield {"type": "status", "message": f"Reading reference website {url} ..."}
            # Fetched concurrently (bounded by the global semaphore); events keep URL order.
            references = list(await asyncio.gather(*(fetch_reference(url) for url in urls)))
        else:  # no network access at all when disabled
            references = [_failure(url, "disabled") for url in urls]
    for url, ref in zip(urls, references):
        yield {
            "type": "reference",
            "url": url,
            "ok": ref.get("ok", False),
            "title": ref.get("title", ""),
            "error": ref.get("error", ""),
        }

    yield {"type": "status", "message": "Revising the PRD..." if previous_prd else "Writing the PRD..."}

    client = get_openai_client()
    messages = build_messages(request, language, references, previous_prd)

    # The first output line carries the product name; buffer until it is complete,
    # then emit the fixed template header followed by the generated sections.
    pending = ""
    header_sent = False
    full = ""
    finish_reason: Optional[str] = None

    async for chunk in client.chat_completion_stream(messages=messages, system_prompt=system_prompt_for(template)):
        if not getattr(chunk, "choices", None):
            continue
        reason = getattr(chunk.choices[0], "finish_reason", None)
        if reason:
            finish_reason = str(reason)
        delta = getattr(chunk.choices[0], "delta", None)
        piece = getattr(delta, "content", None) if delta is not None else None
        if not piece:
            continue
        if header_sent:
            full += piece
            yield {"type": "chunk", "content": piece}
            continue

        pending += piece
        stripped = pending.lstrip()
        if stripped.startswith("```"):  # tolerate a leading code fence
            nl = stripped.find("\n")
            if nl < 0:
                continue
            pending = stripped[nl + 1:]
            stripped = pending.lstrip()
        if "\n" not in stripped and len(stripped) < 200:
            continue  # first line not complete yet

        first_line, _, rest = stripped.partition("\n")
        m = NAME_LINE.match(first_line)
        if m:
            name = m.group(1).strip().strip("*`#").strip()
            body = rest
        else:  # model ignored the format; keep everything as body
            name = product_name_of(previous_prd) if previous_prd else "Produk"
            body = stripped
        header = render_header(template, name)
        header_sent = True
        full = header + body.lstrip("\n")
        yield {"type": "chunk", "content": full}

    if not header_sent and pending.strip():
        stripped = pending.strip()
        first_line, _, rest = stripped.partition("\n")
        m = NAME_LINE.match(first_line)
        name = m.group(1).strip() if m else "Produk"
        full = render_header(template, name) + (rest if m else stripped)
        yield {"type": "chunk", "content": full}

    # Drop a trailing code fence if the model wrapped its answer, and any Lampiran it added anyway
    full = re.sub(r"\n```\s*$", "\n", full.rstrip())
    footer = render_footer(template)
    if footer:
        lamp = re.search(r"^## Lampiran", full, re.MULTILINE)
        if lamp:
            full = full[:lamp.start()].rstrip()
        full += footer
        yield {"type": "chunk", "content": footer}
    full = full.rstrip() + "\n"

    truncated = finish_reason in TRUNCATION_REASONS
    max_tokens = getattr(getattr(client, "config", None), "max_tokens", None)
    checks = validate_prd(full, template)
    valid = not truncated and all(c["ok"] for c in checks)
    if truncated:
        logger.warning("PRD output truncated by the model (finish_reason=%s, max_tokens=%s)", finish_reason, max_tokens)
    yield {
        "type": "validation",
        "finish_reason": finish_reason,
        "truncated": truncated,
        "max_tokens": max_tokens,
        "checks": checks,
        "valid": valid,
    }
    yield {"type": "done", "content": full, "truncated": truncated, "valid": valid}
