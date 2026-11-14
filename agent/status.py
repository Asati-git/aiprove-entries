"""Check the authenticated agent's arena status: entries, submissions, results."""

import argparse
import json
import sys

sys.path.insert(0, __file__.rsplit("\\", 1)[0])

from aiprove.client import AIProveClient
from aiprove.wallet import load_wallet


def main() -> None:
    root = __file__.rsplit("\\", 1)[0]
    cfg = json.load(open(root + "\\config.json", encoding="utf-8"))
    wcfg = cfg["wallet"]
    address, pk = load_wallet(address=wcfg.get("address"), db_path=wcfg.get("db_path"))
    client = AIProveClient(pk, api_base=cfg["api_base"], handle=cfg["handle"])
    client.authenticate()
    print("address:", client.address)
    print(json.dumps(client.me(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
