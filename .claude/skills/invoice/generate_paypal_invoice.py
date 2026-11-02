#!/usr/bin/env python3
"""Generate an English-language PayPal invoice (.docx) by filling in
template_paypal.docx — a real example invoice
(INVOICE-SEO_coveredconnections.com_01_26.docx), edited in place so the
output keeps its exact compact formatting (Arial 11, 1.15 line spacing, no
space-after-paragraph) instead of python-docx's much heavier blank-document
defaults.

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
from docx.opc.constants import RELATIONSHIP_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

SKILL_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = SKILL_DIR / "template_paypal.docx"
REQUISITES_PATH = SKILL_DIR / "paypal_requisites.json"

# Paragraph indices in template_paypal.docx (see SKILL.md if this ever needs
# re-deriving: inspect example paragraphs with python-docx, don't guess).
P_TITLE = 0
P_DATE = 1
P_INVOICE_NO = 2
P_NAME = 4
P_VAT = 5
P_ADDRESS = 6
P_EMAIL = 7
P_PHONE = 8
P_PAYPAL = 10
P_SIG_NAME = 15
P_SIG_CONTACT = 16


def _add_hyperlink(paragraph, text, url):
    part = paragraph.part
    r_id = part.relate_to(url, RELATIONSHIP_TYPE.HYPERLINK, is_external=True)
    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), r_id)
    run = OxmlElement("w:r")
    rpr = OxmlElement("w:rPr")
    color = OxmlElement("w:color")
    color.set(qn("w:val"), "1155CC")
    rpr.append(color)
    underline = OxmlElement("w:u")
    underline.set(qn("w:val"), "single")
    rpr.append(underline)
    run.append(rpr)
    t = OxmlElement("w:t")
    t.text = text
    run.append(t)
    hyperlink.append(run)
    paragraph._p.append(hyperlink)


def _clear_paragraph(paragraph):
    for child in list(paragraph._p):
        if child.tag in (qn("w:r"), qn("w:hyperlink")):
            paragraph._p.remove(child)


def _set_text(paragraph, text):
    _clear_paragraph(paragraph)
    paragraph.add_run(text)


def _fmt_num(n):
    return str(int(n)) if float(n) == int(n) else str(n)


def build_invoice(site, service, price, qty, invoice_date, invoice_no, req):
    subtotal = price * qty

    d = docx.Document(TEMPLATE_PATH)
    paras = d.paragraphs

    _clear_paragraph(paras[P_TITLE])
    paras[P_TITLE].add_run("INVOICE for the SEO ")
    _add_hyperlink(paras[P_TITLE], site, f"https://{site}")
    paras[P_TITLE].add_run(" ")

    _set_text(paras[P_DATE], f"Date: {invoice_date.strftime('%d-%m-%Y')}")
    _set_text(paras[P_INVOICE_NO], f"Invoice number: {invoice_no}")
    _set_text(paras[P_NAME], req["name"])
    _set_text(paras[P_VAT], f"VAT: {req['vat']}")
    _set_text(paras[P_ADDRESS], f"Legal address: {req['address']}")
    _set_text(paras[P_EMAIL], f"E-mail: {req['email']}")
    _set_text(paras[P_PHONE], f"Tel.: {req['phone']}")
    _set_text(paras[P_PAYPAL], f"PayPal: {req['paypal']}")
    _set_text(paras[P_SIG_NAME], req["name"])
    _set_text(paras[P_SIG_CONTACT], f"{req['phone']} | {req['email']}")

    table = d.tables[0]
    row = table.rows[1].cells
    row[0].text, row[1].text, row[2].text, row[3].text = (
        service, _fmt_num(price), _fmt_num(qty), _fmt_num(subtotal),
    )
    table.rows[2].cells[3].text = _fmt_num(subtotal)

    return d


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
