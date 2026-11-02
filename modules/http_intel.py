"""HTTP fingerprint — headers, tech hints, TLS subject."""
from __future__ import annotations

DESCRIPTION = "HTTP headers, status, redirects, basic tech fingerprint"

import argparse
import re
import ssl
import urllib.error
import urllib.request

UA = "OSINTKit/1.0 (+research; D3F4UL7T)"

TECH_SIGS = [
    (re.compile(r"cloudflare", re.I), "Cloudflare"),
    (re.compile(r"nginx", re.I), "nginx"),
    (re.compile(r"apache", re.I), "Apache"),
    (re.compile(r"Microsoft-IIS", re.I), "IIS"),
    (re.compile(r"x-powered-by:\s*php", re.I), "PHP"),
    (re.compile(r"x-powered-by:\s*express", re.I), "Express"),
    (re.compile(r"x-drupal", re.I), "Drupal"),
    (re.compile(r"x-generator:\s*wordpress", re.I), "WordPress"),
    (re.compile(r"wp-content", re.I), "WordPress"),
    (re.compile(r"shopify", re.I), "Shopify"),
    (re.compile(r"x-amz-request-id", re.I), "AWS"),
    (re.compile(r"cf-ray", re.I), "Cloudflare"),
]


def run(argv: list[str]) -> None:
    p = argparse.ArgumentParser(prog="osintkit http", description=DESCRIPTION)
    p.add_argument("url", help="URL (http/https)")
    p.add_argument("--timeout", type=float, default=12.0)
    args = p.parse_args(argv)
    url = args.url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    print(f"[*] url  {url}")
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={"User-Agent": UA}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=args.timeout, context=ctx) as resp:
            status = resp.status
            final = resp.geturl()
            headers = {k.lower(): v for k, v in resp.headers.items()}
            body = resp.read(65536).decode("utf-8", errors="ignore")
    except urllib.error.HTTPError as e:
        status = e.code
        final = e.geturl() if hasattr(e, "geturl") else url
        headers = {k.lower(): v for k, v in (e.headers.items() if e.headers else [])}
        body = e.read(65536).decode("utf-8", errors="ignore") if e.fp else ""
    except Exception as e:
        print(f"[!] request failed: {e}")
        return

    print(f"[+] status   {status}")
    print(f"[+] final    {final}")
    interesting = [
        "server", "x-powered-by", "x-generator", "via", "x-frame-options",
        "content-security-policy", "strict-transport-security", "set-cookie",
        "x-content-type-options", "content-type", "cf-ray", "x-amz-request-id",
    ]
    print("\n[+] headers")
    for k in interesting:
        if k in headers:
            val = headers[k]
            if len(val) > 120:
                val = val[:117] + "..."
            print(f"  {k}: {val}")
    for k, v in headers.items():
        if k not in interesting:
            continue

    blob = "\n".join(f"{k}: {v}" for k, v in headers.items()) + "\n" + body[:4000]
    techs = []
    for rx, name in TECH_SIGS:
        if rx.search(blob) and name not in techs:
            techs.append(name)
    print("\n[+] tech hints")
    print("  " + (", ".join(techs) if techs else "-"))

    title = re.search(r"<title[^>]*>(.*?)</title>", body, re.I | re.S)
    if title:
        print(f"\n[+] title  {re.sub(r'\\s+', ' ', title.group(1)).strip()[:120]}")
