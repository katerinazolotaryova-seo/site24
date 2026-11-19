"""Рахунок / Invoice на 780 USD за Додатком 1 до Договору №191126/1 (crafttoryshop.com).

    python3 contracts/orders/2026-11-19_crafttoryshop.com_invoice.py

Реквізити Сторін — ті самі, що в двомовному договорі (2026-11-19_crafttoryshop.com_ua_en.py).
"""
import importlib.util
from pathlib import Path

import docx
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("contract", HERE / "2026-11-19_crafttoryshop.com_ua_en.py")
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)

OUT = contract.ROOT / "output" / "Рахунок_crafttoryshop.com_191126-1-1.docx"
INVOICE_NO = "191126/1-1"
DATE_UA, DATE_EN = "19.11.2026", "November 19, 2026"
DUE_UA, DUE_EN = "5 (п’ять) банківських днів", "5 (five) banking days"


def party(cell, title, lines):
    contract.write(cell, title, bold=True, first=True)
    for k, (ua, en) in enumerate(lines):
        contract.write(cell, ua if ua == en else f"{ua}\n{en}", bold=(k == 0), after=Pt(2))


def build():
    doc = docx.Document()
    sec = doc.sections[0]
    sec.page_height, sec.page_width = Cm(29.7), Cm(21)
    sec.left_margin = sec.right_margin = sec.top_margin = sec.bottom_margin = Cm(1.7)
    doc.styles["Normal"].font.name, doc.styles["Normal"].font.size = contract.FONT, contract.SIZE
    w = contract.write

    w(doc, f"Рахунок № {INVOICE_NO} / Invoice No. {INVOICE_NO}", bold=True,
      align=WD_ALIGN_PARAGRAPH.CENTER, size=Pt(14), first=True)
    w(doc, f"від {DATE_UA} / dated {DATE_EN}", align=WD_ALIGN_PARAGRAPH.CENTER)
    w(doc, "")

    t = doc.add_table(rows=1, cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    contract.no_borders(t)
    for c in t.rows[0].cells:
        c.width = Cm(8.7)
    party(t.rows[0].cells[0], "Виконавець / Contractor (Beneficiary)", contract.executor_lines())
    party(t.rows[0].cells[1], "Замовник / Customer (Payer)", contract.CUSTOMER)
    w(doc, "")

    items = doc.add_table(rows=3, cols=4)
    items.style = "Table Grid"
    items.alignment = WD_TABLE_ALIGNMENT.CENTER
    widths = (Cm(1.2), Cm(11.2), Cm(2), Cm(3.2))
    items.autofit = False
    for col, width in zip(items.columns, widths):  # ширина в сітці таблиці — її читає LibreOffice
        col.width = width
    rows = [
        ("№ / No.", "Найменування послуг / Description of services", "К-сть / Qty", "Сума, USD / Amount, USD"),
        ("1",
         f"SEO-послуги (план робіт на перший період) згідно з Додатком 1 до Договору №{contract.NUMBER} "
         f"від 19.11.2026, сайт {contract.SITE}\n"
         f"SEO services (work plan for the first period) under Appendix 1 to Agreement No. {contract.NUMBER} "
         f"dated November 19, 2026, website {contract.SITE}",
         "1", "780.00"),
        ("", "Разом до сплати / Total due", "", "780.00"),
    ]
    for r, values in zip(items.rows, rows):
        for k, (c, text) in enumerate(zip(r.cells, values)):
            c.width = widths[k]
            align = WD_ALIGN_PARAGRAPH.RIGHT if k == 3 else None
            w(c, text, bold=(r is items.rows[0] or r is items.rows[2]), align=align, first=True)
    w(doc, "")

    w(doc, "Сума до сплати: 780 (сімсот вісімдесят) доларів США 00 центів. Без ПДВ.\n"
           "Amount due: USD 780.00 (seven hundred eighty US dollars and 00 cents). VAT not applicable.",
      bold=True)
    w(doc, f"Строк оплати: {DUE_UA} з дати виставлення рахунку (п. 2 Додатку 1).\n"
           f"Payment term: {DUE_EN} from the invoice date (clause 2 of Appendix 1).")
    w(doc, "Банківські комісії: SHA — кожна Сторона сплачує комісії свого банку.\n"
           "Bank charges: SHA — each Party pays the charges of its own bank.")
    w(doc, f"Призначення платежу / Payment reference: Payment for SEO services, Invoice No. {INVOICE_NO}, "
           f"Agreement No. {contract.NUMBER} dated 19.11.2026")
    w(doc, "")
    w(doc, "")
    w(doc, "Виконавець / Contractor:  ____________________/Золотарьова К.В. / K. Zolotarova", bold=True)

    doc.save(OUT)
    print(OUT)


if __name__ == "__main__":
    build()
