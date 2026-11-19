"""Договір SEO для crafttoryshop.com (Crafttory LLC, США) на ФОП Золотарьову.

    python3 contracts/orders/2026-11-19_crafttoryshop.com.py

Основа — templates/seo.docx; Виконавець — entities/zolotaryova.yaml.
Реквізити Замовника — з відкритих джерел (сайт, BBB, каталог PRINTING United);
EIN і банківські реквізити публічно недоступні — порожні рядки.
Оплата в USD без перерахунку в гривні: клієнт іноземний.
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
from build import find_par, set_date_runs, words_uk  # noqa: E402

DATE = dt.date(2026, 11, 19)
NUMBER = f"{DATE:%d%m%y}/1"
SITE = "crafttoryshop.com"

CLIENT_PREAMBLE = ("Компанія Crafttory LLC (товариство з обмеженою відповідальністю, зареєстроване "
                   "відповідно до законодавства штату Південна Кароліна, США), в особі власника "
                   "Пархоменка Віталія (Vitalii Parkhomenko), що діє на підставі установчих "
                   "документів компанії")
CLIENT_LINES = [
    "Crafttory LLC",
    "Limited Liability Company, South Carolina, USA",
    "Адреса: 2218 Magnolia Manor Ln, Ste 206, Fort Mill, SC 29708, USA",
    "EIN: ____________________",
    "Банк: ____________________",
    "Рахунок: ____________________",
    "Тел.: +1 (980) 202-4393",
    "E-mail: sales@crafttoryshop.com",
]
CLIENT_SIG = "Vitalii Parkhomenko"

STAGE = {
    "usd": 780,
    "term": "до 5 (п’яти) тижнів з моменту внесення передоплати",
    "plan": [
        "Збір семантичного ядра на пріоритетні категорії - до 60 груп, англійською, ринок США",
        "Формування ТЗ на допрацювання структури сайту - які сторінки потрібно додати на сайт",
        "Написання мета-тегів по зібраній семантиці",
        "Оптимізація шаблонних мета-тегів для сторінок товарів",
        "Формування ТЗ на функціонал фільтрації (сторінки за брендом, кольором, способом нанесення - лише там, де є пошуковий попит)",
        "Формування ТЗ на написання / оптимізацію текстів сторінок - 10 текстів (на основі зібраної семантики та аналізу конкурентів)",
        "Технічний SEO аудит сайту. Формування ТЗ на впровадження",
        "Аналіз видимості CraftTory і конкурентів в AI сервісах (ChatGPT, Perplexity, AI Overview). Аудит карток топ-товарів і товарних фідів Google і Microsoft Merchant Center",
        "Аналіз EEAT факторів (Experience, Expertise, Authoritativeness, Trustworthiness) конкурентів. Формування ТЗ на допрацювання EEAT (відгуки, кейси клієнтів, сторінка про компанію, процес нанесення)",
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

    set_text(by_start("Вартість Послуг"),
             f"Вартість Послуг (робіт), що зазначені в цьому Додатку, складає "
             f"{stage['usd']} ({words_uk(stage['usd'])}) доларів США, звіт за якими надається після "
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
