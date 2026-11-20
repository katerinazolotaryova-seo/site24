"""Рахунок на оплату за Додатком 1 до Договору №201126/1 (kyivlogisticsschool.com).

    python3 contracts/orders/2026-11-20_kyivlogisticsschool.com_invoice.py

Сума, реквізити Замовника і номер — з 2026-11-20_kyivlogisticsschool.com.py;
реквізити Виконавця — з entities/zolotaryova.yaml.
"""
import importlib.util
import sys
from pathlib import Path

import docx
import yaml
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
from build import ONES_F, fmt_amount, plural, triple, words_uk  # noqa: E402

spec = importlib.util.spec_from_file_location("contract", HERE / "2026-11-20_kyivlogisticsschool.com.py")
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)  # заодно перезбирає договір — рахунок завжди відповідає його поточній версії

INVOICE_NO = contract.NUMBER
OUT = ROOT / "output" / f"Рахунок_kyivlogisticsschool.com_{INVOICE_NO.replace('/', '-')}.docx"
FONT, SIZE = "Times New Roman", Pt(11)


def uah_words(n):
    """Сума в гривнях прописом: гривня жіночого роду — «дві», «одна»."""
    words = words_uk(n - n % 1000) if n >= 1000 else ""
    tail = " ".join(triple(n % 1000, ONES_F))
    text = " ".join(w for w in (words, tail) if w)
    return f"{text} {plural(n, 'гривня', 'гривні', 'гривень')} 00 копійок".capitalize()


def write(target, text, bold=False, align=None, first=False, size=SIZE, after=Pt(2)):
    p = target.paragraphs[0] if first and target.paragraphs else target.add_paragraph()
    p.paragraph_format.space_after = after
    if align is not None:
        p.alignment = align
    run = p.add_run(text)
    run.bold, run.font.size, run.font.name = bold, size, FONT
    return p


def build():
    ent = yaml.safe_load((ROOT / "entities" / "zolotaryova.yaml").read_text(encoding="utf-8"))
    uah = round(contract.STAGE["usd"] * contract.RATE)
    date = contract.DATE

    doc = docx.Document()
    sec = doc.sections[0]
    sec.page_height, sec.page_width = Cm(29.7), Cm(21)
    sec.left_margin = sec.right_margin = sec.top_margin = sec.bottom_margin = Cm(2)
    doc.styles["Normal"].font.name, doc.styles["Normal"].font.size = FONT, SIZE

    write(doc, f"Рахунок на оплату № {INVOICE_NO} від {date:%d.%m.%Y}", bold=True,
          align=WD_ALIGN_PARAGRAPH.CENTER, first=True, size=Pt(14), after=Pt(10))

    parties = doc.add_table(rows=2, cols=2)
    parties.style = "Table Grid"
    parties.autofit = False
    executor = [line for line in ent["requisites"] if not line.startswith("Вчасно")]
    rows = (("Постачальник:", executor + ["Платник єдиного податку, без ПДВ"]),
            ("Покупець:", [line for line in contract.CLIENT_LINES if not line.startswith("Директор")]))
    for col, width in zip(parties.columns, (Cm(3.6), Cm(13.4))):  # ширина в сітці — її читає LibreOffice
        col.width = width
    for row, (title, lines) in zip(parties.rows, rows):
        row.cells[0].width, row.cells[1].width = Cm(3.6), Cm(13.4)
        write(row.cells[0], title, bold=True, first=True)
        for k, line in enumerate(lines):
            write(row.cells[1], line, bold=(k == 0), first=(k == 0), after=Pt(0))
    write(doc, f"Договір: №{contract.NUMBER} від {date:%d.%m.%Y}, Додаток 1", after=Pt(8))

    items = doc.add_table(rows=3, cols=6)
    items.style = "Table Grid"
    items.alignment = WD_TABLE_ALIGNMENT.CENTER
    items.autofit = False
    widths = (Cm(0.8), Cm(8.2), Cm(1.9), Cm(1.3), Cm(2.4), Cm(2.4))
    for col, width in zip(items.columns, widths):
        col.width = width
    amount = f"{fmt_amount(uah)},00"
    data = [
        ("№", "Найменування послуг", "Од.", "К-сть", "Ціна, грн", "Сума, грн"),
        ("1", f"Послуги з інформатизації веб-проекту (SEO) згідно з Додатком 1 до Договору "
              f"№{contract.NUMBER} від {date:%d.%m.%Y}, сайт {contract.SITE}",
         "послуга", "1", amount, amount),
        ("", "Всього:", "", "", "", amount),
    ]
    for i, (r, values) in enumerate(zip(items.rows, data)):
        for k, (c, text) in enumerate(zip(r.cells, values)):
            c.width = widths[k]
            align = WD_ALIGN_PARAGRAPH.RIGHT if k >= 3 and i > 0 else None
            write(c, text, bold=(i != 1), align=align, first=True)

    write(doc, "")
    write(doc, f"Всього на суму: {uah_words(uah)}", bold=True)
    write(doc, "Без ПДВ.")
    write(doc, "Оплата протягом 5 (п’яти) банківських днів з дати виставлення рахунку (п. 2 Додатку 1).")
    write(doc, f"Призначення платежу: Оплата за послуги згідно з рахунком № {INVOICE_NO} від "
               f"{date:%d.%m.%Y}, без ПДВ", after=Pt(24))
    write(doc, "Виписав(ла): ____________________ /Золотарьова К.В./", bold=True)

    doc.save(OUT)
    print(OUT, f"{uah} грн — {uah_words(uah)}")


if __name__ == "__main__":
    build()
