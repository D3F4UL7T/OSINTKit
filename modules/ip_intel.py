"""IP intelligence — geolocation, ASN, reverse DNS, reputation hints."""
from __future__ import annotations

DESCRIPTION = "IP geolocation, ASN, reverse DNS, public reputation"

import argparse
import json
import socket
import urllib.request

UA = "OSINTKit/1.0 (+research; D3F4UL7T)"


def fetch_json(url: str, timeout: float = 12.0) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", errors="replace"))


def reverse_dns(ip: str) -> str:
    try:
        host, _, _ = socket.gethostbyaddr(ip)
        return host
    except Exception:
        return "-"


def run(argv: list[str]) -> None:
    p = argparse.ArgumentParser(prog="osintkit ip", description=DESCRIPTION)
    p.add_argument("target", help="IPv4 or IPv6")
    p.add_argument("--json", action="store_true", help="raw JSON dump")
    args = p.parse_args(argv)
    ip = args.target.strip()

    print(f"[*] target  {ip}")
    print(f"[+] reverse DNS  {reverse_dns(ip)}")

    # ipapi.co — no key for light use
    try:
        data = fetch_json(f"https://ipapi.co/{ip}/json/")
        if args.json:
            print(json.dumps(data, indent=2))
            return
        if data.get("error"):
            print(f"[!] {data.get('reason') or data.get('error')}")
        else:
            fields = [
                ("ip", data.get("ip")),
                ("version", data.get("version")),
                ("city", data.get("city")),
                ("region", data.get("region")),
                ("country", f"{data.get('country_name')} ({data.get('country_code')})"),
                ("postal", data.get("postal")),
                ("lat/lon", f"{data.get('latitude')}, {data.get('longitude')}"),
                ("timezone", data.get("timezone")),
                ("org", data.get("org")),
                ("asn", data.get("asn")),
                ("currency", data.get("currency")),
            ]
            print("\n[+] geolocation / network")
            for k, v in fields:
                print(f"  {k:12} {v if v not in (None, '') else '-'}")
            maps = None
            if data.get("latitude") is not None and data.get("longitude") is not None:
                maps = f"https://maps.google.com/?q={data['latitude']},{data['longitude']}"
                print(f"  {'maps':12} {maps}")
    except Exception as e:
        print(f"[!] ipapi: {e}")

    # ip-api.com backup fields (http only on free)
    try:
        data2 = fetch_json(f"http://ip-api.com/json/{ip}?fields=status,message,proxy,hosting,mobile,query,isp,as,reverse")
        if data2.get("status") == "success":
            print("\n[+] hints (ip-api)")
            print(f"  {'isp':12} {data2.get('isp') or '-'}")
            print(f"  {'as':12} {data2.get('as') or '-'}")
            print(f"  {'proxy':12} {data2.get('proxy')}")
            print(f"  {'hosting':12} {data2.get('hosting')}")
            print(f"  {'mobile':12} {data2.get('mobile')}")
            if data2.get("reverse"):
                print(f"  {'rev':12} {data2.get('reverse')}")
    except Exception as e:
        print(f"[!] ip-api: {e}")
