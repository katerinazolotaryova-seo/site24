"""Рахунок-фактура за Додатком 1 до Договору №251126/1 (darismed.com), постачальник — ФОП Лубіна.

    python3 contracts/orders/2026-11-25_darismed.com_invoice.py

Базовий шаблон — templates/invoice.xlsx (у ньому реквізити Золотарьової — замінюємо на Лубіну).
Адреси й телефону Лубіної в реквізитах немає — порожні рядки.
"""
import datetime as dt
import importlib.util
import sys
from pathlib import Path

import openpyxl
from openpyxl.cell.rich_text import CellRichText, TextBlock
from openpyxl.cell.text import InlineFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
from build import ONES_F, fmt_amount, plural, triple, words_uk  # noqa: E402

spec = importlib.util.spec_from_file_location("contract", HERE / "2026-11-25_darismed.com.py")
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)

INVOICE_NO = contract.NUMBER
OUT = ROOT / "output" / f"Рахунок_{contract.SITE}_{INVOICE_NO.replace('/', '-')}.xlsx"

SUPPLIER = {  # ФОП Лубіна — як у templates/seo_lubina.docx
    "D2": "UA653052990000026004025047014",
    "D3": "АТ КБ «ПРИВАТБАНК»",
    "D4": 305299,
    "D5": "3123120343",
    "D6": "____________________",
    "D7": "____________________",
}


def uah_words(n):
    """Сума в гривнях прописом: гривня жіночого роду — «дві», «одна»."""
    words = words_uk(n - n % 1000) if n >= 1000 else ""
    tail = " ".join(triple(n % 1000, ONES_F))
    text = " ".join(w for w in (words, tail) if w)
    return f"{text} {plural(n, 'гривня', 'гривні', 'гривень')} 00 копiйок"


def build():
    uah = round(contract.USD * contract.RATE)
    wb = openpyxl.load_workbook(ROOT / "templates" / "invoice.xlsx", rich_text=True)
    ws = wb.active

    # «ФОП » звичайним, ім'я жирним — як у шаблоні
    ws["D1"] = CellRichText(TextBlock(InlineFont(rFont="Times New Roman"), "ФОП "),
                            TextBlock(InlineFont(rFont="Arial", b=True, sz=10), "Лубіна Катерина Олександрівна"))
    for cell, value in SUPPLIER.items():
        ws[cell] = value

    ws["A11"] = f"РАХУНОК-ФАКТУРА №{INVOICE_NO}"
    ws["B13"] = "____________________"
    ws["B18"] = ("Консультування з питань інформатизації: налаштування та ведення контекстної реклами "
                 f"Google Ads для сайту {contract.SITE} (Додаток 1 до Договору №{contract.NUMBER} "
                 f"від {contract.DATE:%d.%m.%Y})")
    ws["C18"] = "місяць"
    ws["E18"] = fmt_amount(uah)  # як у шаблоні: текстом з пробілом; F18/F19/D21 посилаються на E18
    ws["E21"] = f"грн ({uah_words(uah)})"
    ws["C23"] = "Лубіна К.О.-"
    ws["B26"] = dt.datetime.combine(contract.DATE, dt.time())

    wb.save(OUT)
    print(OUT, uah, uah_words(uah))


if __name__ == "__main__":
    build()
