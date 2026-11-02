"""Додаток 2 до договору №260126/1 (3dexpert.com.ua, ФОП Лубіна) — з КП, план на 1-й місяць.

    python3 contracts/orders/2026-11-02_3dexpert.com.ua_dodatok2.py
"""
import copy
from pathlib import Path

import docx
from docx.text.paragraph import Paragraph

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "signed" / "Договір_SEO_3dexpert.com.ua_260126-1.docx"
OUT = ROOT / "output" / "Додаток_2_SEO_3dexpert.com.ua_11-2026.docx"

N, DATE = 2, "«02» листопада 2026 р."
PLAN = [
    "Збір семантичного ядра на пріоритетні напрямки - до 20 груп (продовження раніше зібраної семантики на інші послуги)",
    "Формування ТЗ на доопрацювання структури сайту - які сторінки послуг потрібно створити",
    "Аналіз структури сторінок послуг конкурентів. Формування ТЗ на додавання нових блоків (які блоки потрібні, їх вміст, приклади)",
    "Написання мета-тегів по зібраній семантиці",
    "Формування ТЗ на написання текстів для сторінок послуг - 10 текстів (на основі зібраної семантики та аналізу конкурентів)",
    "Технічний SEO аудит сайту. Формування ТЗ програмісту на впровадження",
    "Аналіз EEAT факторів (Experience, Expertise, Authoritativeness, Trustworthiness) конкурентів. Формування ТЗ на допрацювання EEAT.",
]
# 530 USD × 45,87156 (комерційний курс продажу ПриватБанку, 02.11.2026) = 24 311,93 → 24 312 грн
PRICE = ("Вартість Послуг (робіт), що зазначений в цьому Додатку складає 24 312 грн, "
         f"звіт за якими надається після виконання Додатку {N} та/або за запитом Замовника.")

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def set_text(p, text):
    runs = [r for r in p.runs if r.text.strip()] or p.runs
    for r in p.runs:
        if r._r is not runs[0]._r:
            r._r.getparent().remove(r._r)
    runs[0].text = text


doc = docx.Document(SRC)
body = doc.element.body

# Лишаємо тільки Додаток: все до абзацу «Додаток 1» видаляємо
start = next(p for p in doc.paragraphs if p.text.strip() == "Додаток 1")
for el in list(body):
    if el is start._p:
        break
    body.remove(el)
for br in list(start._p.iter(W + "br")):  # розрив сторінки перед додатком
    br.getparent().remove(br)
next(r for r in start.runs if r.text.strip()).text = f"Додаток {N} від {DATE}"

# План
head = next(p for p in doc.paragraphs if p.text.startswith("І. План робіт"))
set_text(head, "І. План робіт на наступний період")
items, el = [], head._p.getnext()
while el is not None and Paragraph(el, head._parent).text.strip():
    items.append(Paragraph(el, head._parent))
    el = el.getnext()
while len(items) < len(PLAN):
    new = copy.deepcopy(items[-1]._p)
    items[-1]._p.addnext(new)
    items.append(Paragraph(new, head._parent))
for p, t in zip(items, PLAN):
    set_text(p, t)

set_text(next(p for p in doc.paragraphs if p.text.startswith("Вартість Послуг")), PRICE)

# Порожні абзаци під підписом Замовника тягнуть таблицю на другу сторінку — прибираємо
row = next(r for t in doc.tables for r in t.rows if r.cells[1].text.strip().startswith("ФОП"))
pars = row.cells[1].paragraphs
sig = next(k for k, p in enumerate(pars) if p.text.startswith("____"))
for p in pars[sig + 1:]:
    if not p.text.strip():
        p._p.getparent().remove(p._p)

doc.save(OUT)
print(OUT)
