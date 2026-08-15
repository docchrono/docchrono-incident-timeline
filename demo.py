"""Build and print a source-linked chronology from the synthetic incident files."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from importlib.metadata import version
from pathlib import Path

from docchrono import Case
from docchrono.domain import Event, EvidenceSpan

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
REQUIRED_DOCCHRONO_VERSION = "0.1.0"


@dataclass(frozen=True, slots=True)
class Provenance:
    """The source coordinates behind one extracted event."""

    filename: str
    sha256: str
    raw_start: int
    raw_end: int
    field: str | None
    quote: str


def build_case() -> Case:
    """Analyze all committed fixtures with the released package."""

    installed = version("docchrono")
    if installed != REQUIRED_DOCCHRONO_VERSION:
        raise RuntimeError(
            f"This showcase requires docchrono=={REQUIRED_DOCCHRONO_VERSION}; found {installed}."
        )
    return Case.build(DATA_DIR, strict=True)


def event_date(event: Event) -> str:
    """Return the earliest resolved boundary used by the timeline."""

    starts = sorted(
        temporal.start
        for temporal in event.temporal
        if temporal.resolved and temporal.start is not None
    )
    if not starts:
        raise ValueError(f"event is not dated: {event.id}")
    return starts[0]


def event_provenance(case: Case, event: Event) -> tuple[Provenance, ...]:
    """Resolve an event's exact quote, offsets, file, and full content digest."""

    document_by_id = {document.id: document for document in case.documents}
    source_by_id = {source.id: source for source in case.source_references}
    records: list[Provenance] = []

    for span in sorted(case.evidence(event), key=_span_sort_key):
        document = document_by_id[span.document_id]
        if document.raw_text[span.raw_start : span.raw_end] != span.quote:
            raise AssertionError(f"raw offsets do not reproduce evidence span {span.id}")

        for source_id in document.source_reference_ids:
            source = source_by_id[source_id]
            source_path = DATA_DIR / source.filename
            actual_digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
            if actual_digest != source.content_sha256:
                raise AssertionError(f"source digest changed for {source.filename}")
            if source.content_sha256 != document.content_sha256:
                raise AssertionError(f"document/source digest mismatch for {source.filename}")
            records.append(
                Provenance(
                    filename=source.filename,
                    sha256=source.content_sha256,
                    raw_start=span.raw_start,
                    raw_end=span.raw_end,
                    field=span.field,
                    quote=span.quote,
                )
            )

    if not records:
        raise AssertionError(f"event has no evidence: {event.id}")
    return tuple(sorted(records, key=_provenance_sort_key))


def render(case: Case) -> str:
    """Render deterministic, human-readable demo output."""

    lines = [
        "DocChrono synthetic security incident",
        f"docchrono: {case.report.manifest.docchrono_version}",
        f"build complete: {str(case.report.complete).lower()}",
        f"documents: {len(case.documents)}",
        f"events: {len(case.events)}",
        f"relationships: {len(case.relationships)}",
        f"dated timeline: {len(case.timeline)}",
        f"undated events: {len(case.timeline.undated)}",
        "",
        "Chronology (extracted claims are provisional):",
    ]

    for index, event in enumerate(case.timeline, start=1):
        lines.append(
            f"{index}. {event_date(event)} | {event.type.value} | {event.title} "
            f"| score={event.score:.3f}"
        )
        for source in event_provenance(case, event):
            field = source.field if source.field is not None else "-"
            lines.append(
                f"   source={source.filename} sha256={source.sha256} "
                f"raw={source.raw_start}:{source.raw_end} field={field}"
            )
            lines.append(f"   quote={json.dumps(source.quote, ensure_ascii=False)}")

    if case.timeline.undated:
        lines.extend(("", "Undated events:"))
        for event in case.timeline.undated:
            lines.append(f"- {event.type.value} | {event.title}")

    return "\n".join(lines) + "\n"


def _span_sort_key(span: EvidenceSpan) -> tuple[object, ...]:
    return span.document_id, span.raw_start, span.raw_end, span.id


def _provenance_sort_key(record: Provenance) -> tuple[object, ...]:
    return record.filename, record.raw_start, record.raw_end, record.quote


def main() -> None:
    print(render(build_case()), end="")


if __name__ == "__main__":
    main()
