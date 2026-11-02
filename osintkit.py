#!/usr/bin/env python3
"""
OSINTKit — modular open-source intelligence toolkit
D3F4UL7T

Passive / public-data only. Authorized research use.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

VERSION = "1.0.0"
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

BANNER = r"""
   ____  _____ _____ _   _ _______ _  ___ _
  / __ \/ ___//  _/ | / //_  __/ | / / /|/ /
 / / / /\__ \ / //  |/ /  / /  | |/ /  /| /
/ /_/ /___/ // // /|  /  / /   |   / /|  /
\____//____/___/_/ |_/  /_/    /_/|_/ |_/
  modular OSINT toolkit  |  D3F4UL7T
"""

MODULES = {
    "ip": "modules.ip_intel",
    "dns": "modules.dns_intel",
    "http": "modules.http_intel",
    "username": "modules.username",
    "email": "modules.email_intel",
    "github": "modules.github_intel",
    "domain": "modules.domain_intel",
    "phone": "modules.phone_intel",
    "meta": "modules.meta_intel",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def list_modules() -> None:
    print("[*] modules\n")
    for name, path in MODULES.items():
        try:
            mod = importlib.import_module(path)
            desc = getattr(mod, "DESCRIPTION", "")
        except Exception as e:
            desc = f"load error: {e}"
        print(f"  {name:12}  {desc}")
    print()


def run_module(name: str, argv: list[str]) -> None:
    if name not in MODULES:
        print(f"[!] unknown module: {name}")
        print(f"[*] available: {', '.join(MODULES)}")
        sys.exit(1)
    mod = importlib.import_module(MODULES[name])
    if not hasattr(mod, "run"):
        print(f"[!] {name} has no run()")
        sys.exit(1)
    mod.run(argv)


def main() -> None:
    p = argparse.ArgumentParser(
        prog="osintkit",
        description="OSINTKit — modular OSINT toolkit (D3F4UL7T)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  osintkit list
  osintkit ip 8.8.8.8
  osintkit dns example.com
  osintkit http https://example.com
  osintkit username johndoe
  osintkit email test@example.com
  osintkit github torvalds
  osintkit domain example.com
  osintkit phone +14155552671
  osintkit meta ./photo.jpg
        """,
    )
    p.add_argument("module", nargs="?", help="module name or 'list'")
    p.add_argument("args", nargs=argparse.REMAINDER)
    ns = p.parse_args()

    print(BANNER)
    print(f"[*] OSINTKit {VERSION}  {utc_now()}\n")

    if not ns.module or ns.module in ("-h", "--help"):
        p.print_help()
        print()
        list_modules()
        return
    if ns.module == "list":
        list_modules()
        return
    run_module(ns.module, ns.args)


if __name__ == "__main__":
    main()
