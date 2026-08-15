"""Generate the deterministic, entirely fictional incident record set."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"

FILES: dict[str, str] = {
    "01_initial_access.txt": """Security Access Record

On 2026-04-02, Maya Chen authorized account SEC-104 for Northstar Systems Corp.
The record belongs to the fictional Northstar training environment.
""",
    "02_endpoint_alert.md": """# Endpoint Alert Review

On 2026-04-05, Priya Shah notified Maya Chen about unusual activity on account SEC-104.

This synthetic alert contains no real people, systems, or account data.
""",
    "03_triage_message.eml": """From: Priya Shah <priya.shah@example.test>
To: Maya Chen <maya.chen@example.test>
Date: Mon, 06 Apr 2026 09:15:00 +0000
Subject: Synthetic incident triage
Message-ID: <triage-20260406@example.test>
MIME-Version: 1.0
Content-Type: text/plain; charset=utf-8

On 2026-04-06, Priya Shah submitted Case IR-2026-041 to Northstar Systems Corp.
This message is deterministic synthetic test data.
""",
    "04_containment.txt": """Containment Record

On 2026-04-07, Maya Chen rejected account SEC-104 access at Northstar Systems Corp.
This synthetic record represents the containment step.
""",
    "05_recovery.md": (
        "# Recovery Authorization\n\n"
        "On 2026-04-09, Elena Torres authorized account SEC-104 after credential rotation at "
        "Northstar Systems Corp.\n\n"
        "This is a fictional recovery record for a software demonstration.\n"
    ),
}


def expected_bytes() -> dict[str, bytes]:
    """Return canonical UTF-8 bytes, always with LF line endings."""

    return {name: text.encode("utf-8") for name, text in sorted(FILES.items())}


def generate(*, check: bool = False) -> list[str]:
    """Write canonical fixtures or report files that differ from them."""

    expected = expected_bytes()
    differences: list[str] = []

    for name, content in expected.items():
        destination = DATA_DIR / name
        if not destination.is_file() or destination.read_bytes() != content:
            differences.append(name)
            if not check:
                DATA_DIR.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(content)

    if DATA_DIR.is_dir():
        unexpected = sorted(
            path.name for path in DATA_DIR.iterdir() if path.is_file() and path.name not in expected
        )
        differences.extend(f"unexpected:{name}" for name in unexpected)

    return differences


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit nonzero instead of writing when committed data differs",
    )
    args = parser.parse_args()

    differences = generate(check=args.check)
    if args.check and differences:
        print("Synthetic data is out of date:", file=sys.stderr)
        for difference in differences:
            print(f"- {difference}", file=sys.stderr)
        return 1

    if args.check:
        print(f"Synthetic data is current ({len(FILES)} files).")
    else:
        print(f"Generated {len(FILES)} synthetic files in {DATA_DIR.relative_to(ROOT)}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
