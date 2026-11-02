"""Username presence across public platforms (passive HEAD/GET)."""
from __future__ import annotations

DESCRIPTION = "Username availability / presence across common platforms"

import argparse
import concurrent.futures
import urllib.error
import urllib.request

UA = "OSINTKit/1.0 (+research; D3F4UL7T)"

# format: name -> url template with {u}
SITES = {
    "GitHub": "https://github.com/{u}",
    "GitLab": "https://gitlab.com/{u}",
    "Twitter/X": "https://x.com/{u}",
    "Reddit": "https://www.reddit.com/user/{u}",
    "Instagram": "https://www.instagram.com/{u}/",
    "TikTok": "https://www.tiktok.com/@{u}",
    "YouTube": "https://www.youtube.com/@{u}",
    "HackerNews": "https://news.ycombinator.com/user?id={u}",
    "Keybase": "https://keybase.io/{u}",
    "Pinterest": "https://www.pinterest.com/{u}/",
    "Twitch": "https://www.twitch.tv/{u}",
    "Steam": "https://steamcommunity.com/id/{u}",
    "Linktree": "https://linktr.ee/{u}",
    "Medium": "https://medium.com/@{u}",
    "Dev.to": "https://dev.to/{u}",
    "Pastebin": "https://pastebin.com/u/{u}",
    "About.me": "https://about.me/{u}",
    "DockerHub": "https://hub.docker.com/u/{u}",
    "npm": "https://www.npmjs.com/~{u}",
    "PyPI": "https://pypi.org/user/{u}",
}


def probe(site: str, url: str, timeout: float) -> tuple[str, str, int | str]:
    req = urllib.request.Request(url, headers={"User-Agent": UA}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code = resp.status
            # some sites 200 even when missing — light body check
            body = resp.read(4096).decode("utf-8", errors="ignore").lower()
            if code == 200 and any(x in body for x in ("not found", "page doesn't exist", "couldn't find", "404")):
                return site, url, "miss?"
            return site, url, code
    except urllib.error.HTTPError as e:
        return site, url, e.code
    except Exception as e:
        return site, url, f"err:{type(e).__name__}"


def run(argv: list[str]) -> None:
    p = argparse.ArgumentParser(prog="osintkit username", description=DESCRIPTION)
    p.add_argument("username")
    p.add_argument("--timeout", type=float, default=8.0)
    p.add_argument("--threads", type=int, default=12)
    args = p.parse_args(argv)
    u = args.username.strip().lstrip("@")
    print(f"[*] username  {u}")
    print(f"[*] probing {len(SITES)} sites\n")

    jobs = [(name, tmpl.format(u=u)) for name, tmpl in SITES.items()]
    found = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as pool:
        futs = [pool.submit(probe, n, url, args.timeout) for n, url in jobs]
        for fut in concurrent.futures.as_completed(futs):
            site, url, code = fut.result()
            mark = "+" if code == 200 else "-"
            if code == 200:
                found.append((site, url))
            print(f"  [{mark}] {site:14} {code!s:8}  {url}")

    print(f"\n[*] likely present: {len(found)}/{len(SITES)}")
    for site, url in sorted(found):
        print(f"  {site:14} {url}")
