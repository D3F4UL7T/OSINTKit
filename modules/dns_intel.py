"""DNS intelligence — multi-record lookup."""
from __future__ import annotations

DESCRIPTION = "DNS A/AAAA/MX/NS/TXT/CNAME/SOA lookup"

import argparse
import socket

try:
    import dns.resolver  # type: ignore
    HAS_DNSPYTHON = True
except ImportError:
    HAS_DNSPYTHON = False


RECORD_TYPES = ("A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA")


def lookup_dnspython(name: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    resolver = dns.resolver.Resolver()
    resolver.lifetime = 8.0
    for rtype in RECORD_TYPES:
        try:
            answers = resolver.resolve(name, rtype)
            out[rtype] = sorted({r.to_text() for r in answers})
        except Exception:
            out[rtype] = []
    return out


def lookup_stdlib(name: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {t: [] for t in RECORD_TYPES}
    try:
        for info in socket.getaddrinfo(name, None):
            ip = info[4][0]
            if ":" in ip:
                out["AAAA"].append(ip)
            else:
                out["A"].append(ip)
        out["A"] = sorted(set(out["A"]))
        out["AAAA"] = sorted(set(out["AAAA"]))
    except Exception as e:
        out["A"] = [f"error: {e}"]
    return out


def run(argv: list[str]) -> None:
    p = argparse.ArgumentParser(prog="osintkit dns", description=DESCRIPTION)
    p.add_argument("name", help="hostname / domain")
    args = p.parse_args(argv)
    name = args.name.strip().rstrip(".")

    print(f"[*] dns  {name}")
    if HAS_DNSPYTHON:
        data = lookup_dnspython(name)
        print("[*] resolver  dnspython")
    else:
        data = lookup_stdlib(name)
        print("[*] resolver  stdlib (pip install dnspython for full records)")

    for rtype in RECORD_TYPES:
        vals = data.get(rtype) or []
        if not vals:
            continue
        print(f"\n[+] {rtype}")
        for v in vals:
            print(f"  {v}")
    if not any(data.values()):
        print("[!] no records")
