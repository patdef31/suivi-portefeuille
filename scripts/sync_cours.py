import csv
import io
import os
import urllib.request

SHEET_CSV_URL = os.environ.get(
    "SHEET_CSV_URL",
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ5UquHBz76wt-ZKOSXFOvHcb7GBRdB1F96xi3ifHxfKll4G7x7fql30m1hDekhTw/pub?gid=464867013&single=true&output=csv",
)

def parse_number(val: str):
    if not val:
        return None
    cleaned = val.strip().replace("\u00a0", "").replace(" ", "").replace(",", ".")
    try:
        num = float(cleaned)
        return num if num == num and num > 0 else None
    except ValueError:
        return None

def main():
    req = urllib.request.Request(
        SHEET_CSV_URL,
        headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw_text = resp.read().decode("utf-8-sig")

    sample = raw_text[:1024]
    delimiter = ";" if sample.count(";") > sample.count(",") else ","
    reader = csv.DictReader(io.StringIO(raw_text), delimiter=delimiter)

    out_lines = ["ISIN;Ticker;Libelle;Cours"]
    valid_count = 0

    for row in reader:
        norm_row = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
        isin = norm_row.get("isin", "").upper()
        ticker = norm_row.get("ticker", "").upper()
        libelle = norm_row.get("libelle", "")
        cours_raw = norm_row.get("cours", "") or norm_row.get("dernier", "") or norm_row.get("vl", "")

        cours_val = parse_number(cours_raw)
        if not isin or cours_val is None:
            continue

        # Formate proprement sans zéros inutiles tout en gardant la précision
        cours_str = f"{cours_val:.4f}".rstrip("0").rstrip(".")
        out_lines.append(f"{isin};{ticker};{libelle};{cours_str}")
        valid_count += 1

    if valid_count == 0:
        raise RuntimeError("Aucun cours valide récupéré depuis Google Sheets : abandon pour éviter d'écraser cours.csv.")

    with open("cours.csv", "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out_lines) + "\n")

    print(f"OK : {valid_count} ligne(s) écrite(s) dans cours.csv")

if __name__ == "__main__":
    main()

