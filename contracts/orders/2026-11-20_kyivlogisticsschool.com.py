"""Договір SEO (Блок 1 КП — переїзд сайту) для kyivlogisticsschool.com на ФОП Золотарьову.

    python3 contracts/orders/2026-11-20_kyivlogisticsschool.com.py

Основа — templates/seo.docx; Виконавець — entities/zolotaryova.yaml.
Реквізити Замовника — з договору PPC №210725/1 від 21.07.2025.
"""
import copy
import datetime as dt
import sys
from pathlib import Path

import docx
import yaml
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.text.paragraph import Paragraph

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from build import find_par, fmt_amount, set_date_runs  # noqa: E402

DATE = dt.date(2026, 11, 20)
NUMBER = f"{DATE:%d%m%y}/1"
SITE = "kyivlogisticsschool.com"
RATE = 45.45455  # комерційний курс продажу USD ПриватБанку, 20.11.2026

CLIENT_PREAMBLE = ("Товариство з обмеженою відповідальністю «Київська Логістична Школа» "
                   "(код ЄДРПОУ 40809862), в особі директора Москаленко Марини Сергіївни, "
                   "що діє на підставі Статуту")
CLIENT_LINES = [
    "ТОВ «Київська Логістична Школа»",
    "Код ЄДРПОУ: 40809862",
    "Номер запису в ЄДР: 1 070 102 0000 064853",
    "Юридична адреса: 01103, м. Київ, вул. Кіквідзе, б. 18а, кв. 16",
    "Рахунок: UA763510050000026002878973645",
    "в АТ «УКРСИББАНК», МФО 351005",
    "Директор: Москаленко Марина Сергіївна",
]
CLIENT_SIG = "Москаленко М.С."

STAGE = {
    "usd": 620,
    "term": "до 4 (чотирьох) тижнів з моменту внесення передоплати",
    "term_note": (" Технічний SEO-аудит готового сайту та повторна перевірка (пп. 11–12 плану) "
                  "виконуються після реалізації нового сайту розробниками Замовника."),
    "plan": [
        "Аналіз поточного пошукового трафіку в Google Analytics та Google Search Console: за якими запитами знаходять школу (брендові та небрендові) і на які сторінки переходять з пошуку. Формування переліку сторінок, що отримують трафік, - до того, як буде прийнято рішення, що залишати, а що прибирати",
        "Збір семантичного ядра українською та російською мовами на послугу «Курси логістики». Перевірка попиту і видачі за вузькими напрямками (наприклад, англійська для логістів, управління складом), щоб визначити, для яких напрямків потрібні окремі посадкові сторінки",
        "Збір англомовної семантики для коректної оптимізації",
        "Проектування структури нового сайту: зіставлення курсів, які школа реально пропонує, пошукового попиту та сторінок поточного сайту з трафіком. Перелік сторінок, які переносимо, які створюємо і які прибираємо",
        "Формування ТЗ на структуру посадкових сторінок (сторінка курсу, напрямку, події) - які SEO-елементи там мають бути",
        "Формування ТЗ на тексти для посадкових сторінок - до 4 текстів (на основі семантики та аналізу конкурентів)",
        "Написання мета-тегів для сторінок нового сайту по зібраній семантиці та шаблонних мета-тегів для типових сторінок",
        "Написання ТЗ на архітектуру української, англійської та російської мовних версій (на поточному сайті російська версія відображається некоректно)",
        "Формування технічного ТЗ для розробників з SEO-вимогами до нового сайту, зокрема правила для повторюваних курсів і подій: при новому наборі на той самий курс оновлюються дата та інформація на тій самій сторінці, без нової URL під кожну дату",
        "Складання карти редиректів: що відбувається з кожною старою адресою, яку не переносять або в якої змінюється URL",
        "Технічний SEO-аудит готового сайту після реалізації розробниками. Формування ТЗ на виправлення",
        "Повторна перевірка, що виправлення впроваджено",
    ],
}

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def set_text(p, text):
    runs = [r for r in p.runs if r.text.strip()] or p.runs
    for r in p.runs:
        if r._r is not runs[0]._r:
            r._r.getparent().remove(r._r)
    runs[0].text = text


def set_executor(doc, ent):
    pre = find_par(doc, "«Виконавець»")
    pre.runs[0].text = "___________________"
    pre.runs[1].text = pre.runs[1].text.replace("«3амовник»", "«Замовник»")
    pre.runs[2].text = ent["name"]
    pre.runs[3].text = " ".join(ent["preamble_tail"].split())
    for table in doc.tables:
        row = next(r for r in table.rows if r.cells[0].text.strip().startswith("ФОП"))
        pars = row.cells[0].paragraphs
        sig = next(k for k, p in enumerate(pars) if p.text.startswith("____"))
        lines = ent["requisites"]
        assert len(lines) <= sig
        # рядки 1..N — у форматі звичайного рядка (pars[2]), рядок 0 — жирна назва
        for k in range(1, len(lines)):
            if k != 2:
                pars[k]._p.addprevious(copy.deepcopy(pars[2]._p))
                pars[k]._p.getparent().remove(pars[k]._p)
        pars = row.cells[0].paragraphs
        for k in range(sig):
            text = lines[k] if k < len(lines) else ""
            if pars[k].runs:
                set_text(pars[k], text)
            elif text:
                pars[k].add_run(text)
        pars[sig].runs[-1].text = ent["signature"]
        for p in pars:
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT  # без розтягування «ФОП   Золотарьова»
        # Замовник невідомий: порожні рядки до рівня підпису Виконавця і лінія підпису.
        # Зайві порожні абзаци шаблону подовжують таблицю і дають порожню сторінку.
        cpars = row.cells[1].paragraphs
        csig = next(k for k, p in enumerate(cpars) if p.text.strip().startswith("____"))
        cpars[csig].runs[0].text = "____________________/"
        for p in cpars[csig + 1:]:
            p._p.getparent().remove(p._p)
        for p in cpars[:csig]:
            if not p.text.strip():
                set_text(p, "") if p.runs else None
        sig += 2  # у Виконавця два рядки переносяться — підпис Замовника на тому ж рівні
        while len(row.cells[1].paragraphs) - 1 > sig:
            row.cells[1].paragraphs[0]._p.getparent().remove(row.cells[1].paragraphs[0]._p)
        while len(row.cells[1].paragraphs) - 1 < sig:
            row.cells[1].paragraphs[0]._p.addprevious(copy.deepcopy(row.cells[1].paragraphs[0]._p))
        for r in table.rows:  # зайвий «___» під першою таблицею реквізитів
            if r.cells[1].text.strip() == "___":
                for p in r.cells[1].paragraphs:
                    for run in p.runs:
                        run.text = ""


def fill_dodatok(doc, elements, n, stage):
    pars = [Paragraph(e, doc._body) for e in elements if e.tag == W + "p"]
    by_start = lambda s: next(p for p in pars if p.text.strip().startswith(s))  # noqa: E731

    title = by_start("Додаток")
    next(r for r in title.runs if r.text.strip()).text = f"Додаток {n}"
    # розрив сторінки — властивістю абзацу, а не символом: символ давав порожні сторінки
    for br in list(title._p.iter(W + "br")):
        br.getparent().remove(br)
    title.paragraph_format.page_break_before = True
    # порожні абзаци після таблиці реквізитів Додатку теж переносяться на нову сторінку
    tail = elements[-1]
    while tail.tag == W + "p" and not Paragraph(tail, doc._body).text.strip():
        tail.getparent().remove(tail)
        elements.remove(tail)
        tail = elements[-1]
    # порожні рядки таблиці під реквізитами та зайві порожні абзаци перед нею
    for tr in list(tail.findall(W + "tr")):
        if not "".join(t.text or "" for t in tr.iter(W + "t")).strip():
            tail.remove(tr)
    # таблиця реквізитів не розривається між сторінками: рядки цілі, шапка тримається з таблицею
    for tr in tail.findall(W + "tr"):
        tr_pr = tr.find(W + "trPr")
        if tr_pr is None:
            tr_pr = tr.makeelement(W + "trPr", {})
            tr.insert(0, tr_pr)
        if tr_pr.find(W + "cantSplit") is None:
            tr_pr.append(tr_pr.makeelement(W + "cantSplit", {}))
    for p in tail.iter(W + "p"):
        Paragraph(p, doc._body).paragraph_format.keep_with_next = True
    by_start("ЮРИДИЧНІ АДРЕСИ").paragraph_format.keep_with_next = True
    blanks = [e for e in elements[elements.index(by_start("Цей Додаток")._p) + 1:]
              if e.tag == W + "p" and not Paragraph(e, doc._body).text.strip()]
    for e in blanks[1:]:
        e.getparent().remove(e)
        elements.remove(e)
    app = by_start("до Договору")
    next(r for r in app.runs if "/" in r.text).text = NUMBER
    set_date_runs(app.runs, DATE)
    for r in app.runs:
        r.font.highlight_color = None

    head = by_start("І. План робіт")
    set_text(head, "І. План робіт на перший період")
    items, el = [], head._p.getnext()
    while el is not None and Paragraph(el, doc._body).text.strip():
        items.append(Paragraph(el, doc._body))
        el = el.getnext()
    while len(items) < len(stage["plan"]):
        new = copy.deepcopy(items[-1]._p)
        items[-1]._p.addnext(new)
        items.append(Paragraph(new, doc._body))
    for p in items[len(stage["plan"]):]:
        p._p.getparent().remove(p._p)
    for p, t in zip(items, stage["plan"]):
        set_text(p, t)

    uah = round(stage["usd"] * RATE)
    set_text(by_start("Вартість Послуг"),
             f"Вартість Послуг (робіт), що зазначені в цьому Додатку, складає "
             f"{fmt_amount(uah).replace(' ', chr(160))} грн, звіт за якими надається після "
             f"виконання Додатку {n} та/або за запитом Замовника.")
    if n > 1:
        set_text(by_start("Оплата послуг"),
                 "Оплата послуг Виконавця здійснюється у вигляді попередньої оплати у розмірі "
                 "100% грошових коштів перед початком робіт за цим Додатком на підставі "
                 "виставленого Виконавцем рахунку протягом 5 (п’яти) банківських днів з дати "
                 "виставлення рахунку")
    set_text(by_start("Термін надання"),
             "Термін надання послуг (виконання робіт), що зазначений в цьому Додатку, складає "
             f"{stage['term']} відповідно до п. 5.1. Договору." + stage.get("term_note", ""))


def fill_client(doc):
    pre = find_par(doc, "«Виконавець»")
    pre.runs[0].text = CLIENT_PREAMBLE
    for table in doc.tables:
        row = next(r for r in table.rows if r.cells[0].text.strip().startswith("ФОП"))
        epars, cpars = row.cells[0].paragraphs, row.cells[1].paragraphs
        for k, text in enumerate(CLIENT_LINES):
            src = epars[0] if k == 0 else epars[2]  # 0 — жирна назва, решта — звичайний рядок
            new = copy.deepcopy(src._p)
            cpars[k]._p.addprevious(new)
            cpars[k]._p.getparent().remove(cpars[k]._p)
            set_text(Paragraph(new, row.cells[1]), text)
            cpars = row.cells[1].paragraphs
        set_text(cpars[-1], "____________________/")
        cpars[-1].add_run(CLIENT_SIG).bold = True


doc = docx.Document(ROOT / "templates" / "seo.docx")
ent = yaml.safe_load((ROOT / "entities" / "zolotaryova.yaml").read_text(encoding="utf-8"))

find_par(doc, "Договір", start=True).runs[1].text = f" №{NUMBER}"
set_date_runs(find_par(doc, "м. Київ").runs, DATE)
site_par = find_par(doc, "бренду Замовника")
r = site_par.runs[0]
r.text = r.text[:r.text.index("бренду Замовника") + len("бренду Замовника")] + " " + SITE
set_executor(doc, ent)
fill_client(doc)

start = next(p for p in doc.paragraphs if p.text.strip() == "Додаток 1")._p
elements = []
el = start
while el is not None and el.tag != W + "sectPr":
    elements.append(el)
    el = el.getnext()
fill_dodatok(doc, elements, 1, STAGE)

out = ROOT / "output" / f"Договір_SEO_{SITE}_{DATE:%m-%Y}.docx"
doc.save(out)
print(out)
