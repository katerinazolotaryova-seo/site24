"""Переводить фінальну редакцію договору kyivlogisticsschool.com (від клієнта) на поетапну оплату:
50% передоплата, 30% після завершення пп. 1–10 плану, 20% коли новий сайт готовий (перед аудитом).

    python3 contracts/negotiations/kyivlogisticsschool.com_50-50.py

Решта тексту — без змін, як у редакції клієнта.
"""
from pathlib import Path

import docx

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "negotiations" / "Договір_SEO_kyivlogisticsschool.com_11-2026_фінал_клієнта.docx"
OUT = ROOT / "output" / "Договір_SEO_kyivlogisticsschool.com_11-2026_50-30-20.docx"

TOTAL = 28182
PREPAY = round(TOTAL * 0.5)   # 50% — передоплата
STAGE2 = round(TOTAL * 0.3)   # 30% — після завершення пп. 1–10 плану
STAGE3 = TOTAL - PREPAY - STAGE2  # 20% — коли новий сайт готовий, перед аудитом (пп. 11–12)
NBSP = " "


def fmt(n):
    return f"{n:,}".replace(",", NBSP)


def set_text(p, text):
    runs = [r for r in p.runs if r.text.strip()] or p.runs
    for r in p.runs:
        if r._r is not runs[0]._r:
            r._r.getparent().remove(r._r)
    runs[0].text = text


def par(doc, start):
    hits = [p for p in doc.paragraphs if p.text.strip().startswith(start)]
    assert len(hits) == 1, (start, len(hits))
    return hits[0]


doc = docx.Document(SRC)

set_text(par(doc, "5.1.1."),
         "5.1.1. Ціна за послуги вказується у відповідному Додатку в залежності від плану та об'єму "
         "робіт. Оплата послуг Виконавця здійснюється частинами у порядку та в розмірах, визначених "
         "у відповідному Додатку; перший платіж є попередньою оплатою і здійснюється до початку "
         "надання послуг.")

set_text(par(doc, "Оплата послуг Виконавця"),
         f"Оплата послуг Виконавця здійснюється трьома платежами на підставі рахунків, виставлених "
         f"Виконавцем, кожен — протягом 5 (п’яти) банківських днів з дати виставлення рахунку: "
         f"1) попередня оплата у розмірі 50% — {fmt(PREPAY)} грн — після підписання Сторонами цього "
         f"Додатку; 2) 30% — {fmt(STAGE2)} грн — після завершення робіт за пп. 1–10 плану робіт і "
         f"підписання Сторонами Акту приймання-передачі наданих послуг за ними; 3) 20% — "
         f"{fmt(STAGE3)} грн — після повідомлення Замовником про готовність нової версії Сайту, "
         f"до початку робіт за пп. 11–12 плану робіт.")

doc.save(OUT)
print(OUT)
