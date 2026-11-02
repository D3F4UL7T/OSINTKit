# OSINTKit

Modular open-source intelligence toolkit.

**Developed by [D3F4UL7T](https://github.com/D3F4UL7T)**

Passive / public-data focused. No exploit modules.

## Modules

| module | function |
|--------|----------|
| `ip` | geolocation, ASN, reverse DNS, proxy/hosting hints |
| `dns` | A/AAAA/MX/NS/TXT/CNAME/SOA |
| `http` | headers, redirects, tech fingerprint |
| `username` | multi-platform presence check |
| `email` | syntax, MX/SPF/DMARC, Gravatar |
| `github` | profile, orgs, top repos (API) |
| `domain` | DNS + RDAP registration data |
| `phone` | parse, region, carrier, timezone |
| `meta` | image EXIF / GPS / file facts |
| `discord` | snowflake decode, invite intel, widget, user API, cord/osintcat |

## Install

```bash
git clone https://github.com/D3F4UL7T/OSINTKit.git
cd OSINTKit
pip install -r requirements.txt   # optional but recommended
python3 osintkit.py list
```

Python 3.10+. Core runs on stdlib; `dnspython`, `phonenumbers`, `Pillow` unlock full accuracy.

## Usage

```bash
python3 osintkit.py ip 1.1.1.1
python3 osintkit.py dns example.com
python3 osintkit.py http https://example.com
python3 osintkit.py username johndoe
python3 osintkit.py email alice@example.com
python3 osintkit.py github torvalds
python3 osintkit.py domain example.com
python3 osintkit.py phone +14155552671
python3 osintkit.py meta ./photo.jpg
python3 osintkit.py discord 803511102246789120
python3 osintkit.py discord https://discord.gg/discord-developers
python3 osintkit.py discord 803511102246789120 --deep
```

Optional: `export GITHUB_TOKEN=...` for higher GitHub API rate limits.

## Layout

```
OSINTKit/
├── osintkit.py
├── modules/
│   ├── ip_intel.py
│   ├── dns_intel.py
│   ├── http_intel.py
│   ├── username.py
│   ├── email_intel.py
│   ├── github_intel.py
│   ├── domain_intel.py
│   ├── phone_intel.py
│   └── meta_intel.py
├── requirements.txt
├── LICENSE
└── README.md
```

## FAQ

See [docs/FAQ.md](docs/FAQ.md).

## Notes

Lab and authorized research only. Respect platform ToS and local law. Author assumes no liability for misuse.

## Credits

**Developed by [D3F4UL7T](https://github.com/D3F4UL7T)**

```
root@D3F4ULT:~# whoami
D3F4UL7T
```
