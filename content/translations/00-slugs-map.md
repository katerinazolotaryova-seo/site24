# Site24 — URL-slug мапа (UA / EN / RU)

**Наша робота:** для кожної з 15 сторінок запропонувати читабельний slug в кожній з 3 мов.

**Не наша робота:** обрати схему сайту (папки `/en/` vs субдомени vs окремі домени), налаштувати hreflang, sitemap, перемикач мов — це вирішує розробник Site24.

**Стан UA-slug-ів:** ✅ підтверджено після екстракції 2026-05-14 (Phase 2).

---

## Slug-мапа 15 сторінок

| # | Сторінка | UA-slug (фактичний) | EN-slug | RU-slug |
|---|---|---|---|---|
| 01 | Головна | `/` | `/` (homepage) | `/` (homepage) |
| 02 | SEO просування | `/seo-prosuvannya` | `seo` | `seo-prodvizhenie` |
| 03 | PPC реклама | `/kontekstna-reklama` | `ppc` | `ppc-reklama` |
| 04 | Кейси | `/tag/kejsi/` ❌ → пропоную `/cases/` (CPT) | `case-studies` | `keysy` |
| 05 | Контакти | `/kontakty/` | `contact` | `kontakty` |
| 06 | Про нас | `/pro-nas/` | `about` | `o-nas` |
| 07 | Відгуки | `/all-testimonials/` ⚠️ нечитабельний | `reviews` | `otzyvy` |
| 08 | Блог | `/blog/` | `blog` | `blog` |
| 09 | SERM | `/serm-upravlinnya-reputatsiyeyu-v-poshukovyh-systemah/` ⚠️ задовгий | `serm` | `serm` |
| 10 | Аудит PPC | `/audit-ppc-reklamy/` | `ppc-audit` | `audit-ppc` |
| 11 | Тарифи / Ціни | `/czini-na-prosuvannya-ta-rozkrutku-sajtiv/` ❌ → `/tsiny/` | `pricing` | `tseny` |
| 12 | Семантика | `/zbir-semantychnogo-yadra/` | `keyword-research` | `semantika` |
| 13 | SEO-аудит | `/tehnichnij-seo-audit-sajtu/` | `seo-audit` | `seo-audit` |
| 14 | AI-просування | `/ai-prosuvannya/` | `ai-search` | `ai-prodvizhenie` |
| 15 | Закордонне просування | `/prosuvannya-zarubizhnih-sajtiv/` | `international-seo` | `zarubezhnoe-prodvizhenie` |

---

## Проблемні UA-slug-и (рекомендації для розробника)

### Критичні (треба 301-редірект у будь-якому разі)

1. **`/czini-na-prosuvannya-ta-rozkrutku-sajtiv/`** → `/tsiny/`
   *Нечитабельний транслітерат («czini» замість «tsiny»), SEO-критичне для агенції що продає SEO. Поточний URL — 53 символи з беззмістовним початком, рекомендований — 8 символів.*

2. **`/tag/kejsi/`** → `/cases/` (новий CPT з фільтрами)
   *Зараз це WordPress тегова архівна сторінка з блог-сайдбаром і шапкою «Головна / Кейси Site24». Технічно невірно для розділу «Кейси». Потрібен окремий Custom Post Type.*

### Бажано виправити (не критично, але SEO-неоптимально)

3. **`/all-testimonials/`** → пропоную `/vidhuky/`
   *«all-testimonials» — змішує EN і UA, не SEO-friendly для UA-версії.*

4. **`/serm-upravlinnya-reputatsiyeyu-v-poshukovyh-systemah/`** → пропоную `/serm/`
   *Поточний URL — 53 символи, надмірно довгий. Просто `/serm/` — і коротко, і SEO-чисто.*

5. **Breadcrumb-баг на блозі:** на сторінці `/blog/` лінк «Головна» у breadcrumbs веде на `/seo-prosuvannya` замість `/`. Системний баг — не текстова правка, виправляє розробник.

---

## Що передаємо розробнику

- Цей файл як мапу slug-ів (UA-фактичні + запропоновані EN/RU)
- 2 обов'язкові 301-редіректи (czini, tag/kejsi)
- 3 бажані виправлення UA-slug-ів (all-testimonials, serm, breadcrumb)
- Решта рішень по схемі URL (папки vs субдомени), hreflang, sitemap, перемикач мов — на розсуд розробника
