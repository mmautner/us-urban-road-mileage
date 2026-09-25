"""Download FHWA Highway Statistics 2023, Table HM-71 to data/raw/ and print its SHA-256."""
import hashlib
import urllib.request
from pathlib import Path

URL = "https://www.fhwa.dot.gov/policyinformation/statistics/2023/pdf/hm71.pdf"
OUT = Path(__file__).resolve().parent.parent / "data" / "raw" / "hm71_2023.pdf"

OUT.parent.mkdir(parents=True, exist_ok=True)
req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 (road-per-person reproduction)"})
with urllib.request.urlopen(req, timeout=60) as r:
    data = r.read()
OUT.write_bytes(data)
print(f"saved {OUT} ({len(data):,} bytes)")
print(f"sha256 {hashlib.sha256(data).hexdigest()}")
