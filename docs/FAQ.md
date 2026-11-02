# OSINTKit FAQ

## What is OSINTKit?

A modular command-line toolkit for **passive open-source intelligence** — IP, DNS, HTTP, usernames, email, GitHub, domain RDAP, phone parse, and file/EXIF metadata.

## Is this malware / a scanner for hacking into systems?

No. Modules only query **public** data (DNS, RDAP, HTTP headers, public APIs, platform profile URLs). There is no exploit, brute-force login, or payload delivery code.

## Do I need API keys?

| module | key |
|--------|-----|
| ip, dns, http, username, domain, meta | none |
| github | optional `GITHUB_TOKEN` (higher rate limit) |
| email / phone | none (optional libs for richer parse) |

## Why does username show false positives?

Some sites always return HTTP 200 with a “not found” page. OSINTKit marks obvious miss strings when possible, but treat results as **leads**, not proof. Verify manually.

## DNS shows only A/AAAA records

Install `dnspython` for MX/NS/TXT/CNAME/SOA:

```bash
pip install dnspython
```

## Phone module is limited

```bash
pip install phonenumbers
```

## EXIF / GPS missing

```bash
pip install Pillow
```

Only works on images that still contain metadata (many social apps strip EXIF).

## Rate limits / blocks

- Use reasonable delays on `username` probes.
- Prefer a GitHub PAT for heavy `github` use.
- Public IP APIs may throttle; wait and retry.

## Can I use this on people without consent?

OSINT on public data is often legal, but **harassment, stalking, and unauthorized access** are not. You are responsible for your jurisdiction and target policy. Lab / authorized research only.

## How do I add a module?

1. Create `modules/your_module.py` with `DESCRIPTION` and `run(argv: list[str])`.
2. Register it in `MODULES` inside `osintkit.py`.
3. Keep it passive and dependency-light.

## Who built this?

**[D3F4UL7T](https://github.com/D3F4UL7T)**

```
root@D3F4ULT:~# whoami
D3F4UL7T
```
