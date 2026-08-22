# Реєстр рішень

Формат: `ID | Дата | Рішення | Статус (Proposed → Approved → Implementing → Completed)`

| ID | Дата | Рішення | Статус |
|---|---|---|---|
| M-001 | 2026-08-21 | Запустити робочий репозиторій `Website` для контенту й верстки Site24, працювати локально, комітити готові шматки в приватний GitHub-репозиторій | Approved |
| M-002 | 2026-08-21 | Імпортувати релевантний контент з архіву колеги (`Site24.zip`) у структуру репозиторію (`content/`, `assets/`, `layout-proposals/mockups/`); тримати матеріали інших клієнтів (BetterTone, LingoLondon) поза git-трекінгом у `_other-clients/` | Completed |
| M-003 | 2026-08-22 | Тестовий прогін `content-semantics-agent` на site24.com.ua (RU, catalog-режим, всі 5 пілорів): config.yml (пілари/ICP/money_pages/site_type/languages) підтверджено Катериною; результат — `D:\Claude\Clients\site24-seo-pipeline\clients\site24\` (поза цим репо). Виявлено ймовірну RU/UA канібалізацію цінової сторінки (48% показів сайту на одній сторінці) — не підтверджено, потребує GSC OAuth. Деталі — `logs/sessions/2026-08/2026-08-22-site24-semantics-test-run.md` | Completed |
| M-004 | 2026-08-22 | Додано дзеркальний UA-прогін тієї ж семантики (той самий день) — `clusters/ua-catalog-2026-08-22/`. Ручний live-триаж (curl + hreflang-перевірка) флагованої RU/UA цінової пари **виключив канібалізацію**: обидві сторінки живі, коректний hreflang, порівнянний розмір — 301/merge не застосовний. Розрив у показах (296K RU / 12.8K UA) реальний, причина ще не з'ясована (потрібен GSC OAuth). Попереднє формулювання "підозра на канібалізацію" виправлено в усіх артефактах пайплайну (config.yml, обидва cluster-plan.md/structure.md, обидва батчі BACKLOG.md). Звіт: `clients/site24/reports/triage-ru-ua-pricing-2026-08-22.md` | Completed |
