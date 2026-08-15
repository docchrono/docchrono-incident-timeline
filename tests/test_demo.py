from __future__ import annotations

import hashlib
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path

import demo

ROOT = Path(__file__).resolve().parents[1]


def test_demo_matches_committed_output() -> None:
    result = subprocess.run(
        [sys.executable, "demo.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stderr == ""
    assert result.stdout == (ROOT / "expected_output.txt").read_text(encoding="utf-8")


def test_committed_synthetic_data_is_canonical() -> None:
    result = subprocess.run(
        [sys.executable, "generate_data.py", "--check"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_released_package_builds_a_complete_mixed_format_case() -> None:
    case = demo.build_case()

    assert version("docchrono") == "0.1.0"
    assert case.report.complete
    assert len(case.source_references) == 5
    assert len(case.documents) == 5
    assert {document.media_type for document in case.documents} == {
        "message/rfc822",
        "text/markdown",
        "text/plain",
    }
    assert not case.report.failures
    assert not case.timeline.undated
    assert [demo.event_date(event) for event in case.timeline] == sorted(
        demo.event_date(event) for event in case.timeline
    )


def test_every_event_has_exact_source_provenance() -> None:
    case = demo.build_case()
    document_by_id = {document.id: document for document in case.documents}
    source_by_id = {source.id: source for source in case.source_references}

    for event in case.events:
        records = demo.event_provenance(case, event)
        assert records
        for span in case.evidence(event):
            document = document_by_id[span.document_id]
            assert span.quote == document.raw_text[span.raw_start : span.raw_end]
            for source_id in document.source_reference_ids:
                source = source_by_id[source_id]
                source_bytes = (ROOT / "data" / source.filename).read_bytes()
                assert hashlib.sha256(source_bytes).hexdigest() == source.content_sha256
                assert document.content_sha256 == source.content_sha256
