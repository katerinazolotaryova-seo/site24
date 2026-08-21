# Блог — орфо-перевірка (батч 3, статті 21-30)

**Період:** жовт 2020 → серп 2017 *(найстаріший контент)*
**Формат:** список «знайти/замінити» по 3 мовах. Системні баги шаблону НЕ повторюються — див. батч 1.

> 📌 **Підсумкова примітка про обсяг блогу:**
> Eugenia назвала «21-32», але в публічному блозі **рівно 30 статей** (4 сторінки пагінації: 8+8+8+6, page 5 = 404). Якщо є ще 2 статті в чернетках WP — надішли URL окремо, переглянемо. Цей батч покриває **всі решта 10 опублікованих** (статті 21-30 за нумерацією батчів).

---

## 🛠 Для розробників (нові знахідки на рівні CMS/шаблону/URL)

| Стаття | Проблема | Дія |
|---|---|---|
| 25. Нульова позиція | **Slug — російська транслітерація.** URL `/yz-chego-sostoyt-rabota-seo-speczyalysta/` перекладається з рос. «из чего состоит работа SEO специалиста», тоді як H1 — «Оптимізація під «нульову позицію»: майбутнє голосового пошуку». І мова slug-у не та (треба укр.), і теми не збігаються. | Замінити slug на укр. варіант + 301-редирект зі старого |
| 29. Фільтри Google | **Помилки безпосередньо в H1 (UA + EN).** UA: «Що таке фільтри **google**? За що можна **попасти под** фільтр?» (google з малої + росизми «попасти под»). EN: «What are **google** filters? **For what you can get under** the filter?» (google з малої + поламаний синтаксис). | Виправити обидва H1 → «Що таке фільтри Google? За що можна потрапити під фільтр?» / «What are Google filters? What can get your site filtered?» |
| 27. 13 питань PPC (EN) | **Непереведений російсько-український сленг** у EN-версії: «**herak-herak and in production**» (від «хєрак-хєрак і в продакшн» — означає «зроблено швидко й неякісно»). | Замінити на ідіоматичне «slapped together and shipped» або переписати фразу |
| 26. Садові товари | **Російські слова в H2/H3 укр. версії.** H2: «**Клиент**» (треба «Клієнт»). H3: «**2 этап**. Семантика та Onpage оптимізаці**ї**» (треба «2 етап» + «оптимізація» — у статті обрізане слово). | Виправити заголовки |
| 21. Етапи SEO робіт | **Дефіс/тире у H1.** «Етапи робіт з просування сайту - що входить у вартість SEO просування» — короткий дефіс замість тире + «SEO просування» без дефіса. | H1 → «Етапи робіт з просування сайту — що входить у вартість SEO-просування» |

---

## 21. Етапи робіт з просування сайту — вартість SEO-просування (15.10.2020)

**URL:** `/z-chogo-skladayetsya-robota-seo-fahivczya/` | `/en/what-does-the-job-of-an-seo-specialist-consist-of/` | `/ru/iz-chego-sostoit-rabota-seo-spetsialista/`

### UA
| Знайти | Замінити | Тип |
|---|---|---|
| Етапи робіт з просування сайту - **що входить у вартість SEO просування** (H1) | Етапи робіт з просування сайту — **що входить у вартість SEO-просування** | дефіс→тире + відсутній дефіс у SEO-просування |
| **по посадкових сторінках** | **за посадковими сторінками** | русизм «по» |
| **Google** vs **google** (інконсистенція в тексті) | **Google** скрізь | стиль |
| **SEO** vs **СЕО** (інконсистенція) | **SEO** (латиниця) скрізь | стиль |
| під останнім розуміються | під ним мається на увазі | стиль |

### EN
| Знайти | Замінити | Тип |
|---|---|---|
| Therefore, keep a list of **what works** your sites get to the top, get traffic and sales | Therefore, **here is a list of what helps your sites reach the top, get traffic, and make sales** | поламаний синтаксис (втрачені кома й сполучник) |
| the task of this stage is to determine **how certain sites are in the top** | the task of this stage is to determine **why certain sites rank in the top** | калька («як сайти знаходяться в топі») |
| will 'lead' your site to the wrong place | will steer / send your site in the wrong direction | стиль |
| an **irrationally large** core will eat up a lot of time | an **excessively large** keyword set will consume too much time | стиль («irrationally» неприродне) |
| **devaka.ru back in 2012 compiled a diagram** | **devaka.ru compiled a diagram back in 2012** | порядок слів + застаріле посилання (devaka.ru — рос. SEO-сайт, перевірити чи актуальне) |
| **"Collecting** the semantic core" | "**Building** the semantic core" / "**Building keyword research**" | калька («збір» ядра) |

### RU
| Знайти | Замінити | Тип |
|---|---|---|
| **Список работ по СЕО** (заголовок секції) | **Список работ по SEO** | кириличний акронім СЕО → SEO (як скрізь у статті латиницею) |
| SEO/СЕО — інконсистенція по тексту | уніфікувати **SEO** | стиль |
| Элементами структуры должен быть не только текст, но и картинки, иконки, инфографика | Элементами структуры **должны быть** не только текст, но и картинки, иконки, инфографика | узгодження мн. (множинні підмети) |

---

## 22. Реклама в Amazon: особливості налаштування (04.09.2020)

**URL:** `/reklama-v-amazon-osoblyvosti-ta-nyuansy-nalashtuvannya/` | `/en/advertising-on-amazon-features-and-nuances-of-customization/` | `/ru/reklama-v-amazon-osobennosti-i-nyuansy-nastrojki/`

### UA
| Знайти | Замінити | Тип |
|---|---|---|
| **Амазон** / **амазону** / **Amazon** (інконсистенція в тексті) | **Amazon** скрізь | стиль (то транскрипція, то латиниця) |
| **бренднейм** | **бренд-нейм** | відсутній дефіс |
| **Вішаліст** | **вішлист** *(або калька «список бажань»)* | неточна транслітерація wishlist |
| **мінус-слова** vs **мінус слова** (інконсистенція) | уніфікувати **мінус-слова** з дефісом | стиль |
| **РК** (без розкриття при першій згадці) | **рекламна кампанія (РК)** при першій згадці | стиль |
| **ACoS** (Advertising Cost of Sale) | додати укр. розшифровку при першій згадці | стиль |

### EN
| Знайти | Замінити | Тип |
|---|---|---|
| **Keys** can be collected not very carefully | **Keywords** can be collected **without thorough vetting** | калька + неточний термін («keys»→«keywords») |
| the coverage of your listings **is growing** | the coverage of your listings **grows** | tense (тривала vs проста) |
| **And it has** its own in-house advertising tool | (поч. речення зі сполучника) краще: **«It also has its own in-house advertising tool»** | стиль |
| the efficiency of using Amazon as a trading platform **is growing** | …as a marketplace **grows** | калька («торгова площадка» → marketplace) |

### RU
| Знайти | Замінити | Тип |
|---|---|---|
| в рекламном кабинете **имеется три формата рекламы** | в рекламном кабинете **имеются три формата рекламы** *(або «есть три формата»)* | узгодж. мн. |
| Інші помилки RU потребують повного fetch — модель скоротила | (ручна перевірка) | – |

---

## 23. Кейс: flash-sale → стабільний SEO-трафік у ніші одягу (27.06.2020)

**URL:** `/kejs-pro-prosuvannya-flash-sale-proektu-v-nishi-odyagu/` | `/en/case-about-the-promotion-of-a-flash-sale-project-in-the-clothing-niche/` | `/ru/kejs-pro-prodvizhenie-flash-sale-proekta-v-nishe-odezhdy/`

### UA
| Знайти | Замінити | Тип |
|---|---|---|
| Кейс із просування інтернет-магазину одягу: від flash-sale до стабільного **SEO трафіку** (H1) | Кейс із просування…до стабільного **SEO-трафіку** | відсутній дефіс у H1 |
| **Висновки щодо проекту** (H2) | **Висновки щодо проєкту** | новий правопис |
| **проєкту** vs **проекту** — імовірна інконсистенція у тілі (бо H1/H2 з обома формами повторюються у попередніх статтях) | уніфікувати **проєкту** | стиль |
| flash-sale (бренд/термін) | OK | – |

### EN
| Знайти | Замінити | Тип |
|---|---|---|
| **At the entrance** / **At the exit** *(перекладено «На вході / На виході»)* | **Initial state** / **Final result** *(або просто **Before** / **After**)* | калька з UA-кейс-формату |
| increased growth of organic non-branded traffic **by 4.2 times** | …non-branded traffic **4.2-fold** *(або «grew 4.2x»)* | стиль |
| Experiments have shown**,** that in the clothing niche | Experiments have shown **that** in the clothing niche | зайва кома після «shown» (підрядне з «that») |
| flash-sale **on clothes and household goods** | **a flash-sale of** clothes and household goods | артикль + прийменник |

### RU
| Знайти | Замінити | Тип |
|---|---|---|
| Кейс по продвижению интернет-магазина одежды: от flash-sale до стабильного **SEO трафика** (H1) | …до стабильного **SEO-трафика** | відсутній дефіс у H1 |
| Кейс **по продвижению** | (OK для RU — «по» норма) | – |

---

## 24. Кейс SEO-просування інтернет-магазину сумок та аксесуарів (31.05.2020)

**URL:** `/kejs-seo-prosuvannya-internet-magazinu-sumok-i-aksesuariv/` | `/en/case-seo-promotion-of-an-online-store-of-bags-and-accessories/` | `/ru/kejs-seo-prodvizhenie-internet-magazina-sumok-i-aksessuarov/`

### UA
| Знайти | Замінити | Тип |
|---|---|---|
| **Задача на проекті** (H2) | **Завдання на проєкті** | калька «задача»→«завдання» + новий правопис |
| **Що вже було на проекті до старту SEO робіт** (H2) | **Що вже було на проєкті до старту SEO-робіт** | новий правопис + відсутній дефіс |
| **SEO робіт** | **SEO-робіт** | відсутній дефіс |

### EN
| Знайти | Замінити | Тип |
|---|---|---|
| Results of **1 year systematic work** | Results of **1 year of systematic work** | пропущений прийменник |
| **What's at the start?** | **Where we started / Initial state** | калька («Що на старті?») |
| **Client: online store of bags** | **Client: an online store of bags** *(або «The client: an online…»)* | артикль |
| We worked in detail with several categories | We worked **in depth** with several categories *(«in detail» означає «детально», стиль OK)* | стиль (другорядне) |
| **turned on maximum randomness** | **maximized randomization** / **randomized link distribution** | калька |

### RU
| Знайти | Замінити | Тип |
|---|---|---|
| Кейс о том, как за год **системной работы** | (OK) | – |
| Інші помилки RU потребують повного fetch — модель скоротила | (ручна перевірка) | – |

---

## 25. Оптимізація під «нульову позицію»: майбутнє голосового пошуку (30.05.2020)

**URL:** `/yz-chego-sostoyt-rabota-seo-speczyalysta/` ⚠️ *slug — рос. транслітерація, тема статті інша; див. розділ «Для розробників»* | `/en/optimizing-for-position-zero-the-future-of-voice-search/` | `/ru/optimizatsiya-pod-nulevuyu-pozitsiyu/`

### UA
| Знайти | Замінити | Тип |
|---|---|---|
| Оптимізація під «нульову позицію»: майбутнє голосового пошуку (H1) | (OK у тексті, але **slug не відповідає** — див. devs) | – |
| **розширений сніпет** | **розширений сніпет** *(допустимо)* / **розширений фрагмент** | стиль (англіцизм) |
| цифровий помічник **«зведе» ваш бізнес** | цифровий помічник **«приведе» / «направить»** до вашого бізнесу | стиль («звести бізнес» = «розорити» — потенційна двозначність) |
| Статистика дат: «50% **next year**» — стаття 2020, посилання на comScore | оновити фактологію або зняти статистику | застаріла фактологія (2020→2026) |

### EN
| Знайти | Замінити | Тип |
|---|---|---|
| The era of voice search is still just beginning, **however,** this new type of search engine use, according to comScore data, will reach 50% of the global market **next year** | …**however** + переробка довгого речення з трьома підрядними | синтаксис довжина + застарілий «next year» |
| focus on **zero position** | focus on **position zero** *(стандартний EN-термін)* | стиль |
| rich snippet **styling** | rich snippet **markup / formatting** | калька |

### RU
| Знайти | Замінити | Тип |
|---|---|---|
| Нулевая позиция Google: правила **SEO оптимизации сайта** нулевой позиции (H1) | Нулевая позиция Google: правила **SEO-оптимизации сайта** нулевой позиции | відсутній дефіс |

---

## 26. Кейс SEO-просування інтернет-магазину садових товарів (29.05.2020)

**URL:** `/kejs-prosuvannya-internet-magazinu-sadovih-tovariv/` | `/en/case-promotion-of-an-online-store-of-garden-products/` | `/ru/kejs-prodvizhenie-internet-magazina-sadovyh-tovarov/`

### UA
| Знайти | Замінити | Тип |
|---|---|---|
| **Клиент** (H2 у UA-статті) | **Клієнт** | росіянизм у заголовку |
| **2 этап. Семантика та Onpage оптимізаці** (H3) | **2 етап. Семантика та On-page оптимізація** | росіянизм «этап» + обрізане слово + відсутній дефіс «On-page» |
| **Onpage оптимізаці** | **On-page оптимізація** | відсутній дефіс + обрізане слово |
| **пессимізіровалі** | **песимізувалися / були під фільтром** | рос-укр гібрид (рос. «пессимизировали» + укр. суфікс) |
| **гет-параметри** vs **get-параметри** (інконсистенція в тексті) | уніфікувати — або скрізь **get-параметри** (латиниця), або скрізь транслітерація | стиль |
| **301-редирект** vs **301-го редиректа** (інконсистенція) | уніфікувати: **301-й редирект** / **301-го редиректу** (відмінок -у) | стиль |
| **2-ро роки** | **2-ох років / 2 роки** | стиль/числівник |

### EN
| Знайти | Замінити | Тип |
|---|---|---|
| We were tasked **to return** traffic | We were tasked **with returning** traffic | калька |
| **pessimization** of the site | **demotion / penalty / drop in rankings** | неологізм-калька (рос. «песимізація») |
| **gluing the pages** | **consolidating / merging pages** | калька |
| **High cost of goods; long purchase cycle** | **A high cost of goods; a long purchase cycle** *(або переписати у повних реченнях)* | артиклі |
| moved to HTTPS | moved to **HTTPS** *(OK)* / migrated to HTTPS | стиль |

### RU
| Знайти | Замінити | Тип |
|---|---|---|
| Кейс по продвижению | (OK для RU) | – |
| Інші помилки RU потребують повного fetch — модель скоротила | (ручна перевірка) | – |

---

## 27. 13 найпопулярніших питань по контекстній рекламі (27.05.2020)

**URL:** `/13-najpopulyarnishih-pitan-po-kontekstnij-reklami/` | `/en/13-most-popular-ppc-advertising-questions/` | `/ru/13-samyh-populyarnyh-voprosov-po-kontekstnoj-reklame/`

### UA
| Знайти | Замінити | Тип |
|---|---|---|
| 13 найпопулярніших питань **по контекстній рекламі** (H1) | 13 найпопулярніших питань **з контекстної реклами** | русизм «по»→«з» прямо в H1 |
| **по типу** (у тексті) | **типу / на кшталт** | русизм |
| **CTR** (без розкриття при першій згадці) | **CTR (click-through rate, відсоток кліків)** при першій згадці | стиль |
| **по широкій відповідності** *(в контексті PPC keyword match)* | **за широкою відповідністю / у широкій відповідності** | русизм «по» |

### EN
| Знайти | Замінити | Тип |
|---|---|---|
| **herak-herak and in production** | **slapped together and shipped** *(або переписати без сленгу)* | 🔴 **непереведений рос/укр сленг у тексті статті** |
| In order not to see the suffering in their eyes every time, we decided to write an article with **typical** questions | …with **the typical** questions | артикль |
| **did not make transitions** | **did not click through** | калька |
| you may simply **not get into the targeting settings** | you may simply **fail to fit the targeting parameters / be filtered out by targeting** | калька |
| There are issues that represent **a particular pain** for the PPC department staff | …**a particular headache / a real pain point** | стиль |

### RU
| Знайти | Замінити | Тип |
|---|---|---|
| 13 самых популярных вопросов **по контекстной рекламе** (H1) | (OK для RU — «по» норма) | – |
| Інші помилки RU потребують повного fetch — модель скоротила | (ручна перевірка) | – |

---

## 28. Кейс: SEO-просування сайту медичного обладнання (22.05.2020)

**URL:** `/kejs-seo-prosuvannya-sajtu-medichnogo-obladnannya/` | `/en/case-of-seo-promotion-of-a-medical-equipment-website/` | `/ru/kejs-seo-prodvizheniya-sajta-mediczinskogo-oborudovaniya/`

### UA
| Знайти | Замінити | Тип |
|---|---|---|
| **«Залишити заявку»** *(CTA повторюється 7+ разів у тексті без варіацій)* | змінити частину на «Замовити консультацію» / «Зв'язатися» — варіювати | стиль (UX) |
| H1: Кейс: SEO-просування сайту медичного обладнання | (OK) | – |
| ⚠️ Стаття потребує детальнішого прочитання — модель скоротила | (ручна перевірка) | – |

### EN
| Знайти | Замінити | Тип |
|---|---|---|
| Results of **15 months systematic work** | Results of **15 months of systematic work** | пропущений прийменник |
| moved to HTTPS | (OK) | – |
| **Google's top spots** | **Google's top positions / top rankings** | стиль (calque «топові місця») |
| **link mass formation** | **link building** | калька («формування посилальної маси») |
| 83% of keywords **from commercial pages** reached Google's top 10 | 83% of **commercial-page keywords** reached Google's top 10 | стиль |
| **High cost of goods; long purchase cycle** | (як у статті 26) | артиклі |

### RU
| Знайти | Замінити | Тип |
|---|---|---|
| Кейс о том, как за 15 месяцев | (OK) | – |
| ⚠️ Стаття потребує детальнішого прочитання | (ручна перевірка) | – |

---

## 29. Що таке фільтри Google? (24.04.2020)

**URL:** `/shho-take-filtri-google-za-shho-mozhna-popasti-pod-filtr/` | `/en/what-are-google-filters-for-what-you-can-get-under-the-filter/` | `/ru/chto-takoe-filtry-google-za-chto-mozhno-poluchit-filtr/`

### UA
| Знайти | Замінити | Тип |
|---|---|---|
| 🔴 Що таке фільтри **google**? За що можна **попасти под** фільтр? (H1) | Що таке фільтри **Google**? За що можна **потрапити під** фільтр? | google→Google + росизми «попасти под»→«потрапити під» **у заголовку статті** |
| **попасти под фільтр** (повторюється в тексті) | **потрапити під фільтр** | росизм по всьому тексту |
| **по типу** | **на кшталт / типу** | росизм |
| **пессимізувати** | **песимізувати** *(один «с»)* / **знизити в ранжуванні** | опечатка/неологізм |
| **google** / **Google** — інконсистенція | **Google** скрізь | стиль |

### EN
| Знайти | Замінити | Тип |
|---|---|---|
| 🔴 What are **google** filters? **For what you can get under** the filter? (H1) | What are **Google** filters? **What can get your site filtered?** | google→Google + поломаний синтаксис H1 |
| Search engine filters are a part of the algorithm that is responsible for ensuring that low-quality **or using incorrect promotion methods are not shown** in SEO results | …ensuring that low-quality **sites or sites using incorrect promotion methods are not shown** in SEO results | пропущ. слово «sites» — підмет загублено |
| **pessimize** (повторюється) | **penalize / demote / lower the ranking** | калька |
| **SEO results** | **SEO **search** results** | стиль |

### RU
| Знайти | Замінити | Тип |
|---|---|---|
| Фильтры поисковой системы — это часть алгоритма, **которая отвечает за то, чтобы некачественные или использующие некорректные методы продвижения сайты не показывались в SEO выдаче** | переписати: «…за то, чтобы **сайты низкого качества или те, что используют некорректные методы продвижения,** не показывались в **SEO-выдаче**» | синтаксис ламається на довгому означенні |
| **SEO выдаче** | **SEO-выдаче** | відсутній дефіс |

---

## 30. Навіщо тобі сайт? або трохи про стратегію (17.08.2017)

**URL:** `/navishho-tobi-sajt-abo-trohy-pro-strategiyu/` | `/en/why-do-you-need-a-website-or-a-little-about-strategy/` | `/ru/zachem-tebe-sajt-ili-nemnogo-o-strategii/`

*Найстаріша стаття на сайті (2017). Авторський тон — розмовний, врахувати при правці.*

### UA
| Знайти | Замінити | Тип |
|---|---|---|
| **сезонний сезон** (потенційна тавтологія — потребує перевірки в контексті) | замінити одне зі слів | можлива тавтологія |
| Авторський підпис «Катерина Золотарьова» vs «Катерина Золотарева» (інконсистенція у відгуках/cards) | уніфікувати **Золотарьова** | стиль |
| H1 «Навіщо тобі сайт? або трохи про стратегію» — «або» з малої | (OK — продовження запитання) | – |
| ⚠️ Стаття 2017 року — застарілі реалії та посилання, переглянути для актуалізації | (загальна правка) | застарілість |

### EN
| Знайти | Замінити | Тип |
|---|---|---|
| only a lazy person or a pensioner **did not think about his space** on the Internet | only the lazy or retirees **haven't thought about having a space** on the Internet | стиль (дослівний переклад «не задумувався про своє місце») |
| The important thing is **that the client is important** | переписати без повтору: **«What matters is the client»** | повторення слова «important» |
| **What are the types of sites in terms of the logic of promotion** | **What types of sites exist from a promotion perspective** | формальна структура |
| a useless piece of code and wasted hosting space | (стиль OK у розмовному регістрі) | – |

### RU
| Знайти | Замінити | Тип |
|---|---|---|
| В нашу эру глобализации и информатизации над своим пространством в Интернете не задумывался, наверное, только ленивый или пенсионер | (стиль OK — авторський тон) | – |
| ⚠️ Стаття 2017 року — потребує загальної актуалізації | (загальна правка) | застарілість |

---

## 📝 Підсумок батчу 3

**Системні знахідки нові для devs (на додаток до батчу 2):**
1. Стаття 25 — slug на рос. транслітерації, тема не відповідає slug-у *(другий випадок H1≠slug, перший був стаття 14)*.
2. Стаття 29 — помилки у самому H1 у двох мовах (UA + EN — «google» з малої, «попасти под», поламаний EN-синтаксис).
3. Стаття 27 EN — **непереведений сленг «herak-herak and in production»** — критичний баг перекладу.
4. Стаття 26 — рос. слова в заголовках UA-статті («Клиент», «2 этап»).
5. Стаття 21 — короткий дефіс у H1 замість тире.

**Перекладацька фактологія/калька:**
- «pessimization» / «pessimize» — калька «песимізація» у статтях 26, 29 EN. Правильно — **«penalty / demotion»**.
- «link mass formation» (стаття 28) — калька «формування посилальної маси». Правильно — **«link building»**.
- «At the entrance / At the exit» (стаття 23) — калька «На вході / На виході». Правильно — **«Initial state / Final result»** або **«Before / After»**.
- «collect cream of high season» / «turned on maximum randomness» / «gluing the pages» / «herak-herak» — пакет кальок, що повторюються по всьому EN-блогу.

**Типові повторювані помилки батчу 3 (UA):**
- «по» в значенні «з/за/на» — росизм (статті 21, 27, 29)
- «проекті/проекту»→«проєкті/проєкту» (новий правопис — статті 23, 24)
- Відсутні дефіси: `SEO просування`, `SEO трафіку`, `SEO робіт`, `On-page`, `бренд-нейм`
- «попасти под»→«потрапити під» (стаття 29)
- Інконсистенція `Google/google` і `SEO/СЕО`
- Російські слова у тілі UA-статті: `Клиент`, `этап`, `пессимізіровалі`

**Типові помилки EN:**
- Пропущені артиклі (a/the) — кейс на кожній статті
- Калькові терміни SEO/PPC: pessimize, link mass formation, gluing pages, position zero→focus on zero
- Поламаний синтаксис H1 (стаття 29)
- Непереведений сленг (стаття 27)

**Типові помилки RU:**
- Відсутні дефіси: `SEO выдаче`, `SEO трафика`, `SEO оптимизации`
- Кириличне написання акроніма «СЕО» замість «SEO»
- Узгодження множинного числа («должен быть» при множинних підметах)

---

## Загальна статистика всіх 3 батчів

- **30 статей** перевірено по 3 мовах
- **3 файли deliverable:** `batch-1-articles-1-10.md`, `batch-2-articles-11-20.md`, `batch-3-articles-21-30.md` + 3 `.docx`
- **Системні баги devs (зведено):**
  - Шаблон: TOC «Змicт» з лат. «i» (батч 1), `200ОК` з кир. «О» (батч 2-3)
  - URL: опечатка `mesyacs` (стаття 17), рос. транслітерація `yz-chego-sostoyt` (стаття 25)
  - H1≠slug: статті 14, 25
  - WPML fallback EN: статті 11, 12 (повна копія UA в EN)
  - Помилки прямо в H1: стаття 29 (UA + EN)
  - Непереведений сленг: стаття 27 EN
