"""Переводить фінальну редакцію договору kyivlogisticsschool.com (від клієнта) на оплату 50/50:
50% передоплата, 50% після завершення робіт за Додатком.

    python3 contracts/negotiations/kyivlogisticsschool.com_50-50.py

Решта тексту — без змін, як у редакції клієнта.
"""
from pathlib import Path

import docx

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "negotiations" / "Договір_SEO_kyivlogisticsschool.com_11-2026_фінал_клієнта.docx"
OUT = ROOT / "output" / "Договір_SEO_kyivlogisticsschool.com_11-2026_50-50.docx"

TOTAL = 28182
HALF = TOTAL // 2
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
         "робіт. Оплата послуг Виконавця здійснюється двома платежами: попередня оплата у розмірі 50% "
         "вартості послуг за відповідним Додатком — до початку надання послуг; остаточний розрахунок у "
         "розмірі 50% вартості послуг за відповідним Додатком — після завершення робіт за Додатком, на "
         "підставі підписаного Сторонами Акту приймання-передачі наданих послуг.")

set_text(par(doc, "Оплата послуг Виконавця"),
         f"Оплата послуг Виконавця здійснюється двома платежами на підставі рахунків, виставлених "
         f"Виконавцем: попередня оплата у розмірі 50% — {fmt(HALF)} грн — протягом 5 (п’яти) "
         f"банківських днів з дати підписання Сторонами цього Додатку та виставлення рахунку; "
         f"остаточний розрахунок у розмірі 50% — {fmt(TOTAL - HALF)} грн — протягом 5 (п’яти) "
         f"банківських днів з дати підписання Сторонами Акту приймання-передачі наданих послуг за "
         f"цим Додатком та виставлення рахунку.")

doc.save(OUT)
print(OUT)
