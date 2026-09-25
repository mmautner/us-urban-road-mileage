"""Parse FHWA Highway Statistics 2024, Table HM-71 into data/hm71_2024_all_areas.csv.

Every data row in the table is an urbanized-area name followed by 17 numbers:
    population (2020 Census urbanized area),
    miles by functional class (7 columns) and TOTAL miles,
    daily vehicle-miles traveled in thousands by class (7 columns) and TOTAL DVMT.
A dash means zero.

Usage:
    python scripts/parse_hm71.py                      # reads data/raw/hm71_2024.pdf
    python scripts/parse_hm71.py path/to/table.txt    # or a plain-text extraction

Checks performed:
    1. Every row's class columns sum to its TOTAL column (FHWA rounds, so +/- 2 is allowed).
    2. The sums over all parsed rows match the table's own TOTAL row, which proves no
       row was dropped or split during extraction.
"""
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NUM = re.compile(r"^(-|\d{1,3}(,\d{3})*)$")
CLASSES = ["interstate", "other_fwy_expwy", "other_principal_arterial", "minor_arterial",
           "major_collector", "minor_collector", "local"]
COLS = (["urbanized_area", "population_2020"]
        + [f"miles_{c}" for c in CLASSES] + ["miles_total"]
        + [f"dvmt_k_{c}" for c in CLASSES] + ["dvmt_k_total"])


def num(tok):
    return 0 if tok == "-" else int(tok.replace(",", ""))


def lines_from(path: Path):
    if path.suffix.lower() == ".pdf":
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                yield from (page.extract_text() or "").splitlines()
    else:
        yield from path.read_text().splitlines()


def parse(path: Path):
    rows, total = [], None
    for line in lines_from(path):
        tok = line.split()
        if len(tok) < 18 or not all(NUM.match(t) for t in tok[-17:]):
            continue
        name, vals = " ".join(tok[:-17]), [num(t) for t in tok[-17:]]
        if name == "TOTAL":
            total = vals
            continue
        rows.append([name] + vals)
    return rows, total


def check(rows, total):
    for r in rows:
        miles, dvmt = r[2:10], r[10:18]
        assert abs(sum(miles[:7]) - miles[7]) <= 2, f"{r[0]}: mile classes don't sum to total"
        assert abs(sum(dvmt[:7]) - dvmt[7]) <= 2, f"{r[0]}: DVMT classes don't sum to total"
    if total is None:
        print("note: no TOTAL row found (partial input); skipped completeness check")
        return
    sums = [sum(r[i] for r in rows) for i in range(1, 18)]
    assert sums[0] == total[0], f"population sum {sums[0]:,} != TOTAL {total[0]:,}: rows missing"
    for i, (s, t) in enumerate(zip(sums, total)):
        # per-row rounding accumulates across ~490 rows, so allow 0.05%
        assert abs(s - t) <= max(5, 0.0005 * t), f"column {COLS[i + 1]}: {s:,} vs TOTAL {t:,}"
    print(f"completeness check passed: {len(rows)} areas sum to the published TOTAL row")


if __name__ == "__main__":
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "raw" / "hm71_2024.pdf"
    rows, total = parse(src)
    assert rows, f"no data rows parsed from {src}"
    check(rows, total)
    out = ROOT / "data" / "hm71_2024_all_areas.csv"
    with open(out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(COLS)
        w.writerows(rows)
    print(f"wrote {out} ({len(rows)} rows)")
