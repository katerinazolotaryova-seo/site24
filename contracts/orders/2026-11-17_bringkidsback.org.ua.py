"""Договір SEO для bringkidsback.org.ua на ФОП Золотарьову: кожен етап КП — окремий Додаток.

    python3 contracts/orders/2026-11-17_bringkidsback.org.ua.py

Основа — templates/seo.docx; Виконавець замінюється на entities/zolotaryova.yaml.
Реквізити Замовника в КП відсутні — лишаються порожні рядки «___».
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

DATE = dt.date(2026, 11, 17)
NUMBER = f"{DATE:%d%m%y}/1"
SITE = "bringkidsback.org.ua"
RATE = 45.87156  # комерційний курс продажу USD ПриватБанку, 17.11.2026

STAGES = [
    {
        "title": "Етап 1. Технічний аудит сканування та індексації",
        "usd": 360,
        "term": "до 2 (двох) тижнів з моменту внесення передоплати",
        "plan": [
            "Повне сканування сайту з рендерингом JavaScript та за sitemap (1 726 сторінок, 6 мов)",
            "Аналіз Google Search Console: які сторінки проіндексовані і чому решта ні, статистика сканування, обрана Google основна версія сайту (www / без www), Core Web Vitals",
            "ТЗ програмісту: виведення посилань на новини, історії дітей і розділи меню в HTML-код сторінок (серверний рендеринг Next.js) - без зміни дизайну",
            "ТЗ на архів новин: пагінація, canonical сторінок архіву, sitemap",
            "ТЗ на виправлення: H1 на ключових сторінках, биті посилання на контактах, meta robots на сторінці 404, 301-редирект зі старого домену bringkidsback.com.ua (якщо домен належить Замовнику)",
            "ТЗ на структуровану розмітку: Organization, WebSite, NewsArticle, BreadcrumbList, FAQPage",
            "Перевірка мовних версій і hreflang",
        ],
    },
    {
        "title": "Етап 2. Оптимізація наявного контенту",
        "usd": 540,
        "term": "до 3 (трьох) тижнів з моменту внесення передоплати",
        "plan": [
            "Збір семантики для наявних ключових сторінок (головна, «Про нас», «Як долучитися», «Пояснювачі», «Документи і розслідування», «Міжнародна коаліція», «Партнери», «Амбасадори», історії дітей, новини) - до 15 груп, українська та англійська мови",
            "Написання мета-тегів (title, description) і H1 для ключових сторінок українською та англійською",
            "Шаблони мета-тегів для новин та історій дітей для всіх шести мов",
            "Адаптація мета-тегів ключових сторінок французької, іспанської, німецької та італійської версій під формулювання запитів цими мовами",
            "ТЗ на оптимізацію наявних текстів ключових сторінок - до 8 сторінок (структура підзаголовків, блоки «питання - відповідь» на основі вже наявних матеріалів, без написання нових розділів)",
            "ТЗ на внутрішнє перелінкування між новинами, історіями дітей, пояснювачами і документами",
            "Рекомендації щодо структури - лише там, де це потрібно для пошуку, з урахуванням процесу погодження контенту експертами Замовника",
        ],
    },
    {
        "title": "Етап 3. EEAT і видимість в AI-сервісах",
        "usd": 180,
        "term": "до 1 (одного) тижня з моменту внесення передоплати",
        "plan": [
            "Аналіз відповідей ChatGPT, Gemini, Perplexity і Google AI Overview за брендовими та тематичними запитами: чи згадується ініціатива, які джерела цитуються",
            "Аналіз EEAT-факторів наявних сторінок: джерела даних, дати оновлення, інформація про ініціативу, партнерів і авторів матеріалів",
            "ТЗ на доопрацювання наявного контенту для AI-сервісів і EEAT",
        ],
    },
    {
        "title": "Етап 4. Контроль впровадження та індексації",
        "usd": 130,
        "term": "до 4 (чотирьох) тижнів з моменту внесення передоплати",
        "term_note": " Роботи за цим Додатком починаються після впровадження Замовником правок за Додатком 1.",
        "plan": [
            "Перевірка впроваджених правок і повторне сканування сайту",
            "Контроль індексації в Google Search Console, надсилання оновленого sitemap",
            "Підсумковий звіт: зміни в індексації та видимості, рекомендації на наступний етап (за потреби)",
        ],
    },
]

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


def restart_numbering(doc, elements):
    """Копія Додатку отримує власні списки, щоб нумерація пунктів починалась з 1."""
    numbering = doc.part.numbering_part.element
    nums = {n.get(W + "numId"): n for n in numbering.findall(W + "num")}
    next_id = max(int(i) for i in nums) + 1
    mapping = {}
    for el in elements:
        for num_id in el.iter(W + "numId"):
            old = num_id.get(W + "val")
            if old not in nums:
                continue
            if old not in mapping:
                new = copy.deepcopy(nums[old])
                new.set(W + "numId", str(next_id))
                for o in new.findall(W + "lvlOverride"):
                    new.remove(o)
                over = new.makeelement(W + "lvlOverride", {W + "ilvl": "0"})
                over.append(new.makeelement(W + "startOverride", {W + "val": "1"}))
                new.append(over)
                numbering.append(new)
                mapping[old] = str(next_id)
                next_id += 1
            num_id.set(W + "val", mapping[old])


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
    set_text(head, f"І. План робіт. {stage['title']}")
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
    return uah


doc = docx.Document(ROOT / "templates" / "seo.docx")
ent = yaml.safe_load((ROOT / "entities" / "zolotaryova.yaml").read_text(encoding="utf-8"))

find_par(doc, "Договір", start=True).runs[1].text = f" №{NUMBER}"
set_date_runs(find_par(doc, "м. Київ").runs, DATE)
site_par = find_par(doc, "бренду Замовника")
r = site_par.runs[0]
r.text = r.text[:r.text.index("бренду Замовника") + len("бренду Замовника")] + " " + SITE
set_executor(doc, ent)

# Додаток 1 у шаблоні — від абзацу «Додаток 1» до кінця (без sectPr); копіюємо на кожен етап
body = doc.element.body
start = next(p for p in doc.paragraphs if p.text.strip() == "Додаток 1")._p
template = []
el = start
while el is not None and el.tag != W + "sectPr":
    template.append(el)
    el = el.getnext()
originals = [copy.deepcopy(e) for e in template]

total = 0
elements = template
for n, stage in enumerate(STAGES, 1):
    if n > 1:
        anchor = elements[-1]  # кінець попереднього Додатку (вже без порожніх абзаців)
        elements = [copy.deepcopy(e) for e in originals]
        for e in elements:
            anchor.addnext(e)
            anchor = e
        restart_numbering(doc, elements)
    total += fill_dodatok(doc, elements, n, stage)

out = ROOT / "output" / f"Договір_SEO_{SITE}_{DATE:%m-%Y}.docx"
doc.save(out)
print(out, f"разом {total} грн")
