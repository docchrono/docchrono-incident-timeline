# DocChrono Incident Timeline

[![CI](https://github.com/docchrono/docchrono-incident-timeline/actions/workflows/ci.yml/badge.svg)](https://github.com/docchrono/docchrono-incident-timeline/actions/workflows/ci.yml)
[![DocChrono 0.1.0](https://img.shields.io/badge/DocChrono-0.1.0-3776ab)](https://pypi.org/project/docchrono/0.1.0/)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)

A complete, runnable example that turns five fictional security-incident records into a
source-linked chronology with [`docchrono==0.1.0`](https://pypi.org/project/docchrono/0.1.0/).
It uses plain text, Markdown, and an RFC 822 email, makes no cloud-AI calls, and prints the exact
source quote, raw character offsets, and SHA-256 digest behind every extracted event.

> [!IMPORTANT]
> Every person, organization, email address, account, case, and event in this repository is
> synthetic. `example.test` is a reserved example domain. Do not treat this demonstration as a
> real incident report or as a security-detection system.

## What this demonstrates

- `Case.build(...)` over a directory containing `.txt`, `.md`, and `.eml` files.
- `case.timeline`, including an RFC 822 `Date` header normalized to an instant.
- `case.evidence(event)` for source-linked event evidence.
- Exact provenance verification: quote ↔ raw offsets ↔ parsed document ↔ source SHA-256.
- Deterministic fixture generation and output checked in CI on Python 3.11 and 3.13.

The standard DocChrono pipeline is local and rule-based. It extracts *candidate claims*; the
events shown here remain provisional and should be reviewed in real workflows.

## Run it

DocChrono 0.1.0 supports CPython 3.11–3.13.

```bash
python -m venv .venv
```

Activate the environment:

```bash
# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Install the exact released package and run the demo:

```bash
python -m pip install -r requirements.txt
python generate_data.py --check
python demo.py
```

No API key, model download, service account, or network call is needed while `demo.py` runs.
The install command uses PyPI; subsequent analysis is local.

## Output

The complete stable output is committed in [`expected_output.txt`](expected_output.txt). The
opening entries look like this:

```text
DocChrono synthetic security incident
docchrono: 0.1.0
build complete: true
documents: 5
events: 6
relationships: 18
dated timeline: 6
undated events: 0

Chronology (extracted claims are provisional):
1. 2026-04-02 | DECISION | Authorized: account SEC-104 for Northstar Systems Corp | score=0.920
   source=01_initial_access.txt sha256=d004ed29... raw=39:102 field=-
   quote="Maya Chen authorized account SEC-104 for Northstar Systems Corp"
```

The full 64-character digest is printed by the actual demo. A provenance line means:

- `source`: the original file linked to the parsed document;
- `sha256`: DocChrono's full content digest, re-computed from disk by this demo;
- `raw=39:102`: Python slice coordinates in `Document.raw_text` (start inclusive, end exclusive);
- `field`: a structured field when the evidence is confined to one, otherwise `-`;
- `quote`: the exact result of `document.raw_text[raw_start:raw_end]`.

`demo.py` fails rather than printing misleading output if any source digest, document digest,
raw slice, or evidence quote disagrees.

## Synthetic data map

| File | Format | Fictional incident step | Expected extracted event |
| --- | --- | --- | --- |
| `01_initial_access.txt` | UTF-8 text | Access granted | `AUTHORIZED` decision on 2026-04-02 |
| `02_endpoint_alert.md` | Markdown | Analyst notification | `NOTIFIED` communication on 2026-04-05 |
| `03_triage_message.eml` | RFC 822 email | Triage message and case submission | `SUBMITTED` action plus header-derived `EMAIL_SENT` |
| `04_containment.txt` | UTF-8 text | Access rejected | `REJECTED` decision on 2026-04-07 |
| `05_recovery.md` | Markdown | Recovery authorization | `AUTHORIZED` decision on 2026-04-09 |

The source text deliberately uses verbs recognized by DocChrono 0.1.0's finite English rules.
That makes the example reproducible while keeping the package's precision/recall tradeoff
visible.

## API walkthrough

Build a case. `strict=True` makes an unsupported or malformed input fail the run instead of
leaving a partial case unnoticed:

```python
from docchrono import Case

case = Case.build("data", strict=True)
assert case.report.complete
```

`timeline` is a property and a deterministic sequence of dated `Event` objects—not a method:

```python
for event in case.timeline:
    print(event.title, event.temporal, event.provisional)

for event in case.timeline.undated:
    print("needs a date:", event.title)
```

Follow an event to its exact evidence span:

```python
event = case.timeline[0]
for span in case.evidence(event):
    document = next(doc for doc in case.documents if doc.id == span.document_id)
    assert span.quote == document.raw_text[span.raw_start : span.raw_end]
    print(span.quote, span.raw_start, span.raw_end, span.field)
```

Documents link to immutable source records through `source_reference_ids`; those source records
carry the filename and content digest:

```python
sources = {source.id: source for source in case.source_references}
document = case.documents[0]

for source_id in document.source_reference_ids:
    source = sources[source_id]
    assert source.content_sha256 == document.content_sha256
    print(source.filename, source.content_sha256)
```

See [`event_provenance`](demo.py) for the complete, defensive join used by this showcase.

## Regenerate and test

`generate_data.py` uses only fixed strings and UTF-8/LF encoding. It never reads the clock,
random state, environment, or network.

```bash
# Recreate missing or changed fixtures
python generate_data.py

# Verify committed fixtures without changing them
python generate_data.py --check

# Install test dependencies and run all checks
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

The tests prove that:

1. the demo output exactly matches `expected_output.txt`;
2. committed fixtures match the generator byte-for-byte;
3. the build consumes the production `docchrono==0.1.0` distribution;
4. all three formats parse successfully and every event is dated; and
5. every event's quote, offsets, document digest, and source bytes agree.

CI installs from `requirements-dev.txt` on Python 3.11 and 3.13. GitHub Actions are pinned by
full commit SHA, and the workflow has read-only repository permissions.

## Repository layout

```text
.
├── .github/workflows/ci.yml  # SHA-pinned Python 3.11/3.13 checks
├── data/                     # committed fictional source documents
├── tests/test_demo.py        # behavior and provenance checks
├── demo.py                   # DocChrono build and report
├── expected_output.txt       # golden output from docchrono 0.1.0
├── generate_data.py          # deterministic fixture generator/checker
├── requirements.txt          # production release pin
└── requirements-dev.txt      # test dependencies
```

## Deliberate limitations

- This is an API example, not an intrusion-detection, forensic, SIEM, or incident-response tool.
- DocChrono 0.1.0 uses finite English rules and does not understand arbitrary security prose.
- Extracted events are provisional source claims, not independently verified facts.
- The example does not demonstrate contradiction detection, semantic search, OCR, spreadsheets,
  visualization, or a general OWL/RDF ontology; those are not DocChrono 0.1.0 features.
- The email communication event is structural: it comes from `From`, `To`, and `Date` headers.
- Identical inputs and software versions are required for byte-for-byte golden output.

For the package API and its complete limits, see the
[DocChrono repository](https://github.com/docchrono/docchrono) and
[DocChrono 0.1.0 on PyPI](https://pypi.org/project/docchrono/0.1.0/).

## License

Apache License 2.0. See [`LICENSE`](LICENSE).
