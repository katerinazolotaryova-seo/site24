"""Рахунок-фактура за Додатком 1 до Договору №201126/1 (kyivlogisticsschool.com).

    python3 contracts/orders/2026-11-20_kyivlogisticsschool.com_invoice.py

Базовий шаблон рахунку — templates/invoice.xlsx (рахунок mybox.ua); реквізити Виконавця вже в ньому.
Сума, реквізити Замовника і номер — з 2026-11-20_kyivlogisticsschool.com.py.
"""
import datetime as dt
import importlib.util
import sys
from pathlib import Path

import openpyxl

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
from build import ONES_F, fmt_amount, plural, triple, words_uk  # noqa: E402

spec = importlib.util.spec_from_file_location("contract", HERE / "2026-11-20_kyivlogisticsschool.com.py")
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)  # заодно перезбирає договір — рахунок завжди відповідає його поточній версії

INVOICE_NO = contract.NUMBER
OUT = ROOT / "output" / f"Рахунок_kyivlogisticsschool.com_{INVOICE_NO.replace('/', '-')}.xlsx"


def uah_words(n):
    """Сума в гривнях прописом: гривня жіночого роду — «дві», «одна»."""
    words = words_uk(n - n % 1000) if n >= 1000 else ""
    tail = " ".join(triple(n % 1000, ONES_F))
    text = " ".join(w for w in (words, tail) if w)
    return f"{text} {plural(n, 'гривня', 'гривні', 'гривень')} 00 копiйок"


def build():
    # оплата 50/50 (фінальна редакція договору): цей рахунок — попередня оплата 50%
    uah = round(contract.STAGE["usd"] * contract.RATE) // 2
    wb = openpyxl.load_workbook(ROOT / "templates" / "invoice.xlsx", rich_text=True)  # жирне ім'я в D1 — rich text
    ws = wb.active

    ws["A11"] = f"РАХУНОК-ФАКТУРА №{INVOICE_NO}"
    ws["B13"] = "ТОВ «Київська Логістична Школа», код ЄДРПОУ 40809862"
    ws["B14"] = "р/р UA763510050000026002878973645 в АТ «УКРСИББАНК», МФО 351005"
    ws["B18"] = ("Консультування з питань інформатизації: SEO оптимізація сайту "
                 f"{contract.SITE} (Додаток 1 до Договору №{contract.NUMBER} "
                 f"від {contract.DATE:%d.%m.%Y}), попередня оплата 50%")
    ws["C18"] = "послуга"
    ws["E18"] = fmt_amount(uah)  # як у шаблоні: текстом з пробілом («17 117»); F18/F19/D21 посилаються на E18
    ws["E21"] = f"грн ({uah_words(uah)})"
    ws["B26"] = dt.datetime.combine(contract.DATE, dt.time())

    wb.save(OUT)
    print(OUT, uah, uah_words(uah))


if __name__ == "__main__":
    build()
