"""
Discord OSINT — snowflake decode, invite resolve, user lookup, widget, multi-source.

Public endpoints + optional bot token / third-party keys.
"""
from __future__ import annotations

DESCRIPTION = "Discord deep OSINT: snowflake, invite, user, guild widget, multi-source"

import argparse
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

UA = "OSINTKit/1.1 (+discord-osint; D3F4UL7T)"
DISCORD_EPOCH_MS = 1420070400000

SNOWFLAKE_RE = re.compile(r"^\d{17,20}$")
INVITE_RE = re.compile(
    r"(?:https?://)?(?:www\.)?(?:discord\.gg|discord(?:app)?\.com/invite)/([A-Za-z0-9-]+)",
    re.I,
)


def http_json(url: str, headers: dict | None = None, timeout: float = 15.0) -> tuple[int, dict | list | str]:
    h = {"User-Agent": UA, "Accept": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode("utf-8", errors="replace")
            try:
                return r.status, json.loads(raw)
            except json.JSONDecodeError:
                return r.status, raw
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, body[:500]
    except Exception as e:
        return 0, str(e)


def decode_snowflake(sf: str) -> dict:
    n = int(sf)
    ts_ms = (n >> 22) + DISCORD_EPOCH_MS
    dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
    return {
        "id": sf,
        "timestamp_ms": ts_ms,
        "created_utc": dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "created_iso": dt.isoformat(),
        "worker_id": (n & 0x3E0000) >> 17,
        "process_id": (n & 0x1F000) >> 12,
        "increment": n & 0xFFF,
    }


def resolve_invite(code: str) -> dict:
    # with counts for richer guild intel
    url = f"https://discord.com/api/v10/invites/{urllib.parse.quote(code)}?with_counts=true&with_expiration=true"
    status, data = http_json(url)
    return {"status": status, "data": data}


def guild_widget(guild_id: str) -> dict:
    url = f"https://discord.com/api/v10/guilds/{guild_id}/widget.json"
    status, data = http_json(url)
    return {"status": status, "data": data}


def discord_user_api(user_id: str, bot_token: str | None) -> dict:
    """Requires bot token that shares a mutual guild OR can fetch public profile fields."""
    if not bot_token:
        return {"status": 0, "data": "bot token not set (DISCORD_BOT_TOKEN)"}
    url = f"https://discord.com/api/v10/users/{user_id}"
    status, data = http_json(url, headers={"Authorization": f"Bot {bot_token}"})
    return {"status": status, "data": data}


def cord_lookup(discord_id: str, api_key: str | None) -> dict:
    url = f"https://api.cord.cat/api/v2/query/{discord_id}"
    headers = {}
    if api_key:
        headers["X-API-Key"] = api_key
    status, data = http_json(url, headers=headers)
    return {"status": status, "data": data}


def osintcat_lookup(query: str, api_key: str | None) -> dict:
    if not api_key:
        return {"status": 0, "data": "OSINTCAT_KEY required"}
    url = "https://www.osintcat.net/api/discord?" + urllib.parse.urlencode({"query": query})
    status, data = http_json(url, headers={"X-API-KEY": api_key})
    return {"status": status, "data": data}


def avatar_urls(user_id: str, avatar_hash: str | None = None) -> dict:
    out = {
        "default_index": str((int(user_id) >> 22) % 6),
        "default_png": f"https://cdn.discordapp.com/embed/avatars/{(int(user_id) >> 22) % 6}.png",
    }
    if avatar_hash:
        ext = "gif" if avatar_hash.startswith("a_") else "png"
        out["custom"] = f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.{ext}?size=1024"
    return out


def print_section(title: str) -> None:
    print(f"\n[+] {title}")
    print("-" * 50)


def dump(obj: object, limit: int = 4000) -> None:
    if isinstance(obj, (dict, list)):
        s = json.dumps(obj, indent=2, default=str)
    else:
        s = str(obj)
    if len(s) > limit:
        s = s[:limit] + "\n... [truncated]"
    print(s)


def run(argv: list[str]) -> None:
    p = argparse.ArgumentParser(
        prog="osintkit discord",
        description=DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  osintkit discord 803511102246789120
  osintkit discord discord.gg/discord-developers
  osintkit discord --invite abcdef
  osintkit discord 803511102246789120 --deep
        """,
    )
    p.add_argument("target", nargs="?", help="snowflake id, invite URL/code, or @username hint")
    p.add_argument("--invite", help="invite code or URL")
    p.add_argument("--guild", help="guild id for widget.json")
    p.add_argument("--deep", action="store_true", help="hit cord.cat + osintcat if keys present")
    p.add_argument("--bot-token", default=os.environ.get("DISCORD_BOT_TOKEN"), help="bot token for /users API")
    p.add_argument("--cord-key", default=os.environ.get("CORD_KEY"))
    p.add_argument("--osintcat-key", default=os.environ.get("OSINTCAT_KEY"))
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    target = (args.target or "").strip()
    invite = args.invite
    if target and not invite:
        m = INVITE_RE.search(target)
        if m:
            invite = m.group(1)
            target = ""
        elif re.fullmatch(r"[A-Za-z0-9-]{2,32}", target) and not SNOWFLAKE_RE.match(target):
            # bare invite code heuristic
            if "discord" not in target.lower():
                pass

    report: dict = {"tool": "osintkit-discord", "target": args.target}

    # --- invite path ---
    if invite:
        m = INVITE_RE.search(invite)
        code = m.group(1) if m else invite.strip().rstrip("/")
        print_section(f"invite  {code}")
        inv = resolve_invite(code)
        report["invite"] = inv
        if args.json:
            pass
        elif inv["status"] == 200 and isinstance(inv["data"], dict):
            d = inv["data"]
            g = d.get("guild") or {}
            print(f"  invite     {code}")
            print(f"  guild      {g.get('name')}  ({g.get('id')})")
            print(f"  desc       {(g.get('description') or '-')[:120]}")
            print(f"  members    {d.get('approximate_member_count')}")
            print(f"  online     {d.get('approximate_presence_count')}")
            print(f"  features   {', '.join((g.get('features') or [])[:12])}")
            print(f"  vanity     {g.get('vanity_url_code') or '-'}")
            print(f"  channel    {(d.get('channel') or {}).get('name')} ({(d.get('channel') or {}).get('id')})")
            print(f"  inviter    {(d.get('inviter') or {}).get('username')} ({(d.get('inviter') or {}).get('id')})")
            if g.get("id"):
                if SNOWFLAKE_RE.match(str(g["id"])):
                    print(f"  guild_created  {decode_snowflake(str(g['id']))['created_utc']}")
                print_section("guild widget")
                w = guild_widget(str(g["id"]))
                report["widget"] = w
                if w["status"] == 200 and isinstance(w["data"], dict):
                    print(f"  widget_enabled  yes")
                    print(f"  name            {w['data'].get('name')}")
                    print(f"  presence        {len(w['data'].get('members') or [])} listed samples")
                    for mem in (w["data"].get("members") or [])[:8]:
                        print(f"    - {mem.get('username')}  status={mem.get('status')}")
                else:
                    print(f"  widget  disabled/unavailable ({w['status']})")
        else:
            print(f"  failed  status={inv['status']}  {inv['data']!r}"[:200])

    # --- snowflake / user path ---
    sf = target if target and SNOWFLAKE_RE.match(target) else None
    if sf:
        print_section(f"snowflake  {sf}")
        meta = decode_snowflake(sf)
        report["snowflake"] = meta
        for k, v in meta.items():
            print(f"  {k:14} {v}")
        av = avatar_urls(sf)
        print(f"  default_avatar {av['default_png']}")

        print_section("discord API user")
        u = discord_user_api(sf, args.bot_token)
        report["discord_api_user"] = u
        if u["status"] == 200 and isinstance(u["data"], dict):
            d = u["data"]
            for k in ("id", "username", "global_name", "discriminator", "bot", "system", "flags", "public_flags"):
                if k in d:
                    print(f"  {k:14} {d.get(k)}")
            if d.get("avatar"):
                print(f"  avatar_url    {avatar_urls(sf, d['avatar']).get('custom')}")
            if d.get("banner"):
                print(f"  banner        {d.get('banner')}")
            if d.get("accent_color") is not None:
                print(f"  accent        #{d['accent_color']:06x}" if isinstance(d["accent_color"], int) else d["accent_color"])
        else:
            print(f"  status {u['status']}  — set DISCORD_BOT_TOKEN for profile fetch")
            print(f"  note: bot must share a mutual server with the user for full profile")

        if args.deep or args.cord_key or args.osintcat_key:
            print_section("cord.cat")
            c = cord_lookup(sf, args.cord_key)
            report["cord"] = c
            dump(c["data"] if c["status"] == 200 else c, limit=3500)

            print_section("osintcat")
            o = osintcat_lookup(sf, args.osintcat_key)
            report["osintcat"] = o
            dump(o["data"] if o["status"] == 200 else o, limit=3500)

    if not sf and not invite and target:
        print_section("query")
        print(f"  raw target: {target}")
        print("  tip: pass a numeric snowflake (17-20 digits) or invite URL/code")
        if args.deep or args.osintcat_key:
            print_section("osintcat (raw query)")
            o = osintcat_lookup(target, args.osintcat_key)
            report["osintcat"] = o
            dump(o["data"] if o["status"] == 200 else o, limit=3500)

    if args.guild:
        print_section(f"guild widget  {args.guild}")
        w = guild_widget(args.guild.strip())
        report["widget"] = w
        dump(w["data"] if w["status"] == 200 else w)

    if args.json:
        print(json.dumps(report, indent=2, default=str))

    print("\n[*] done")
