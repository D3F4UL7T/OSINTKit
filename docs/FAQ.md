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


## Discord module — how deep does it go?

```bash
# snowflake decode (created time, worker) — always offline-accurate
python3 osintkit.py discord 803511102246789120

# invite resolve + member counts + widget samples
python3 osintkit.py discord https://discord.gg/CODE

# optional bot token for /users/{id}
export DISCORD_BOT_TOKEN=...
python3 osintkit.py discord 803511102246789120

# third-party breach/intel aggregators (keys required for full data)
export CORD_KEY=...
export OSINTCAT_KEY=...
python3 osintkit.py discord 803511102246789120 --deep
```

Without keys you still get: snowflake creation time, invite/guild public metadata, widget presence samples, and CDN avatar URLs.
With a bot token: username, global name, avatar, flags (if the bot can resolve the user).
With cord/osintcat keys: aggregated breach / exposure records those services provide.


## CordCat (cord.cat) — how to go deep on Discord

CordCat is **first-class** in `osintkit discord`.

### How to get a CordCat API key

1. Open **[https://cord.cat](https://cord.cat)** in a browser.
2. Click **Sign up / Log in** and create a CordCat account  
   (this is *not* your Discord password — CordCat account only).
3. After login, open the **Dashboard**.
4. Find **API key** / **Developer** section.
5. **Create** or **Reveal** your key. It usually looks like `cc_...`.
6. Copy the key once — store it somewhere safe. Do **not** commit it to git.

#### Put the key in your shell

```bash
# current session only
export CORD_KEY=cc_paste_your_key_here

# optional: persist for your user shell
echo 'export CORD_KEY=cc_paste_your_key_here' >> ~/.bashrc
source ~/.bashrc
```

#### Or pass it per command

```bash
python3 osintkit.py discord 803511102246789120 --cord-key cc_paste_your_key_here
```

#### Or use a local secrets file (never commit)

```bash
echo 'CORD_KEY=cc_paste_your_key_here' > .env
# then: export $(grep -v '^#' .env | xargs)
```

### Plans / limits (CordCat)

CordCat enforces its own quotas (free / premium / contributor).  
If you get `401` → bad/missing key. `429` → rate limit — wait and retry.  
Details: [https://cord.cat/docs](https://cord.cat/docs)


### What CordCat endpoints we hit

| endpoint | purpose |
|----------|---------|
| `GET /api/v2/query/:id` | full profile, breach exposure, FiveM, EU DSA, risk/bot score |
| `GET /api/v2/lookup/:name` | search by username / display name |
| `GET /api/v2/guilds/:id` | user's server list (tier gated) |
| `GET /api/v2/server/:id` | server deep stats / history |
| `GET /api/v2/lookup/guild/:id` | guild member profile view |

### Commands

```bash
# full ID intel (needs CORD_KEY for breach/FiveM/DSA layers)
python3 osintkit.py discord 803511102246789120

# username search
python3 osintkit.py discord --name someuser

# user + guild list
python3 osintkit.py discord 803511102246789120 --guilds

# invite → guild, then CordCat server endpoints
python3 osintkit.py discord https://discord.gg/CODE --server-deep

# raw JSON from CordCat
python3 osintkit.py discord 803511102246789120 --raw

# full machine report
python3 osintkit.py discord 803511102246789120 --json
```

Without a key you still get accurate snowflake timestamps, invite metadata, and widget samples.  
With a key you unlock CordCat's aggregated OSINT (plan limits apply — free/premium/contributor).
