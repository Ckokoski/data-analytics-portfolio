"""
generate_demo_data.py — make two SYNTHETIC, deliberately MESSY demo CSVs.

WHY MESSY ON PURPOSE
--------------------
The whole point of the audit tool is to *catch* data-quality problems. To prove
it works, we need files that genuinely contain those problems. So this generator
builds two small, fake datasets and bakes specific, known issues into each:

  data/messy_customers.csv
      A customer list with MISSING VALUES and DUPLICATE ROWS / DUPLICATE IDs.

  data/messy_orders.csv
      An order list with BAD TYPES (text in a price column) and
      OUT-OF-RANGE values (negative quantities, an impossible discount,
      a price typed as the word "free").

EVERYTHING HERE IS FAKE
-----------------------
No real person, customer, or company. The names are obviously invented. The
random parts are seeded so re-running this produces the exact same files every
time (reproducible). See data/README.md for the full rundown.

RUN IT
------
    python generate_demo_data.py            # writes both CSVs into data/
"""

import csv             # the standard library's CSV writer — no pandas needed here
import random          # for the small amount of randomness, seeded for reproducibility
from pathlib import Path

# Seed the randomness so the output is identical on every run. The specific
# number doesn't matter; fixing it is what makes the demo reproducible.
random.seed(42)

# Where to write the files. We resolve paths relative to THIS script's folder so
# it works no matter what directory you run it from.
HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"


# A pool of obviously-fake names, so nobody mistakes this for real customer data.
FAKE_NAMES = [
    "Ada Sample", "Ben Testers", "Cora Mockton", "Dev Placeholder",
    "Edie Faux", "Finn Dummy", "Gail Stubbs", "Hank Example",
    "Ivy Synthetic", "Jules Fixture", "Kira Notreal", "Leo Demoman",
]

FAKE_CITIES = ["Springfield", "Faketown", "Mockville", "Testburg", "Sampleton"]


def write_csv(path: Path, header: list, rows: list) -> None:
    """
    Write a list of rows to a CSV file with the given header.

    Each row is itself a list of values lined up with the header. We write with
    newline="" as the csv module recommends, so there are no blank lines between
    rows on Windows.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        writer.writerows(rows)


def make_messy_customers() -> None:
    """
    Build data/messy_customers.csv.

    Problems intentionally baked in (this file is designed to earn a FAIL):
      * A NEARLY-EMPTY COLUMN — 'phone' is blank on most rows, the kind of
        half-populated field that crosses the audit's "serious" line. This is the
        main driver of the FAIL verdict.
      * DUPLICATE FULL ROWS — several records are copied verbatim (as if a file
        was accidentally appended to itself), enough to cross the duplicate-row
        "serious" line too.
      * MISSING VALUES — some 'email' and 'signup_date' cells are left blank, and
        a couple use the text "N/A" as a stand-in for blank (a classic real-world
        mess the audit treats as missing).
      * DUPLICATE KEYS — the same customer_id is reused for a different person,
        which the audit catches when run with `--key customer_id`.
    """
    header = ["customer_id", "name", "email", "phone", "city", "signup_date"]
    rows = []

    # 18 baseline customers, mostly clean — EXCEPT 'phone', which we leave blank
    # for almost everyone on purpose (a field someone added but never backfilled).
    for i in range(1, 19):
        cust_id = f"C{i:03d}"                         # C001, C002, ...
        name = FAKE_NAMES[i % len(FAKE_NAMES)]
        email = f"{name.split()[0].lower()}{i}@example.com"
        # Only the first three customers ever got a phone number recorded.
        phone = f"555-01{i:02d}" if i <= 3 else ""
        city = random.choice(FAKE_CITIES)
        # Spread signup dates across early 2024.
        signup = f"2024-{random.randint(1, 6):02d}-{random.randint(1, 28):02d}"
        rows.append([cust_id, name, email, phone, city, signup])

    # --- Now bake in the rest of the problems. ---

    # (a) Blank out some emails to create missing values.
    for idx in (2, 5, 9):
        rows[idx][2] = ""           # empty email cell

    # (b) Use "N/A" text as a fake-blank in signup_date (audit treats as missing).
    rows[7][5] = "N/A"
    rows[12][5] = "n/a"

    # (c) Blank a couple of cities too, so more than one column shows missingness.
    rows[3][4] = ""
    rows[15][4] = ""

    # (d) DUPLICATE FULL ROWS: copy several existing rows verbatim and append
    #     them. With ~20 base rows, four copies pushes the duplicate share over
    #     the 10% "serious" line so this shows up as a FAIL-level problem.
    rows.append(list(rows[0]))      # exact copy of the first customer
    rows.append(list(rows[4]))      # exact copy of the fifth customer
    rows.append(list(rows[8]))      # exact copy of the ninth customer
    rows.append(list(rows[8]))      # ...copied a second time (triple in total)

    # (e) DUPLICATE KEY: reuse an existing customer_id for a *different* person.
    #     The row isn't a full duplicate, but the ID collides — a subtle, common
    #     bug that silently breaks any join or per-customer rollup.
    rows.append(["C003", "Mara Conflict", "mara@example.com", "", "Faketown", "2024-07-01"])

    write_csv(DATA_DIR / "messy_customers.csv", header, rows)
    print(f"  wrote {DATA_DIR / 'messy_customers.csv'}  ({len(rows)} rows)")


def make_messy_orders() -> None:
    """
    Build data/messy_orders.csv.

    Problems intentionally baked in:
      * BAD TYPES — the 'price' column is mostly numbers but a few cells contain
        text ("free", "TBD"), and 'quantity' has a spelled-out "two". These break
        any sum or average until cleaned.
      * OUT-OF-RANGE VALUES — a negative quantity, a price of 0 that should be
        positive, a discount_pct above 100, and a wildly large price typo. These
        are caught when the audit is run with the matching --rules file.
      * A few currency-formatted prices ("$19.99", "1,250.00") to show the audit
        correctly recognises those as numbers, not errors.
    """
    header = ["order_id", "customer_id", "price", "quantity", "discount_pct"]
    rows = []

    # 22 baseline orders, mostly clean and well-formed.
    for i in range(1, 23):
        order_id = f"O{i:04d}"
        cust_id = f"C{random.randint(1, 18):03d}"
        price = round(random.uniform(5, 250), 2)
        quantity = random.randint(1, 6)
        discount = random.choice([0, 0, 0, 5, 10, 15, 20])  # mostly no discount
        rows.append([order_id, cust_id, price, quantity, discount])

    # --- Bake in the problems. ---

    # (a) BAD TYPES in the numeric 'price' column.
    rows[3][2] = "free"             # word instead of a number
    rows[10][2] = "TBD"             # placeholder text left in

    # (b) BAD TYPE in 'quantity' — a spelled-out number.
    rows[6][3] = "two"

    # (c) Currency formatting that SHOULD be accepted as numeric (not an error).
    rows[1][2] = "$19.99"
    rows[8][2] = "1,250.00"

    # (d) OUT-OF-RANGE values, to be caught by rules_example.json:
    rows[5][3] = -2                 # negative quantity (impossible)
    rows[12][2] = 0                 # a zero price where price must be > 0
    rows[14][4] = 150               # discount of 150% (over the 100 max)
    rows[18][2] = 999999.99         # absurd price typo (over a sane max)

    write_csv(DATA_DIR / "messy_orders.csv", header, rows)
    print(f"  wrote {DATA_DIR / 'messy_orders.csv'}  ({len(rows)} rows)")


def main():
    print("Generating SYNTHETIC messy demo data (seeded, reproducible)...")
    make_messy_customers()
    make_messy_orders()
    print("Done. These files are FAKE and exist only to exercise the audit tool.")


if __name__ == "__main__":
    main()
