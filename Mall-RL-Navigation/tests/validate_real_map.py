"""
Ambience Mall Gurugram Real Map Validation Script.

Run via:
python tests/validate_real_map.py
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.map_validator import MapValidator


def main():
    print("=" * 70)
    print("AMBIENCE MALL GURUGRAM — MASTER SPATIAL DATA VALIDATION REPORT")
    print("=" * 70)

    validator = MapValidator()
    report = validator.run_all_checks()

    print(f"Validation Status: {'✅ PASSED' if report['passed'] else '❌ FAILED'}")
    print()
    print("--- Summary Statistics ---")
    for k, v in report["stats"].items():
        print(f"  {k:25}: {v}")

    if report["warnings"]:
        print()
        print(f"--- Warnings ({len(report['warnings'])}) ---")
        for w in report["warnings"]:
            print(f"  ⚠️  {w}")

    if report["issues"]:
        print()
        print(f"--- Issues Detected ({len(report['issues'])}) ---")
        for err in report["issues"]:
            print(f"  ❌ {err}")
        sys.exit(1)
    else:
        print()
        print("🎉 All spatial integrity and graph connectivity checks passed with zero errors!")
        print("=" * 70)
        sys.exit(0)


if __name__ == "__main__":
    main()
