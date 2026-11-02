"""Domain OSINT — DNS + WHOIS-lite via RDAP."""
from __future__ import annotations

DESCRIPTION = "Domain DNS + RDAP/WHOIS registration data"

import argparse
import json
import urllib.request

UA = "OSINTKit/1.0 (+research; D3F4UL7T)"


def rdap_domain(domain: str) -> dict:
    url = f"https://rdap.org/domain/{domain}"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/rdap+json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())


def run(argv: list[str]) -> None:
    p = argparse.ArgumentParser(prog="osintkit domain", description=DESCRIPTION)
    p.add_argument("domain")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)
    domain = args.domain.strip().lower().rstrip(".")
    print(f"[*] domain  {domain}")

    # pull DNS quickly via sibling logic
    try:
        from modules.dns_intel import lookup_dnspython, lookup_stdlib, HAS_DNSPYTHON
        data = lookup_dnspython(domain) if HAS_DNSPYTHON else lookup_stdlib(domain)
        for rtype, vals in data.items():
            if vals:
                print(f"\n[+] DNS {rtype}")
                for v in vals:
                    print(f"  {v}")
    except Exception as e:
        print(f"[!] dns: {e}")

    print("\n[+] RDAP")
    try:
        rdap = rdap_domain(domain)
        if args.json:
            print(json.dumps(rdap, indent=2)[:8000])
            return
        print(f"  handle     {rdap.get('handle') or '-'}")
        print(f"  ldhName    {rdap.get('ldhName') or '-'}")
        if rdap.get("status"):
            print(f"  status     {', '.join(rdap['status'])}")
        for event in rdap.get("events") or []:
            print(f"  event      {event.get('eventAction')}: {event.get('eventDate')}")
        for ent in rdap.get("entities") or []:
            roles = ",".join(ent.get("roles") or [])
            vcard = ent.get("vcardArray")
            name = "-"
            if isinstance(vcard, list) and len(vcard) > 1:
                for item in vcard[1]:
                    if item and item[0] == "fn":
                        name = item[3]
            print(f"  entity     [{roles}] {name} ({ent.get('handle')})")
        for ns in rdap.get("nameservers") or []:
            print(f"  nserver    {ns.get('ldhName')}")
        for link in rdap.get("links") or []:
            if link.get("rel") == "self":
                print(f"  rdap       {link.get('href')}")
    except Exception as e:
        print(f"  error: {e}")
