"""GitHub public profile / repo OSINT (API, optional token)."""
from __future__ import annotations

DESCRIPTION = "GitHub user profile, repos, orgs (public API)"

import argparse
import json
import os
import urllib.error
import urllib.request

UA = "OSINTKit/1.0 (+research; D3F4UL7T)"


def gh_get(path: str, token: str | None) -> dict | list:
    url = f"https://api.github.com{path}"
    headers = {
        "User-Agent": UA,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())


def run(argv: list[str]) -> None:
    p = argparse.ArgumentParser(prog="osintkit github", description=DESCRIPTION)
    p.add_argument("user", help="GitHub username")
    p.add_argument("--token", default=os.environ.get("GITHUB_TOKEN"), help="optional PAT for higher rate limit")
    p.add_argument("--repos", type=int, default=15, help="list top N repos by stars")
    args = p.parse_args(argv)
    user = args.user.strip().lstrip("@")
    print(f"[*] github  {user}")

    try:
        u = gh_get(f"/users/{user}", args.token)
    except urllib.error.HTTPError as e:
        print(f"[!] API {e.code}: {e.reason}")
        return
    except Exception as e:
        print(f"[!] {e}")
        return

    if not isinstance(u, dict):
        print("[!] unexpected response")
        return

    fields = [
        ("login", u.get("login")),
        ("name", u.get("name")),
        ("id", u.get("id")),
        ("company", u.get("company")),
        ("blog", u.get("blog")),
        ("location", u.get("location")),
        ("email", u.get("email")),
        ("bio", u.get("bio")),
        ("twitter", u.get("twitter_username")),
        ("public_repos", u.get("public_repos")),
        ("followers", u.get("followers")),
        ("following", u.get("following")),
        ("created", u.get("created_at")),
        ("updated", u.get("updated_at")),
        ("profile", u.get("html_url")),
    ]
    print("\n[+] profile")
    for k, v in fields:
        if v not in (None, ""):
            print(f"  {k:14} {v}")

    # orgs
    try:
        orgs = gh_get(f"/users/{user}/orgs", args.token)
        if isinstance(orgs, list) and orgs:
            print("\n[+] orgs")
            for o in orgs:
                print(f"  {o.get('login')}  {o.get('description') or ''}")
    except Exception:
        pass

    # repos
    try:
        repos = gh_get(f"/users/{user}/repos?per_page=100&sort=updated", args.token)
        if isinstance(repos, list) and repos:
            repos_sorted = sorted(repos, key=lambda r: r.get("stargazers_count") or 0, reverse=True)
            print(f"\n[+] top repos (by stars, showing {min(args.repos, len(repos_sorted))})")
            for r in repos_sorted[: args.repos]:
                print(
                    f"  ★{r.get('stargazers_count', 0):5}  "
                    f"{r.get('name')}  "
                    f"lang={r.get('language') or '-'}  "
                    f"{r.get('html_url')}"
                )
    except Exception as e:
        print(f"[!] repos: {e}")
