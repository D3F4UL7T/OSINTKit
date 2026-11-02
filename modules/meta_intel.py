"""File metadata — images (EXIF) and basic file facts."""
from __future__ import annotations

DESCRIPTION = "File / image metadata (EXIF GPS, camera, timestamps)"

import argparse
import os
from datetime import datetime
from pathlib import Path


def run(argv: list[str]) -> None:
    p = argparse.ArgumentParser(prog="osintkit meta", description=DESCRIPTION)
    p.add_argument("path", help="file path")
    args = p.parse_args(argv)
    path = Path(args.path).expanduser()
    if not path.is_file():
        print(f"[!] not a file: {path}")
        return

    st = path.stat()
    print(f"[*] file  {path}")
    print(f"[+] size      {st.st_size} bytes")
    print(f"[+] modified  {datetime.fromtimestamp(st.st_mtime).isoformat()}")
    print(f"[+] created   {datetime.fromtimestamp(st.st_ctime).isoformat()}")

    try:
        from PIL import Image
        from PIL.ExifTags import TAGS, GPSTAGS
    except ImportError:
        print("[*] pip install pillow  for EXIF")
        return

    try:
        img = Image.open(path)
    except Exception as e:
        print(f"[!] not an image or unreadable: {e}")
        return

    print(f"[+] format    {img.format}")
    print(f"[+] size      {img.size}")
    print(f"[+] mode      {img.mode}")

    exif = img._getexif() if hasattr(img, "_getexif") else None
    if not exif:
        # Pillow 10+
        try:
            exif = img.getexif()
        except Exception:
            exif = None
    if not exif:
        print("[+] exif      none")
        return

    print("\n[+] EXIF")
    gps_raw = {}
    for tag_id, value in dict(exif).items():
        tag = TAGS.get(tag_id, tag_id)
        if tag == "GPSInfo":
            gps_raw = value
            continue
        if isinstance(value, bytes):
            continue
        print(f"  {tag}: {value}")

    if gps_raw:
        gps = {}
        for k, v in dict(gps_raw).items():
            gps[GPSTAGS.get(k, k)] = v
        print("\n[+] GPS")
        for k, v in gps.items():
            print(f"  {k}: {v}")

        def _to_deg(ref, values):
            try:
                d = float(values[0])
                m = float(values[1])
                s = float(values[2])
                dec = d + m / 60.0 + s / 3600.0
                if ref in ("S", "W"):
                    dec = -dec
                return dec
            except Exception:
                return None

        lat = _to_deg(gps.get("GPSLatitudeRef"), gps.get("GPSLatitude"))
        lon = _to_deg(gps.get("GPSLongitudeRef"), gps.get("GPSLongitude"))
        if lat is not None and lon is not None:
            print(f"  decimal: {lat}, {lon}")
            print(f"  maps: https://maps.google.com/?q={lat},{lon}")
