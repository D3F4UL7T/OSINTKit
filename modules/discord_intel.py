"""
Discord OSINT — deep module with first-class CordCat (cord.cat) integration.

Endpoints used (CordCat API docs):
  GET /api/v2/query/:discord_id     full profile + breach exposure + FiveM + DSA + risk
  GET /api/v2/lookup/:name          search by username / display name
  GET /api/v2/guilds/:id            user server list (tier gated)
  GET /api/v2/server/:id            server deep stats
  GET /api/v2/lookup/guild/:id      guild member profile view

Plus public Discord APIs: invite resolve, widget, snowflake decode, optional bot token.
"""
from __future__ import annotations

DESCRIPTION = "Discord deep OSINT via CordCat + invite/widget/snowflake (cord.cat first-class)"

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

UA = "OSINTKit/1.2 (+cord.cat; D3F4UL7T)"
CORD_BASE = "https://api.cord.cat"
DISCORD_EPOCH_MS = 1420070400000

SNOWFLAKE_RE = re.compile(r"^\d{17,20}$")
INVITE_RE = re.compile(
    r"(?:https?://)?(?:www\.)?(?:discord\.gg|discord(?:app)?\.com/invite)/([A-Za-z0-9-]+)",
    re.I,
)


# ── http ────────────────────────────────────────────────────────────────

def http_json(
    url: str,
    headers: dict | None = None,
    timeout: float = 20.0,
) -> tuple[int, object]:
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
            return e.code, body[:800]
    except Exception as e:
        return 0, {"error": str(e)}


def cord_headers(api_key: str | None) -> dict:
    if not api_key:
        return {}
    # CordCat accepts X-API-Key or Authorization: Bearer
    if api_key.lower().startswith("bearer "):
        return {"Authorization": api_key}
    return {"X-API-Key": api_key, "Authorization": f"Bearer {api_key}"}


# ── snowflake / avatar ──────────────────────────────────────────────────

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
        "default_avatar_index": (n >> 22) % 6,
        "default_avatar_url": f"https://cdn.discordapp.com/embed/avatars/{(n >> 22) % 6}.png",
    }


def avatar_url(user_id: str, avatar_hash: str | None) -> str | None:
    if not avatar_hash:
        return None
    ext = "gif" if str(avatar_hash).startswith("a_") else "png"
    return f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.{ext}?size=1024"


# ── CordCat API ─────────────────────────────────────────────────────────

def cord_query(discord_id: str, api_key: str | None) -> tuple[int, object]:
    """Full lookup: profile, breach exposure, FiveM, DSA, risk/bot score."""
    url = f"{CORD_BASE}/api/v2/query/{urllib.parse.quote(discord_id)}"
    return http_json(url, headers=cord_headers(api_key))


def cord_lookup_name(name: str, api_key: str | None) -> tuple[int, object]:
    """Search by username / display name."""
    url = f"{CORD_BASE}/api/v2/lookup/{urllib.parse.quote(name)}"
    return http_json(url, headers=cord_headers(api_key))


def cord_user_guilds(discord_id: str, api_key: str | None) -> tuple[int, object]:
    url = f"{CORD_BASE}/api/v2/guilds/{urllib.parse.quote(discord_id)}"
    return http_json(url, headers=cord_headers(api_key))


def cord_server(server_id: str, api_key: str | None) -> tuple[int, object]:
    url = f"{CORD_BASE}/api/v2/server/{urllib.parse.quote(server_id)}"
    return http_json(url, headers=cord_headers(api_key))


def cord_guild_lookup(guild_id: str, api_key: str | None) -> tuple[int, object]:
    url = f"{CORD_BASE}/api/v2/lookup/guild/{urllib.parse.quote(guild_id)}"
    return http_json(url, headers=cord_headers(api_key))


# ── public Discord ──────────────────────────────────────────────────────

def resolve_invite(code: str) -> tuple[int, object]:
    url = (
        f"https://discord.com/api/v10/invites/{urllib.parse.quote(code)}"
        f"?with_counts=true&with_expiration=true"
    )
    return http_json(url)


def guild_widget(guild_id: str) -> tuple[int, object]:
    return http_json(f"https://discord.com/api/v10/guilds/{guild_id}/widget.json")


def discord_bot_user(user_id: str, bot_token: str | None) -> tuple[int, object]:
    if not bot_token:
        return 0, {"error": "DISCORD_BOT_TOKEN not set"}
    return http_json(
        f"https://discord.com/api/v10/users/{user_id}",
        headers={"Authorization": f"Bot {bot_token}"},
    )


# ── pretty printers ─────────────────────────────────────────────────────

def section(title: str) -> None:
    print(f"\n[+] {title}")
    print("-" * 56)


def kv(key: str, val: object, width: int = 16) -> None:
    if val is None or val == "":
        return
    s = str(val)
    if len(s) > 200:
        s = s[:197] + "..."
    print(f"  {key:<{width}} {s}")


def dump_json(obj: object, limit: int = 5000) -> None:
    s = json.dumps(obj, indent=2, default=str)
    if len(s) > limit:
        s = s[:limit] + "\n  ... [truncated]"
    print(s)


def print_cord_query(data: object) -> None:
    if not isinstance(data, dict):
        dump_json(data)
        return

    # flexible field walk — CordCat schema may nest under profile / user / data
    user = data.get("user") or data.get("profile") or data.get("discord") or data
    if isinstance(user, dict):
        section("cord · profile")
        for k in (
            "id", "username", "global_name", "display_name", "discriminator",
            "bio", "pronouns", "locale", "nsfw_allowed", "bot", "system",
            "flags", "public_flags", "premium_type",
        ):
            kv(k, user.get(k))
        av = user.get("avatar") or data.get("avatar")
        uid = str(user.get("id") or data.get("id") or "")
        if av and uid:
            kv("avatar_url", avatar_url(uid, str(av)))
        if user.get("banner"):
            kv("banner", user.get("banner"))
        if data.get("created_at") or user.get("created_at"):
            kv("created_at", data.get("created_at") or user.get("created_at"))

    # risk / bot score
    for key in ("risk", "risk_score", "bot_score", "score", "trust"):
        if key in data:
            section("cord · risk")
            dump_json(data[key], limit=1500)
            break

    # exposure / breaches
    for key in ("exposure", "breaches", "datasets", "leaks", "breach_data"):
        if key in data and data[key]:
            section(f"cord · {key}")
            dump_json(data[key], limit=3000)
            break

    # FiveM
    for key in ("fivem", "fivem_records", "five_m"):
        if key in data and data[key]:
            section("cord · FiveM")
            dump_json(data[key], limit=2000)
            break

    # DSA sanctions
    for key in ("dsa", "sanctions", "dsa_sanctions", "eu_dsa"):
        if key in data and data[key]:
            section("cord · DSA / sanctions")
            dump_json(data[key], limit=2000)
            break

    # residual keys not printed
    known = {
        "user", "profile", "discord", "id", "username", "avatar", "banner",
        "risk", "risk_score", "bot_score", "score", "trust",
        "exposure", "breaches", "datasets", "leaks", "breach_data",
        "fivem", "fivem_records", "five_m", "dsa", "sanctions", "dsa_sanctions",
        "eu_dsa", "created_at", "global_name", "display_name",
    }
    extra = {k: v for k, v in data.items() if k not in known and v not in (None, "", [], {})}
    if extra:
        section("cord · other fields")
        dump_json(extra, limit=2500)


# ── main ────────────────────────────────────────────────────────────────

def run(argv: list[str]) -> None:
    p = argparse.ArgumentParser(
        prog="osintkit discord",
        description=DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
CordCat (https://cord.cat) is first-class. Get a key: cord.cat → Dashboard.

examples:
  export CORD_KEY=cc_...
  osintkit discord 803511102246789120
  osintkit discord 803511102246789120 --guilds --server-deep
  osintkit discord --name someuser
  osintkit discord https://discord.gg/discord-developers
  osintkit discord --guild 613425648685547541
        """,
    )
    p.add_argument("target", nargs="?", help="discord snowflake id or invite URL/code")
    p.add_argument("--name", help="username / display name search via CordCat lookup")
    p.add_argument("--invite", help="invite code or URL")
    p.add_argument("--guild", help="guild/server id (widget + cord server/guild endpoints)")
    p.add_argument("--guilds", action="store_true", help="CordCat: list user guilds for snowflake target")
    p.add_argument("--server-deep", action="store_true", help="CordCat: deep server stats when guild id known")
    p.add_argument("--cord-key", default=os.environ.get("CORD_KEY") or os.environ.get("CORDCAT_KEY"))
    p.add_argument("--bot-token", default=os.environ.get("DISCORD_BOT_TOKEN"))
    p.add_argument("--osintcat-key", default=os.environ.get("OSINTCAT_KEY"))
    p.add_argument("--no-cord", action="store_true", help="skip CordCat even if key present")
    p.add_argument("--raw", action="store_true", help="always dump raw JSON from CordCat")
    p.add_argument("--json", action="store_true", help="machine-readable full report")
    args = p.parse_args(argv)

    cord_key = None if args.no_cord else args.cord_key
    report: dict = {"tool": "osintkit-discord", "cord": bool(cord_key)}

    target = (args.target or "").strip()
    invite = args.invite
    if target and not invite:
        m = INVITE_RE.search(target)
        if m:
            invite = m.group(1)
            target = ""

    # ── name search via CordCat ─────────────────────────────────────────
    if args.name:
        section(f"cord · lookup name  {args.name}")
        if not cord_key:
            print("  need CORD_KEY for /api/v2/lookup/:name")
            print("  get one: https://cord.cat → Dashboard")
        else:
            st, data = cord_lookup_name(args.name, cord_key)
            report["cord_lookup"] = {"status": st, "data": data}
            print(f"  status  {st}")
            if st == 200:
                print_cord_query(data) if not args.raw else dump_json(data)
            else:
                dump_json(data, limit=1500)

    # ── invite ──────────────────────────────────────────────────────────
    guild_id_from_invite = None
    if invite:
        m = INVITE_RE.search(invite) if "discord" in invite else None
        code = m.group(1) if m else invite.strip().strip("/")
        section(f"invite  {code}")
        st, data = resolve_invite(code)
        report["invite"] = {"status": st, "data": data}
        if st == 200 and isinstance(data, dict):
            g = data.get("guild") or {}
            guild_id_from_invite = str(g.get("id") or "") or None
            kv("guild", f"{g.get('name')} ({g.get('id')})")
            kv("description", (g.get("description") or "")[:140])
            kv("members", data.get("approximate_member_count"))
            kv("online", data.get("approximate_presence_count"))
            kv("features", ", ".join((g.get("features") or [])[:14]))
            kv("vanity", g.get("vanity_url_code"))
            ch = data.get("channel") or {}
            kv("channel", f"{ch.get('name')} ({ch.get('id')})")
            inv = data.get("inviter") or {}
            if inv:
                kv("inviter", f"{inv.get('username')} ({inv.get('id')})")
            if guild_id_from_invite and SNOWFLAKE_RE.match(guild_id_from_invite):
                kv("guild_created", decode_snowflake(guild_id_from_invite)["created_utc"])
        else:
            print(f"  status {st}")
            dump_json(data, limit=800)

    # ── snowflake target ────────────────────────────────────────────────
    sf = target if target and SNOWFLAKE_RE.match(target) else None
    if sf:
        section(f"snowflake  {sf}")
        meta = decode_snowflake(sf)
        report["snowflake"] = meta
        for k, v in meta.items():
            kv(k, v)

        # CordCat FULL QUERY — main event
        section("cord.cat · full query")
        if not cord_key:
            print("  CORD_KEY not set — only public decode available")
            print("  export CORD_KEY=cc_...   # https://cord.cat dashboard")
            print("  CordCat returns: profile · breach exposure · FiveM · DSA · risk score")
        else:
            st, data = cord_query(sf, cord_key)
            report["cord_query"] = {"status": st, "data": data}
            print(f"  HTTP {st}")
            if st == 200:
                if args.raw or args.json:
                    dump_json(data, limit=12000)
                else:
                    print_cord_query(data)
            elif st == 401:
                print("  unauthorized — check CORD_KEY")
                dump_json(data, limit=500)
            elif st == 429:
                print("  rate limited — wait and retry")
            else:
                dump_json(data, limit=1000)

        # optional guild list for user
        if args.guilds:
            section("cord · user guilds")
            if not cord_key:
                print("  CORD_KEY required")
            else:
                st, data = cord_user_guilds(sf, cord_key)
                report["cord_guilds"] = {"status": st, "data": data}
                print(f"  HTTP {st}")
                dump_json(data, limit=4000)

        # Discord bot API supplement
        section("discord API · user")
        st, data = discord_bot_user(sf, args.bot_token)
        report["discord_api"] = {"status": st, "data": data}
        if st == 200 and isinstance(data, dict):
            for k in ("id", "username", "global_name", "discriminator", "bot", "flags", "public_flags"):
                kv(k, data.get(k))
            if data.get("avatar"):
                kv("avatar_url", avatar_url(sf, data["avatar"]))
        else:
            print(f"  status {st} — set DISCORD_BOT_TOKEN for live profile")

        # osintcat optional second source
        if args.osintcat_key:
            section("osintcat · discord")
            url = "https://www.osintcat.net/api/discord?" + urllib.parse.urlencode({"query": sf})
            st, data = http_json(url, headers={"X-API-KEY": args.osintcat_key})
            report["osintcat"] = {"status": st, "data": data}
            print(f"  HTTP {st}")
            dump_json(data, limit=3000)

    # ── guild focus ─────────────────────────────────────────────────────
    guild_id = (args.guild or guild_id_from_invite or "").strip() or None
    if guild_id:
        section(f"guild widget  {guild_id}")
        st, data = guild_widget(guild_id)
        report["widget"] = {"status": st, "data": data}
        if st == 200 and isinstance(data, dict):
            kv("name", data.get("name"))
            kv("presence_samples", len(data.get("members") or []))
            for mem in (data.get("members") or [])[:10]:
                print(f"    - {mem.get('username')}  [{mem.get('status')}]")
        else:
            print(f"  widget unavailable ({st})")

        if cord_key:
            section("cord · server")
            st, data = cord_server(guild_id, cord_key)
            report["cord_server"] = {"status": st, "data": data}
            print(f"  HTTP {st}")
            dump_json(data, limit=3000)

            section("cord · lookup guild")
            st, data = cord_guild_lookup(guild_id, cord_key)
            report["cord_guild_lookup"] = {"status": st, "data": data}
            print(f"  HTTP {st}")
            dump_json(data, limit=3000)
        elif args.server_deep:
            print("  --server-deep needs CORD_KEY")

    if not any([sf, invite, args.name, guild_id]):
        section("usage")
        print("  pass a snowflake, invite URL, --name, or --guild")
        print("  CordCat key: export CORD_KEY=cc_...  (https://cord.cat)")

    if args.json:
        print("\n===JSON===")
        print(json.dumps(report, indent=2, default=str)[:50000])

    print("\n[*] done")
