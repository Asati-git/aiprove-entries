"""Enter + submit the skill-bounty entries (code repos and the bug-hunt list).

Usage:
    python submit_entries.py                 # dry run
    python submit_entries.py --live          # actually enter + submit
    python submit_entries.py --live --only fastest-primes,code-golf-expr
"""

from __future__ import annotations

import argparse
import json
import logging
import sys

sys.path.insert(0, __file__.rsplit("\\", 1)[0])

from aiprove.client import AIProveClient
from aiprove.wallet import load_wallet
from transcripts import transcript_for

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

BUGS = [
    # utils.js factorial(): loop bound is i<n, dropping the final multiply.
    {"fn": "factorial", "input": 5, "expected": 120},
    # utils.js countVowels(): regex /[aeiou]/ misses uppercase vowels.
    {"fn": "countVowels", "input": "AIProve", "expected": 4},
]

# slug -> entry description
CODE_ENTRIES = ["fastest-primes", "code-golf-expr", "eth-pnl-fixed"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--only", help="comma-separated slugs")
    args = ap.parse_args()

    root = __file__.rsplit("\\", 1)[0]
    cfg = json.load(open(root + "\\config.json", encoding="utf-8"))
    wcfg = cfg["wallet"]
    address, pk = load_wallet(address=wcfg.get("address"), db_path=wcfg.get("db_path"))
    repo_state = json.load(open(root + "\\repo_state.json", encoding="utf-8"))

    client = AIProveClient(pk, api_base=cfg["api_base"], handle=cfg["handle"], dry_run=not args.live)
    client.authenticate()

    slugs = set(args.only.split(",")) if args.only else None

    for slug in CODE_ENTRIES:
        if slugs and slug not in slugs:
            continue
        client.enter(slug)
        client.submit_code(slug, repo_state["url"], repo_state["commit"], transcript_for(slug))
        print(f"[{'LIVE' if args.live else 'dry'}] {slug}: repo {repo_state['url']} @ {repo_state['commit'][:8]}")

    if not slugs or "bug-hunt-utils" in slugs:
        client.enter("bug-hunt-utils")
        client.submit_bughunt("bug-hunt-utils", BUGS)
        print(f"[{'LIVE' if args.live else 'dry'}] bug-hunt-utils: {len(BUGS)} bugs reported")

    if args.live:
        me = client.me()
        print(json.dumps(me, indent=2, ensure_ascii=False)[:3000])


if __name__ == "__main__":
    main()
