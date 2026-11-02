"""Email OSINT — syntax, domain DNS, gravatar, breach-safe hints."""
from __future__ import annotations

DESCRIPTION = "Email validation, domain MX/SPF/DMARC, Gravatar"

import argparse
import hashlib
import re
import urllib.request

UA = "OSINTKit/1.0 (+research; D3F4UL7T)"
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")


def run(argv: list[str]) -> None:
    p = argparse.ArgumentParser(prog="osintkit email", description=DESCRIPTION)
    p.add_argument("email")
    args = p.parse_args(argv)
    email = args.email.strip().lower()
    print(f"[*] email  {email}")

    ok = bool(EMAIL_RE.match(email))
    print(f"[+] syntax   {'valid' if ok else 'invalid'}")
    if not ok:
        return
    local, domain = email.split("@", 1)
    print(f"[+] local    {local}")
    print(f"[+] domain   {domain}")

    # DNS via optional dnspython
    try:
        import dns.resolver
        res = dns.resolver.Resolver()
        res.lifetime = 6.0
        for rtype in ("MX", "TXT"):
            try:
                ans = res.resolve(domain, rtype)
                print(f"\n[+] {rtype}")
                for r in ans:
                    txt = r.to_text()
                    if rtype == "TXT":
                        low = txt.lower()
                        if "v=spf1" in low:
                            print(f"  SPF  {txt[:200]}")
                        elif "dmarc" in low or "v=dmarc" in low:
                            print(f"  DMARC candidate {txt[:200]}")
                        else:
                            print(f"  {txt[:200]}")
                    else:
                        print(f"  {txt}")
            except Exception as e:
                print(f"[!] {rtype}: {e}")
        try:
            ans = res.resolve(f"_dmarc.{domain}", "TXT")
            print("\n[+] DMARC (_dmarc)")
            for r in ans:
                print(f"  {r.to_text()[:240]}")
        except Exception:
            print("\n[+] DMARC (_dmarc)  -")
    except ImportError:
        print("[*] install dnspython for MX/SPF/DMARC")

    # Gravatar presence (hash)
    md5 = hashlib.md5(email.encode("utf-8")).hexdigest()
    grav = f"https://www.gravatar.com/avatar/{md5}?d=404"
    req = urllib.request.Request(grav, headers={"User-Agent": UA}, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            print(f"\n[+] gravatar  YES  ({resp.status})  https://www.gravatar.com/{md5}")
    except Exception:
        print("\n[+] gravatar  no public image")

    print("\n[*] note: breach lookup not embedded — use haveibeenpwned.com manually / API key")
