"""
Run proof vector cases against the Python verifier.

Usage: verify_proof_offline.py <vector_file>
Exit 0 iff every case's outcome matches its 'expected' field.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from verify_garden import verify_proof


def main(path: str) -> int:
    v = json.loads(Path(path).read_text())
    matched = 0
    mismatches = []
    for case in v["cases"]:
        try:
            verify_proof(
                case["body"], case["proof"], case["expected_did"])
            got, err = "pass", None
        except Exception as e:
            got, err = "fail", str(e)
        if got == case["expected"]:
            matched += 1
        else:
            msg = (f"  [{case['id']}] expected {case['expected']} "
                   f"got {got}")
            if err:
                msg += f": {err}"
            mismatches.append(msg)

    print("=== vector runner (Python) ===")
    print(f"  identity: {v['identity']['did']}")
    print(f"  cases:    {len(v['cases'])}")
    print(f"  match:    {matched}/{len(v['cases'])}")
    if mismatches:
        print()
        print("  mismatches:")
        for m in mismatches:
            print(m)
        return 1
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: verify_proof_offline.py <vector_file>",
              file=sys.stderr)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
