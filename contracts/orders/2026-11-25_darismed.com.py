"""Договір PPC для darismed.com на ФОП Лубіну, 100% передоплата.

    python3 contracts/orders/2026-11-25_darismed.com.py

Основа — templates/ppc.docx (PPC-договір kyivlogisticsschool.com №210725/1, Виконавець Золотарьова);
Виконавець замінюється на Лубіну (реквізити — як у templates/seo_lubina.docx).
Реквізитів Замовника в КП немає — порожні рядки «___».
"""
import copy
import datetime as dt
import sys
from pathlib import Path

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm
from docx.text.paragraph import Paragraph

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from build import MONTHS, fmt_amount  # noqa: E402

DATE = dt.date(2026, 11, 25)
NUMBER = f"{DATE:%d%m%y}/1"
SITE = "darismed.com"
RATE = 45.66210  # комерційний курс продажу USD ПриватБанку, 25.11.2026
USD = 585        # 1-й місяць; далі 306 $ / міс — окремими Додатками

EXECUTOR = [  # ФОП Лубіна — як у templates/seo_lubina.docx
    "ФОП Лубіна Катерина Олександрівна",
    "Свідоцтво № 312667",
    "Від: «28» травня 2013 р.",
    "ІПН: 3123120343",
    "Р/р UA653052990000026004025047014 в АТ КБ «ПРИВАТБАНК»",
    "МФО: 305299",
]
EXECUTOR_SIG = "Лубіна К.О."
EXECUTOR_PREAMBLE = ("Фізична особа-підприємець Лубіна Катерина Олександрівна",
                     ", яка діє на підставі свідоцтва № 312667 від «28» травня 2013 р. та є платником "
                     "єдиного податку, з іншої сторони, іменований надалі «Виконавець», разом "
                     "«Сторони», а кожна окремо «Сторона», уклали даний Договір (далі – Договір)")

# (пункт, [підпункти]) — план 1-го місяця з КП
PLAN = [
    ("Отримання доступів до Google Ads, Merchant Center, GA4 (Google Analytics), Google Tag Manager (GTM)", []),
    ("Налаштування аналітики та відслідковування конверсій:", [
        "Перевірка налаштування цілей у Google Analytics, коригування при необхідності",
        "Перевірка зв'язки акаунтів Google Ads, Google Analytics і Google Merchant Center",
        "Налаштування передачі конверсійних дій з Analytics в Ads, коригування при необхідності",
        "Перевірка роботи електронної комерції (e-commerce)",
    ]),
    ("Вивчення асортименту та збір запитів:", [
        "Узгодження з Замовником списку з 15–20 пріоритетних препаратів для Daris Med",
        "Вивчення кожного препарату зі списку: призначення, особливості, як його шукають покупці",
        "Збір запитів за назвами всіх пріоритетних препаратів",
        "Збір запитів за призначенням препаратів і варіантами пошуку відповідного продукту",
        "Аналіз поточних сигналів аудиторій: для яких препаратів запити вже опрацьовані (Ozempic, Mounjaro, Ursofalk та інші), для яких їх потрібно доповнити",
    ]),
    ("Аналіз кампаній, товарного фіду та обмежень:", [
        "Аналіз продажів у розрізі препаратів: які продаються, які майже не продаються",
        "Визначення структури кампаній: окрема кампанія на препарати, що вже продаються, з тестуванням решти окремо, або групування препаратів за спільними характеристиками",
        "Оцінка доцільності окремого фіду для торгових кампаній (Shopping), щоб розділити роботу Shopping і Performance Max",
        "Перевірка історії обмежень і блокувань у Google Ads та Merchant Center",
    ]),
    ("Роботи з оптимізації Performance Max та торгових кампаній:", [
        "Формування сигналів аудиторій на основі зібраних запитів для препаратів, по яких їх бракує",
        "Тестування різних поєднань сигналів аудиторій, перевірка інтересів аудиторії як гіпотези",
        "Перевірка роботи Merchant Center, внесення змін за необхідністю",
        "Тестування та зміна стратегій призначення ставок (щотижня)",
        "Контроль балансу рекламного кабінету (щотижня)",
        "Контроль показників ROAS і продажів по кожному препарату з пріоритетного списку, щоб вчасно помічати просідання (щотижня)",
        "Регулярне сортування пошукових запитів. Формування списку мінус-слів з нецільових запитів, додавання цільових до існуючих кампаній (щотижня)",
    ]),
    ("Звітність, комунікація з акаунт-менеджером", []),
    ("Аналіз роботи облікового запису. Перевірка відсотка отриманих показів для кампаній. Перевірка відсотка виграних аукціонів. Аналіз конкурентів. Визначення точок зростання з урахуванням отриманих даних (раз на місяць)", []),
]

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


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


def fill_cell(cell, lines, sig, height, bold_first=True):
    """Рядки реквізитів у форматі першого/другого абзацу клітинки, далі порожні — і рядок підпису."""
    pars = cell.paragraphs
    sig_idx = next(k for k, p in enumerate(pars) if p.text.strip().startswith("____"))
    name_tpl, line_tpl = pars[0]._p, pars[1]._p
    for p in pars[:sig_idx]:
        p._p.getparent().remove(p._p)
    sig_p = cell.paragraphs[0]
    for k, text in enumerate(lines):
        new = copy.deepcopy(name_tpl if (k == 0 and bold_first) else line_tpl)
        sig_p._p.addprevious(new)
        np = Paragraph(new, cell)
        set_text(np, text)
        np.alignment = WD_ALIGN_PARAGRAPH.LEFT  # без розтягування «Код   ЄДРПОУ   /»
    for _ in range(2 + height - len(lines)):  # підписи обох Сторін на одному рівні
        new = copy.deepcopy(line_tpl)
        sig_p._p.addprevious(new)
        set_text(Paragraph(new, cell), "")
    set_text(sig_p, "")
    sig_p.runs[0].text = "____________________/"
    if sig:
        sig_p.add_run(sig).bold = True


def build():
    doc = docx.Document(ROOT / "templates" / "ppc.docx")

    set_text(par(doc, "ДОГОВІР №"), f"ДОГОВІР № {NUMBER}")
    runs = par(doc, "м. Київ").runs
    runs[1].text, runs[3].text = f"{DATE.day:02d}", MONTHS[DATE.month - 1] + " "
    runs[4].text, runs[5].text = str(DATE.year)[:3], str(DATE.year)[3:]

    pre = par(doc, "ТОВ “Київська Логістична Школа”").runs
    pre[0].text = "___________________"
    pre[1].text, pre[2].text = ", в особі ___________________", ""
    pre[3].text = pre[3].text.replace("«3амовник»", "«Замовник»").replace(", іменований", ", що діє на підставі ___________________, з однієї сторони, іменований", 1)
    pre[4].text, pre[5].text = EXECUTOR_PREAMBLE

    # Сайт у п. 1.2: «для сайтів» + гіперпосилання в наступному абзаці
    site_p = par(doc, "Виконавець надає для Замовника")
    site_p.runs[1].text = "у"
    link = site_p._p.getnext().find(W + "hyperlink")
    link.find(f"{W}r/{W}t").text = f"https://{SITE}/"
    doc.part.rels[link.get(R + "id")]._target = f"https://{SITE}/"

    # Реквізити Сторін в обох таблицях
    for table in doc.tables:
        row = next(r for r in table.rows if r.cells[0].text.strip().startswith("ФОП"))
        fill_cell(row.cells[0], EXECUTOR, EXECUTOR_SIG, len(EXECUTOR))
        fill_cell(row.cells[1], ["___________________", "Код ЄДРПОУ / РНОКПП: ___________________",
                                 "Адреса: ___________________", "Рахунок: ___________________",
                                 "Банк: ___________________"], "", len(EXECUTOR))
        for tr in table.rows:  # таблиця не розривається між сторінками і тримається із заголовком
            tr_pr = tr._tr.get_or_add_trPr()
            tr_pr.append(tr_pr.makeelement(W + "cantSplit", {}))
            for c in tr.cells:
                for cp in c.paragraphs:
                    cp.paragraph_format.keep_with_next = True
    for p in doc.paragraphs:
        if "АДРЕСИ ТА" in p.text:
            p.paragraph_format.keep_with_next = True

    # Додаток 1
    app = par(doc, "до Договору №")
    app.runs[0].text = f"до Договору №{NUMBER}  від «{DATE.day:02d}» {MONTHS[DATE.month - 1]} {DATE.year} р. "

    head = par(doc, "І. План надання послуг")
    items, el = [], head._p.getnext()
    while el is not None and Paragraph(el, head._parent).text.strip():
        items.append(Paragraph(el, head._parent))
        el = el.getnext()
    tpl = copy.deepcopy(items[0]._p)
    for p in items:
        p._p.getparent().remove(p._p)
    anchor = head._p
    for text, subs in PLAN:
        new = copy.deepcopy(tpl)
        anchor.addnext(new)
        anchor = new
        set_text(Paragraph(new, head._parent), text)
        for sub in subs:  # підпункти — без нумерації, з відступом
            new = copy.deepcopy(tpl)
            num = new.find(f"{W}pPr/{W}numPr")
            num.getparent().remove(num)
            anchor.addnext(new)
            anchor = new
            sp = Paragraph(new, head._parent)
            set_text(sp, f"– {sub}")
            sp.paragraph_format.left_indent = Cm(1.6)
            sp.paragraph_format.first_line_indent = Cm(-0.4)

    # у шаблоні посилання на п. 5.1, якого в PPC-договорі немає: порядок оплати — п. 4.3
    term = par(doc, "Термін надання послуг")
    set_text(term, term.text.replace("п. 5.1. Договору", "п. 4.3 Договору").strip())

    uah = round(USD * RATE)
    set_text(par(doc, "Вартість Послуг"),
             f"Вартість Послуг (робіт), що зазначені в цьому Додатку, складає "
             f"{fmt_amount(uah).replace(' ', chr(160))} грн. Звіт по виконаним роботам надається після "
             f"виконання Додатку 1 та/або за запитом Замовника. Рекламний бюджет не входить до вартості "
             f"Послуг: Замовник поповнює рекламний кабінет самостійно.")

    out = ROOT / "output" / f"Договір_PPC_{SITE}_{DATE:%m-%Y}.docx"
    doc.save(out)
    print(out, uah)
    return uah


if __name__ == "__main__":
    build()
