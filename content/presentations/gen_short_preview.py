# -*- coding: utf-8 -*-
"""Генерує HTML-прев'ю короткої презентації Site24 (9 слайдів 16:9), вірне геометрії PPTX."""
import os, base64, html
BASE=os.path.dirname(os.path.abspath(__file__))
def b64(p):
    with open(p,'rb') as f: return base64.b64encode(f.read()).decode()
LOGO="data:image/png;base64,"+b64(os.path.join(BASE,"bettertone-assets/icons/site24-ink.png"))
CLIENTS="data:image/jpeg;base64,"+b64(os.path.join(BASE,"bettertone-assets/clients-logos.jpeg"))
def dataimg(p):
    ext=p.rsplit('.',1)[1].lower(); mt={'png':'png','jpg':'jpeg','jpeg':'jpeg'}[ext]
    return f"data:image/{mt};base64,"+b64(os.path.join(BASE,p))
BADGES={n:dataimg("site24-assets/badges/"+n) for n in ["google-partner.png","clutch.jpg","horoshop.png"]}
NICHES={n:dataimg("site24-assets/niches/"+n) for n in ["ecommerce.png","medicine.png","manufacturing.png","services.png","realestate.png","edtech.png"]}

# ---- helpers: абсолютне позиціювання в pt (1pt=1px базово, слайд 960x540) ----
def box(x,y,w,h,style="",inner=""):
    return f'<div style="position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;{style}">{inner}</div>'
def slides_html():
    S=[]
    def start(bg="#fff"): S.append([]); S[-1].append(bg)
    def add(h): S[-1].append(h)
    MX=64
    # каталог кольорів
    INK="#0E0E3A";BLUE="#2966FF";GREEN="#36EF74";GREENM="#94FCB1";MINT="#E6FAEE";TINT="#DAF8FF";INK60="#6E6E88";LINE="#DDE1EC"
    def foot(n):
        return (box(MX,504,140,20,f"font:12px Ubuntu;color:{INK60}",str(n))
                +box(760,505,140,22,"text-align:right",f'<img src="{LOGO}" style="height:20px">'))
    def case(tagtxt,htitle,subtitle,stats4,task,case_url,foot_num):
        start("#fff")
        add(box(MX,50,110,27,f"background:{BLUE};border-radius:14px;color:#fff;font:700 13px Ubuntu;display:inline-flex;align-items:center;justify-content:center;padding:0 16px",tagtxt))
        add(box(MX,80,832,50,f"font:700 27px Ubuntu;line-height:1.08;color:{INK}",htitle))
        add(box(MX,134,832,26,f"font:15px Ubuntu;line-height:1.3;color:{INK60}",subtitle))
        add(box(MX,168,832,62,f"background:{MINT};border-radius:14px;display:flex;align-items:center;padding:0 24px",
            f'<span style="width:4px;height:22px;background:{BLUE};margin-right:16px;flex:none"></span>'
            f'<span style="font:13.5px Ubuntu;line-height:1.28;color:{INK60}"><b style="color:{INK}">Задача: </b>{task}</span>'))
        for i,(n,l) in enumerate(stats4):
            x=MX+i*(200+11)
            add(box(x,250,200,150,f"background:{TINT};border-radius:18px",""))
            add(box(x+22,274,14,14,f"background:{GREEN}",""))
            add(box(x+22,294,160,52,f"font:700 36px Ubuntu;color:{BLUE}",n))
            add(box(x+22,348,164,50,f"font:11.5px Ubuntu;line-height:1.18;color:{INK60}",l))
        add(box(MX,438,320,22,f"font:700 14px Ubuntu",f'<a href="{case_url}" style="color:{BLUE};text-decoration:none">Детальніше про кейс&nbsp;&nbsp;→</a>'))
        add(box(512,438,320,22,f"font:700 14px Ubuntu;text-align:right",f'<a href="https://site24.com.ua/tag/kejsi/" style="color:{INK60};text-decoration:none">Читати всі кейси&nbsp;&nbsp;→</a>'))
        add(foot(foot_num))

    # 01 ТИТУЛ
    start(TINT)
    add(box(MX,58,300,32,"",f'<img src="{LOGO}" style="height:32px">'))
    add(box(MX,168,150,27,f"background:{BLUE};border-radius:14px;color:#fff;font:700 13px Ubuntu;display:flex;align-items:center;justify-content:center","ПРО КОМПАНІЮ"))
    add(box(MX,206,820,120,f"font:700 46px Ubuntu;line-height:1.08;color:{INK}",f'Агенція <span style="color:{BLUE}">digital-маркетингу</span>'))
    add(box(MX,326,720,60,f"font:20px Ubuntu;color:{INK60}","SEO та PPC просування, що приводить клієнтів з Google та AI"))
    add(box(MX,398,300,4,f"background:{GREEN}",""))
    add(box(MX,504,460,20,f"font:13px Ubuntu;color:{INK60}",'site24.com.ua &nbsp;&nbsp;·&nbsp;&nbsp; <b>+38 (098) 738 77 08</b>'))
    add(box(720,504,180,20,f"font:12px Ubuntu;color:{INK60};text-align:right","2026"))

    # 02 ХТО МИ + STATS
    start("#fff")
    add(box(MX,54,820,40,f"font:700 30px Ubuntu;color:{INK}",f'Хто <span style="color:{BLUE}">ми</span>'))
    add(box(MX,118,832,84,f"font:17px Ubuntu;line-height:1.4;color:{INK}",'Site24 — агенція digital-маркетингу, що спеціалізується на просуванні сайтів у Google через SEO та PPC. Працюємо як <b>партнер</b>, який допомагає малому та середньому бізнесу залучати клієнтів із пошуку — без зайвих технічних клопотів.'))
    stats=[("1000+","сайтів вивели в топ Google"),("550+","прибуткових рекламних кампаній запущено"),("86%","клієнтів приходять до нас за рекомендацією"),("9","років успіху на ринку просування")]
    for i,(n,l) in enumerate(stats):
        x=MX+i*(200+11)
        add(box(x,236,200,150,f"background:{TINT};border-radius:18px",""))
        add(box(x+22,262,14,14,f"background:{GREEN}",""))
        add(box(x+22,282,160,54,f"font:700 42px Ubuntu;color:{BLUE}",n))
        add(box(x+22,336,164,48,f"font:12.5px Ubuntu;line-height:1.18;color:{INK60}",l))
    add(foot("02"))

    # 03 ПЕРЕВАГИ
    start("#fff")
    add(box(MX,50,860,40,f"font:700 30px Ubuntu;color:{INK}",f'Конкурентні <span style="color:{BLUE}">переваги</span>'))
    adv=[("Партнер, а не підрядник","Не просто виконуємо ТЗ, а самі пропонуємо покращення й беремо на себе повний цикл просування: лінкбілдинг, крауд-маркетинг, UX, роботу з розробниками та аналітику. Готові «підставити плече» на кожному етапі й вести проєкт як власний."),
         ("Орієнтація на ROI","Будуємо стратегію так, щоб SEO та PPC приносили максимальну окупність — не просто позиції в топі, а більше клієнтів і прибутку. Перші результати клієнт бачить уже за 2–3 місяці, і вони працюють у довгостроковій перспективі."),
         ("Прозорість","Клієнт завжди знає, що ми робимо, за що платить і які результати отримуємо. Регулярна звітність зрозумілою мовою бізнесу — конкретні цифри та вигоди, без складних технічних термінів.")]
    for i,(t,d) in enumerate(adv):
        x=MX+i*(270+11)
        add(box(x,120,270,252,f"background:{MINT};border-radius:18px",""))
        add(box(x+20,142,38,4,f"background:{BLUE}",""))
        add(box(x+20,162,232,52,f"font:700 18px Ubuntu;line-height:1.1;color:{INK}",t))
        add(box(x+20,224,232,134,f"font:13px Ubuntu;line-height:1.35;color:{INK60}",d))
    add(foot("03"))

    # 04 КЛІЄНТСЬКИЙ СЕРВІС
    start("#fff")
    add(box(MX,50,890,40,f"font:700 27px Ubuntu;color:{INK}",f'Чому клієнтський сервіс <span style="color:{BLUE}">Site24</span> найкращий'))
    serv=[("Постійний контакт з менеджером",'Ваш персональний project-менеджер завжди на зв\'язку, володіє всією актуальною інформацією та оперативно відповідає на запити. <b style="color:'+BLUE+'">90% звернень вирішуються в день надходження.</b>'),
          ("Прозоре спілкування без «води»","Пояснюємо складні речі простою мовою, без технічного жаргону. Ви завжди розумієте, що і навіщо ми робимо у вашій рекламній кампанії."),
          ("Відкритість у бюджетах та звітах","Працюємо з відкритими бюджетами: ви чітко бачите, скільки йде на рекламу, а скільки — на нашу роботу. Усі дії задокументовані та прозорі.")]
    for i,(t,d) in enumerate(serv):
        x=MX+i*(270+11)
        add(box(x,116,270,232,f"background:{MINT};border-radius:18px",""))
        add(box(x+20,138,38,4,f"background:{BLUE}",""))
        add(box(x+20,158,232,50,f"font:700 17px Ubuntu;line-height:1.12;color:{INK}",t))
        add(box(x+20,212,232,128,f"font:12.5px Ubuntu;line-height:1.32;color:{INK60}",d))
    add(box(MX,372,832,50,f"background:{BLUE};border-radius:14px;display:flex;align-items:center;justify-content:center;font:17px Ubuntu",f'<span style="color:#fff">Ваш успіх — </span><span style="color:{GREENM}">&nbsp;наша репутація.</span>'))
    add(foot("04"))

    # 05 СЕРТИФІКАТИ
    start("#fff")
    add(box(MX,54,860,40,f"font:700 30px Ubuntu;color:{INK}",f'<span style="color:{BLUE}">Сертифікати</span> та статуси'))
    add(box(MX,116,832,30,f"font:15px Ubuntu;color:{INK60}","Підтверджена експертиза й офіційні партнерські статуси провідних платформ."))
    certs=[("google-partner.png","Офіційний партнерський статус Google Ads — доступ до бета-функцій, навчання та підтримки платформи."),
           ("clutch.jpg","Верифікований профіль із реальними відгуками клієнтів на міжнародному рейтингу агенцій."),
           ("horoshop.png","Сертифікований підрядник для e-commerce на одній із провідних платформ України.")]
    for i,(logo,d) in enumerate(certs):
        x=MX+i*(270+11)
        add(box(x,176,270,210,f"background:#fff;border:1px solid {LINE};border-radius:18px",""))
        add(box(x,176,270,6,f"background:{BLUE};border-radius:18px 18px 0 0",""))
        add(box(x+24,204,222,84,f"background:{TINT};border-radius:12px;display:flex;align-items:center;justify-content:center",f'<img src="{BADGES[logo]}" style="max-width:182px;max-height:56px">'))
        add(box(x+24,304,222,68,f"font:13px Ubuntu;line-height:1.32;color:{INK60}",d))
    add(foot("05"))

    # 05 ПОСЛУГИ
    start("#fff")
    add(box(MX,50,860,40,f"font:700 30px Ubuntu;color:{INK}",f'Послуги <span style="color:{BLUE}">та технології</span>'))
    svc=[("SEO-просування сайтів","Комплексне виведення сайту в топ Google за комерційними запитами"),
         ("PPC / контекстна реклама","Google Ads під ROI: пошук, банери, ремаркетинг, Shopping"),
         ("Просування в AI","Видимість у ChatGPT та AI Overview (AEO) — новий канал трафіку"),
         ("SERM — репутація в пошуку","Керування тим, що бачить клієнт про бренд у видачі"),
         ("Просування закордонних сайтів","SEO та PPC для інших країн, мов і ринків")]
    for i,(t,d) in enumerate(svc):
        y=110+i*(56+9)
        add(box(MX,y,832,56,f"background:{MINT};border-radius:12px;display:flex;align-items:center",
            f'<span style="color:{BLUE};font:700 18px Ubuntu;padding:0 12px 0 20px">→</span>'
            f'<span style="font:700 16.5px Ubuntu;color:{INK};width:288px">{t}</span>'
            f'<span style="font:13.5px Ubuntu;color:{INK60}">{d}</span>'))
    add(box(MX,438,140,20,f"font:700 13px Ubuntu;color:{BLUE}","Працюємо з:"))
    add(box(MX+108,438,724,20,f"font:13.5px Ubuntu;color:{INK60}","Google Analytics 4  ·  Search Console  ·  Google Ads  ·  Ahrefs  ·  Serpstat  ·  Screaming Frog"))
    add(foot("06"))

    # 06 ГАЛУЗЕВИЙ ДОСВІД
    start("#fff")
    add(box(MX,54,880,40,f"font:700 30px Ubuntu;color:{INK}",f'Галузевий <span style="color:{BLUE}">досвід</span>'))
    add(box(MX,116,832,30,f"font:15px Ubuntu;color:{INK60}","Розуміємо специфіку різних ніш — від e-commerce до медицини — на ринку України та за кордоном."))
    niches=[("E-commerce","ecommerce.png"),("Медицина","medicine.png"),("Виробництво","manufacturing.png"),("Сервісні бізнеси","services.png"),("Нерухомість","realestate.png"),("IT та освіта","edtech.png")]
    for i,(t,ic) in enumerate(niches):
        x=MX+(i%3)*(270+11); y=172+(i//3)*(74+14)
        add(box(x,y,270,74,f"background:{TINT};border-radius:14px;display:flex;align-items:center;padding-left:16px",
            f'<span style="width:46px;height:46px;background:#fff;border-radius:11px;display:flex;align-items:center;justify-content:center;margin-right:16px"><img src="{NICHES[ic]}" style="width:28px;height:28px"></span>'
            f'<span style="font:700 17px Ubuntu;color:{INK}">{t}</span>'))
    add(box(MX,400,832,64,f"background:{BLUE};border-radius:16px;display:flex;align-items:center;padding:0 28px;font:15px Ubuntu",f'<span style="color:#fff">Локальний та міжнародний досвід — </span><span style="color:{GREENM}">&nbsp;працюємо і з українськими, і з закордонними проєктами: різні країни, мови та ринки.</span>'))
    add(foot("07"))

    # 07 КЛІЄНТИ
    start("#fff")
    add(box(MX,54,820,40,f"font:700 30px Ubuntu;color:{INK}",f'Нам <span style="color:{BLUE}">довіряють</span>'))
    add(box(MX,110,832,26,f"font:15px Ubuntu;color:{INK60}","Понад 1000 бізнесів обрали Site24 для просування — від локальних магазинів до брендів національного рівня."))
    add(box(MX,158,832,316,"display:flex;align-items:flex-start;justify-content:center",f'<img src="{CLIENTS}" style="max-width:832px;max-height:316px">'))
    add(foot("08"))

    # 09 КЕЙС SEO
    case("SEO-КЕЙС",
         f'Кейс: <span style="color:{BLUE}">музичний інтернет-магазин</span>',
         "Спеціалізований онлайн-магазин гітар та музичних інструментів на платформі Horoshop.",
         [("×24","зростання SEO-трафіку: 667 → 17 205 візитів/міс"),
          ("1922","запити в ТОП-3 Google (48% ядра)"),
          ("3705","запитів у ТОП-10 (92% ядра)"),
          ("18 міс","тривалість проєкту")],
         "вивести пріоритетні категорії гітар у ТОП-3 Google з мінімальним бюджетом на посилання — старт на початку повномасштабного вторгнення.",
         "https://site24.com.ua/seo-prodvizhenie-internet-magazina-muzykalnyh-instrumentov/","09")

    # 10 КЕЙС PPC
    case("PPC-КЕЙС",
         f'Кейс: <span style="color:{BLUE}">e-commerce — дохід ×2,5 за рік</span>',
         "The Tea (thetea.ua) — інтернет-магазин китайського чаю та аксесуарів для чайних церемоній.",
         [("×2,5","зростання доходу за рік"),
          ("×2,3","транзакції: 940 → 2143 /міс"),
          ("+200%","ROAS: 333% → 523%"),
          ("30+","нових Google Ads кампаній")],
         "масштабувати контекстну рекламу магазину чаю The Tea та збільшити кількість замовлень і дохід.",
         "https://site24.com.ua/ppc-dlya-e-commerce-zrostannya-dohodu-v-25-razi-za-odin-rik/","10")

    # 11 КОНТАКТИ
    start(TINT)
    add(box(MX,58,300,30,"",f'<img src="{LOGO}" style="height:30px">'))
    add(box(MX,150,760,60,f"font:700 38px Ubuntu;color:{INK}",f'Обговоримо <span style="color:{BLUE}">ваш проєкт</span>?'))
    add(box(MX,222,700,30,f"font:17px Ubuntu;color:{INK60}","Проведемо безкоштовну консультацію та покажемо точки зростання для вашого сайту."))
    add(box(MX,296,360,18,f"font:700 12.5px Ubuntu;color:{BLUE}","КЕРІВНИК АГЕНЦІЇ"))
    add(box(MX,318,420,26,f"font:18px Ubuntu;color:{INK}","Катерина Золотарьова"))
    add(box(MX,372,360,18,f"font:700 12.5px Ubuntu;color:{BLUE}","ТЕЛЕФОН"))
    add(box(MX,394,420,26,f"font:18px Ubuntu;color:{INK}","+38 (098) 738 77 08"))
    add(box(500,372,360,18,f"font:700 12.5px Ubuntu;color:{BLUE}","САЙТ"))
    add(box(500,394,420,26,f"font:700 18px Ubuntu;color:{BLUE}","site24.com.ua"))
    add(box(500,296,300,52,"",f'<a href="https://t.me/katerinazolotaryova" style="display:flex;width:300px;height:52px;background:{GREEN};border-radius:12px;align-items:center;justify-content:center;font:700 16px Ubuntu;color:{INK};text-decoration:none">Замовити консультацію&nbsp;&nbsp;→</a>'))
    add(box(MX,504,160,20,f"font:12px Ubuntu;color:{INK60}","11"))
    return S

def render():
    S=slides_html()
    parts=[]
    for i,sl in enumerate(S):
        bg=sl[0]; inner="".join(sl[1:])
        parts.append(f'<div class="wrap"><div class="cap">Слайд {i+1} / {len(S)}</div><div class="slide" style="background:{bg}">{inner}</div></div>')
    css="""
    *{box-sizing:border-box;margin:0;padding:0}
    body{background:#EEF1F6;font-family:Ubuntu,system-ui,sans-serif;padding:32px 0}
    .page{max-width:1000px;margin:0 auto}
    h1.t{font:700 24px Ubuntu;color:#0E0E3A;padding:0 20px 4px}
    p.s{font:14px Ubuntu;color:#6E6E88;padding:0 20px 24px}
    .wrap{margin:0 auto 34px;width:960px;max-width:96vw}
    .cap{font:600 12px Ubuntu;color:#9AA0B4;margin-bottom:6px}
    .slide{position:relative;width:960px;height:540px;border-radius:14px;overflow:hidden;box-shadow:0 8px 30px rgba(20,30,60,.14);transform-origin:top left}
    @media(max-width:1000px){.slide{transform:scale(calc(96vw/960))}.wrap{height:auto}}
    """
    return f"""<!doctype html><html lang="uk"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Ubuntu:wght@400;500;700&display=swap" rel="stylesheet">
<title>Site24 — коротка презентація (прев'ю)</title><style>{css}</style></head>
<body><div class="page"><h1 class="t">Site24 — коротка презентація «Про компанію»</h1>
<p class="s">Прев'ю 11 слайдів (16:9). Редагований файл: 2026-07-15-EN-site24-company-short.pptx</p>
{''.join(parts)}</div></body></html>"""

open(os.path.join(BASE,"2026-07-15-EN-site24-company-short.html"),"w").write(render())
print("WROTE 2026-07-15-EN-site24-company-short.html")
