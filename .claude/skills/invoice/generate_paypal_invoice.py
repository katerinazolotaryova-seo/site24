#!/usr/bin/env python3
"""Generate an English-language PayPal invoice (.docx), modeled after a real
example (INVOICE-SEO_coveredconnections.com_01_26.docx): plain text, a
single line-item table, USD.

Usage example:
    python3 generate_paypal_invoice.py \
        --site 3dexpert.com.ua \
        --price 530 \
        --date 2026-11-02 \
        --requisites zolotaryova \
        --out-dir .

If --service is omitted, it defaults to "SEO Consulting service for <site>".

Invoice number follows the example's own scheme: "<YYYY>-<DDMM>" (day then
month, not month then day) from --date.

Output filename follows: INVOICE-SEO_<site>_<MM>_<YY>.docx
"""
import argparse
import datetime
import json
import sys
from pathlib import Path

import docx

SKILL_DIR = Path(__file__).resolve().parent
REQUISITES_PATH = SKILL_DIR / "paypal_requisites.json"


def build_invoice(site, service, price, qty, invoice_date, invoice_no, req):
    subtotal = price * qty

    d = docx.Document()

    d.add_paragraph(f"INVOICE for the SEO {site}")
    d.add_paragraph(f"Date: {invoice_date.strftime('%d-%m-%Y')}")
    d.add_paragraph(f"Invoice number: {invoice_no}")
    d.add_paragraph("")

    d.add_paragraph(req["name"])
    d.add_paragraph(f"VAT: {req['vat']}")
    d.add_paragraph(f"Legal address: {req['address']}")
    d.add_paragraph(f"E-mail: {req['email']}")
    d.add_paragraph(f"Tel.: {req['phone']}")
    d.add_paragraph("")
    d.add_paragraph(f"PayPal: {req['paypal']}")

    for _ in range(4):
        d.add_paragraph("")

    table = d.add_table(rows=3, cols=4)
    table.style = "Table Grid"
    header = table.rows[0].cells
    header[0].text, header[1].text, header[2].text, header[3].text = (
        "Description", "Price, $", "Quantity", "Subtotal, $",
    )
    row = table.rows[1].cells
    row[0].text, row[1].text, row[2].text, row[3].text = (
        service, _fmt_num(price), _fmt_num(qty), _fmt_num(subtotal),
    )
    total_row = table.rows[2].cells
    total_row[0].text, total_row[1].text = "", ""
    total_row[2].text, total_row[3].text = "Total:", _fmt_num(subtotal)

    d.add_paragraph("")
    d.add_paragraph(req["name"])
    d.add_paragraph(f"{req['phone']} | {req['email']}")

    return d


def _fmt_num(n):
    return str(int(n)) if float(n) == int(n) else str(n)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--site", required=True, help="e.g. 3dexpert.com.ua")
    p.add_argument("--service", default=None,
                    help="Defaults to 'SEO Consulting service for <site>'")
    p.add_argument("--price", type=float, required=True, help="USD, per unit")
    p.add_argument("--qty", type=float, default=1)
    p.add_argument("--date", default=datetime.date.today().isoformat(),
                    help="YYYY-MM-DD, defaults to today")
    p.add_argument("--requisites", default="zolotaryova")
    p.add_argument("--out-dir", default=".")
    args = p.parse_args()

    if args.service is None:
        args.service = f"SEO Consulting service for {args.site}"

    invoice_date = datetime.date.fromisoformat(args.date)

    requisites = json.loads(REQUISITES_PATH.read_text())
    if args.requisites not in requisites:
        sys.exit(f"Unknown PayPal requisites profile '{args.requisites}'. "
                  f"Known: {', '.join(requisites)}")
    req = requisites[args.requisites]

    invoice_no = f"{invoice_date.year}-{invoice_date.day:02d}{invoice_date.month:02d}"

    doc = build_invoice(args.site, args.service, args.price, args.qty,
                         invoice_date, invoice_no, req)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = (f"INVOICE-SEO_{args.site}_"
                f"{invoice_date.month:02d}_{invoice_date.year % 100:02d}.docx")
    out_path = out_dir / filename
    doc.save(out_path)

    print(out_path)


if __name__ == "__main__":
    main()
