"""Phone OSINT — E.164 parse, region, carrier hints via phonenumbers lib if present."""
from __future__ import annotations

DESCRIPTION = "Phone number parse, region, timezone, carrier (optional lib)"

import argparse
import re


def run(argv: list[str]) -> None:
    p = argparse.ArgumentParser(prog="osintkit phone", description=DESCRIPTION)
    p.add_argument("number", help="phone number, preferably E.164 (+...)")
    args = p.parse_args(argv)
    raw = args.number.strip()
    print(f"[*] phone  {raw}")

    try:
        import phonenumbers
        from phonenumbers import carrier, geocoder, timezone
    except ImportError:
        digits = re.sub(r"[^\d+]", "", raw)
        print("[*] pip install phonenumbers  for full parse")
        print(f"[+] cleaned  {digits}")
        print(f"[+] length   {len(digits.lstrip('+'))} digits")
        return

    try:
        num = phonenumbers.parse(raw, None if raw.startswith("+") else "US")
    except Exception as e:
        print(f"[!] parse error: {e}")
        return

    valid = phonenumbers.is_valid_number(num)
    possible = phonenumbers.is_possible_number(num)
    print(f"[+] valid     {valid}")
    print(f"[+] possible  {possible}")
    print(f"[+] E.164     {phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.E164)}")
    print(f"[+] national  {phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.NATIONAL)}")
    print(f"[+] type      {phonenumbers.number_type(num)}")
    print(f"[+] region    {geocoder.description_for_number(num, 'en') or '-'}")
    print(f"[+] carrier   {carrier.name_for_number(num, 'en') or '-'}")
    tzs = timezone.time_zones_for_number(num)
    print(f"[+] timezone  {', '.join(tzs) if tzs else '-'}")
