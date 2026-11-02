"""Договір SEO на ФОП Лубіну (шаблон templates/seo_lubina.docx) з файлу замовлення.

    python3 contracts/build_lubina.py contracts/orders/<файл>.yaml
"""
import copy
import datetime as dt
import sys
from pathlib import Path

import docx
import yaml

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from build import MONTHS, find_par, fmt_amount  # noqa: E402


def set_text(p, text):
    runs = [r for r in p.runs if r.text] or p.runs
    for r in p.runs:
        if r._r is not runs[0]._r:
            r._r.getparent().remove(r._r)
    runs[0].text = text


o = yaml.safe_load(Path(sys.argv[1]).read_text(encoding="utf-8"))
date = o.get("date") or dt.date.today()
if isinstance(date, str):
    date = dt.date.fromisoformat(date)
NUMBER = o.get("number") or f"{date:%d%m%y}/1"
DAY, MONTH, YEAR = f"{date.day:02d}", MONTHS[date.month - 1], str(date.year)
SITE, CLIENT, CLIENT_SIG = o["site"], o["client"]["name"], o["client"]["signature"]
CLIENT_LINES, PLAN = o["client"]["requisites"], o["plan"]
# рядок з «: » без лапок YAML читає як словник — ловимо це одразу
bad = [x for x in CLIENT_LINES + PLAN if not isinstance(x, str)]
if bad:
    raise SystemExit(f"Візьміть у лапки рядки з двокрапкою: {bad}")
uah = round(o["price"]["usd"] * o["price"]["rate"])
PRICE = ("Вартість Послуг (робіт), що зазначений в цьому Додатку складає "
         f"{fmt_amount(uah).replace(' ', '\u00a0')} грн, звіт за якими надається після виконання Додатку 1 "
         "та/або за запитом Замовника.")
doc = docx.Document(ROOT / "templates" / "seo_lubina.docx")

# Номер і дата
find_par(doc, "Договір №", start=True).runs[1].text = NUMBER
date_run = next(r for r in find_par(doc, "м. Київ").runs if "«" in r.text)
date_run.text = f"   «{DAY}» {MONTH} {YEAR} р."

# Преамбула
pre = find_par(doc, "«Виконавець»")
pre.runs[1].text = CLIENT
pre.runs[3].text = pre.runs[3].text.replace("«3амовник»", "«Замовник»")

# Сайт: гіперпосилання в п. 2.1 + п. 3.2.1
p21 = find_par(doc, "2.1.", start=True)
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
hl = p21._p.find(W + "hyperlink")
hl.find(f"{W}r/{W}t").text = SITE
doc.part.rels[hl.get(R + "id")]._target = f"http://{SITE}/"
p321 = find_par(doc, "3.2.1.", start=True)
p321.runs[0].text = p321.runs[0].text.rstrip() + " " + SITE + "."

# Строк дії
p112 = find_par(doc, "11.2.", start=True)
next(r for r in p112.runs if "31.12." in r.text).text = "до 31.12.2027"

# Додаток 1: номер, дата
app = find_par(doc, "до Договору №", start=True)
app.runs[1].text = NUMBER + " "
app.runs[3].text = DAY
app.runs[5].text = f" {MONTH} "
app.runs[6].text, app.runs[7].text = YEAR[:2], YEAR[2:]

# Додаток 1: план
head = find_par(doc, "І. План робіт", start=True)
items, el = [], head._p.getnext()
while el is not None:
    p = docx.text.paragraph.Paragraph(el, head._parent)
    if not p.text.strip():
        break
    items.append(p)
    el = el.getnext()
while len(items) < len(PLAN):
    new = copy.deepcopy(items[-1]._p)
    items[-1]._p.addnext(new)
    items.append(docx.text.paragraph.Paragraph(new, head._parent))
for p, t in zip(items, PLAN):
    set_text(p, t)

set_text(find_par(doc, "Вартість Послуг", start=True), PRICE)

# Реквізити Замовника в обох таблицях
for table in doc.tables:
    row = next(r for r in table.rows if r.cells[1].text.strip().startswith("ФОП"))
    pars = row.cells[1].paragraphs
    sig = next(k for k, p in enumerate(pars) if p.text.startswith("____"))
    assert len(CLIENT_LINES) < sig
    # зайві порожні рядки перед підписом опускають його нижче, ніж у Виконавця
    # Виконавець: кілька рядків реквізитів в одному абзаці, тому його підпис на 2 абзаци вище
    exec_sig = next(k for k, p in enumerate(row.cells[0].paragraphs) if p.text.startswith("____"))
    while sig > exec_sig + 2 and not pars[sig - 1].text.strip():
        pars[sig - 1]._p.getparent().remove(pars[sig - 1]._p)
        pars = row.cells[1].paragraphs
        sig -= 1
    for k in range(sig):
        p = pars[k]
        if 0 < k < len(CLIENT_LINES) and k != 1:  # формат звичайного рядка
            new = copy.deepcopy(pars[1]._p)
            p._p.addprevious(new)
            p._p.getparent().remove(p._p)
    pars = row.cells[1].paragraphs
    for k in range(sig):
        text = CLIENT_LINES[k] if k < len(CLIENT_LINES) else ""
        if pars[k].runs:
            set_text(pars[k], text)
        elif text:
            pars[k].add_run(text)
    next(r for r in pars[sig].runs if r.text.strip() and not r.text.startswith("_")).text = CLIENT_SIG

out = ROOT / "output" / f"Договір_SEO_{SITE}_{date:%m-%Y}.docx"
# зайвий «___» під першою таблицею реквізитів
for table in doc.tables:
    for r in table.rows:
        if r.cells[1].text.strip() == "___":
            for p in r.cells[1].paragraphs:
                for run in p.runs:
                    run.text = ""
doc.save(out)
print(out, f"({o['price']['usd']} $ × {o['price']['rate']} = {uah} грн)")
