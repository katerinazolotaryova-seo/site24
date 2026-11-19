"""Двомовний (UA/EN) договір SEO для crafttoryshop.com (Crafttory LLC, США), Виконавець — ФОП Золотарьова.

    python3 contracts/orders/2026-11-19_crafttoryshop.com_ua_en.py

Текст — той самий, що в україномовному договорі 2026-11-19_crafttoryshop.com.py
(шаблон templates/seo.docx), у дві колонки: ліворуч українська, праворуч англійська.
Нумерацію пунктів шаблону вирівняно (4.1, 8.2, розділ 12), додано п. 12.6 про пріоритет мов.
Контакт Вчасно Виконавця береться з entities/zolotaryova.yaml.
"""
from pathlib import Path

import docx
import yaml
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "Договір_SEO_crafttoryshop.com_11-2026_UA-EN.docx"

NUMBER = "191126/1"
SITE = "crafttoryshop.com"

# (тип, UA, EN): "h" — заголовок розділу, "p" — пункт
CONTRACT = [
    ("p",
     "Компанія Crafttory LLC (товариство з обмеженою відповідальністю, зареєстроване відповідно до законодавства штату Південна Кароліна, США), в особі власника Пархоменка Віталія (Vitalii Parkhomenko), що діє на підставі установчих документів компанії, з однієї сторони, іменований надалі «Замовник», та Фізична особа-підприємець Золотарьова Катерина Володимирівна, що діє на підставі свідоцтва про державну реєстрацію № 492659 від 28.05.2013, та є платником єдиного податку на підставі свідоцтва про сплату єдиного податку серії АВ № 342537 від 03.07.2013, з іншої сторони, іменований надалі «Виконавець», разом «Сторони», а кожна окремо «Сторона», уклали даний Договір (далі – Договір) про таке:",
     "Crafttory LLC (a limited liability company organized under the laws of the State of South Carolina, USA), represented by its owner Vitalii Parkhomenko, acting on the basis of the company's organizational documents, on the one part, hereinafter referred to as the “Customer”, and Individual Entrepreneur Kateryna Volodymyrivna Zolotarova, acting on the basis of state registration certificate No. 492659 dated 28.05.2013 and being a single tax payer under single tax certificate series AV No. 342537 dated 03.07.2013, on the other part, hereinafter referred to as the “Contractor”, together the “Parties” and each individually a “Party”, have entered into this Agreement (hereinafter the “Agreement”) as follows:"),
    ("h", "1. ТЛУМАЧЕННЯ ТЕРМІНІВ У ДОГОВОРІ", "1. DEFINITIONS"),
    ("p", "1.1. Виконавець - суб'єкт господарювання, який надає рекламні послуги.",
     "1.1. Contractor means a business entity that provides advertising services."),
    ("p", "1.2. Замовник - фізична або юридична особа, яка доручає виконання рекламних послуг Виконавцю.",
     "1.2. Customer means an individual or legal entity that engages the Contractor to perform advertising services."),
    ("p", "1.3. Дата старту проекту – дата, з якої фактично розпочалось просування та популяризація сайту в мережі Інтернет.",
     "1.3. Project Start Date means the date on which the promotion and popularization of the website on the Internet actually began."),
    ("p", "1.4. Договір – письмова угода між Замовником і Виконавцем про якість, терміни, ціну та інші умови, за яких надаються рекламні послуги.",
     "1.4. Agreement means a written agreement between the Customer and the Contractor on the quality, timing, price and other terms on which advertising services are provided."),
    ("p", "1.5. Мережа Інтернет - глобальна мережа, що об'єднує інформаційні ресурси, котрі належать різним юридичним і фізичним особам, та яка забезпечує передачу і прийом інформації між різними комп'ютерами.",
     "1.5. Internet means the global network that connects information resources owned by various legal entities and individuals and enables the transmission and receipt of information between computers."),
    ("p", "1.6. Образ сайту – зовнішній вигляд сайту, який гармонійно поєднує у собі художнє зображення та інформаційно-тематичне наповнення, а також є зручним у користуванні.",
     "1.6. Website Image means the appearance of the website that harmoniously combines visual design and informational content and is convenient to use."),
    ("p", "1.7. Оптимізація сайту - разові роботи по зміненню образу сайту та підвищенню релевантності (ваги сайту) в пошукових системах.",
     "1.7. Website Optimization means one-time work to change the Website Image and to increase its relevance (website authority) in search engines."),
    ("p", "1.8. Просування сайту - комплекс заходів, спрямований на підвищення рейтингу сайту, збільшення кількості відвідувачів та формування цільової аудиторії.",
     "1.8. Website Promotion means a set of measures aimed at improving the website's ranking, increasing the number of visitors and building a target audience."),
    ("p", "1.9. Пошукова система - це система, призначена для пошуку інформації в Інтернеті. Вона створена для впорядкування інформації та полегшення її пошуку.",
     "1.9. Search Engine means a system designed to search for information on the Internet, created to organize information and make it easier to find."),
    ("p", "1.10. Пошукове просування сайту - роботи по підвищенню ваги сайту у пошукових системах.",
     "1.10. Search Engine Promotion means work to increase the website's authority in search engines."),
    ("p", "1.11. Релевантність - це міра відповідності результатів пошуку завданню, поставленому в пошуковому запиті.",
     "1.11. Relevance means the degree to which search results match the task expressed in a search query."),
    ("p", "1.12. Сайт - сукупність інформаційних даних, об'єднаних по сенсу, що навігаційно і фізично знаходяться на одному сервері.",
     "1.12. Website means a set of information data, united by meaning, located navigationally and physically on one server."),
    ("p", "1.13. Якість популяризації – знаходження сайту серед перших десяти результатів пошуку у відповідній пошуковій системі.",
     "1.13. Popularization Quality means the website being among the first ten search results in the relevant search engine."),
    ("h", "2. ПРЕДМЕТ ДОГОВОРУ", "2. SUBJECT OF THE AGREEMENT"),
    ("p", "2.1. Замовник доручає, а Виконавець зобов'язується надати послуги щодо планування та реалізації проекту із популяризації сайту Замовника, а останній зобов'язується зробити оплату послуг та прийняти їх.",
     "2.1. The Customer engages the Contractor, and the Contractor undertakes to provide services for planning and implementing a project to popularize the Customer's website, and the Customer undertakes to pay for and accept the services."),
    ("h", "3. ПРАВА ТА ОБОВ'ЯЗКИ ВИКОНАВЦЯ", "3. RIGHTS AND OBLIGATIONS OF THE CONTRACTOR"),
    ("p", "3.1. Виконавець зобов'язується:", "3.1. The Contractor undertakes:"),
    ("p", "3.1.1. Якісно та своєчасно виконати послуги, визначені у предметі цього Договору в п. 2.1.",
     "3.1.1. To perform the services defined in clause 2.1 of this Agreement properly and on time."),
    ("p", "3.1.2. Приступити до надання послуг протягом двох робочих днів з моменту отримання першого платежу.",
     "3.1.2. To begin providing the services within two business days after receiving the first payment."),
    ("p", "3.1.3. Перелік робіт на кожний етап проекту визначається та письмово узгоджується між Виконавцем та Замовником в Додатках до цього Договору. Перелік робіт на наступний етап проекту Виконавець надсилає разом зі звітом по роботах та результатах попереднього періоду.",
     "3.1.3. The scope of work for each project stage is defined and agreed in writing between the Contractor and the Customer in the Appendices to this Agreement. The Contractor sends the scope of work for the next project stage together with the report on the work and results of the previous period."),
    ("p", "3.2. Виконавець має право:", "3.2. The Contractor has the right:"),
    ("p", f"3.2.1. Публікувати інформацію про хід, спосіб та результати надання Послуг Замовнику на особистих ресурсах без зазначення сайту, назви компанії та бренду Замовника {SITE}.",
     f"3.2.1. To publish information on the progress, methods and results of the Services provided to the Customer on its own resources without disclosing the Customer's website, company name or brand {SITE}."),
    ("h", "4. ПРАВА ТА ОБОВ'ЯЗКИ ЗАМОВНИКА", "4. RIGHTS AND OBLIGATIONS OF THE CUSTOMER"),
    ("p", "4.1. Замовник має право на перевірку ходу робіт по сайту:",
     "4.1. The Customer has the right to monitor the progress of work on the website:"),
    ("p", "4.1.1. На основі обов'язкової щомісячної звітності.", "4.1.1. Based on mandatory monthly reports."),
    ("p", "4.1.2. На запит Замовника Виконавець повинен надати звіт по виконаних роботах впродовж 48 годин.",
     "4.1.2. At the Customer's request, the Contractor shall provide a report on the work performed within 48 hours."),
    ("p", "4.2. Замовник зобов'язується:", "4.2. The Customer undertakes:"),
    ("p", "4.2.1. Сплатити за послуги Виконавця згідно цін та умов, що наведені в Розділі 5 даного Договору.",
     "4.2.1. To pay for the Contractor's services in accordance with the prices and terms set out in Section 5 of this Agreement."),
    ("h", "5. ЦІНА ПОСЛУГ, ВИЗНАЧЕННЯ ВАРТОСТІ ПОСЛУГ ТА ПОРЯДОК ЇХ ОПЛАТИ",
     "5. PRICE OF SERVICES, DETERMINATION OF COST AND PAYMENT PROCEDURE"),
    ("p", "5.1. Вартість послуг за Договором складає:", "5.1. The cost of services under the Agreement is as follows:"),
    ("p", "5.1.1. Ціна за послуги вказується у відповідному Додатку в залежності від плану та об'єму робіт. Оплата послуг Виконавця здійснюється у вигляді попередньої оплати у розмірі 100% грошових коштів кожного місяця протягом строку дії договору.",
     "5.1.1. The price of the services is specified in the relevant Appendix depending on the plan and scope of work. The Contractor's services are paid as a 100% prepayment each month during the term of the Agreement."),
    ("p", "5.1.2. Платежі, передбачені п. 5.1.1., Замовник має сплачувати протягом 5-ти робочих днів з моменту отримання рахунку-фактури.",
     "5.1.2. The Customer shall make the payments provided for in clause 5.1.1 within 5 business days after receiving the invoice."),
    ("p", "5.1.3. При відсутності оплати рахунку протягом 10 робочих днів з моменту отримання рахунку-фактури Виконавець має право розірвання цього Договору в односторонньому порядку.",
     "5.1.3. If an invoice is not paid within 10 business days after its receipt, the Contractor has the right to terminate this Agreement unilaterally."),
    ("h", "6. ВІДПОВІДАЛЬНІСТЬ СТОРІН", "6. LIABILITY OF THE PARTIES"),
    ("p", "6.1. У разі часткового невиконання Виконавцем п. 3.1.3. даного Договору (неповне виконання щомісячного завдання) частка коштів, які Виконавець повинен повернути Замовнику, дорівнює оціночній вартості кожного пункту щомісячного плану робіт. Разом з рахунком Виконавець надає щомісячний план робіт з розписаною по пунктах вартістю робіт, узгоджений представниками сторін.",
     "6.1. In case of partial non-performance by the Contractor of clause 3.1.3 of this Agreement (incomplete performance of the monthly task), the amount the Contractor shall refund to the Customer equals the estimated cost of each item of the monthly work plan. Together with the invoice, the Contractor provides a monthly work plan with the cost itemized by tasks, agreed by the Parties' representatives."),
    ("p", "6.2. За згодою сторін частка коштів, яка підлягає поверненню, може бути надана Замовнику у вигляді знижки до ціни послуги наступного періоду, визначеної у п. 5.1.1. договору. Рахунок-фактура, відповідно, буде виставлений Замовнику з урахуванням суми цієї знижки.",
     "6.2. By agreement of the Parties, the amount subject to refund may be provided to the Customer as a discount on the price of services for the next period determined under clause 5.1.1 of the Agreement. The invoice will then be issued to the Customer taking this discount into account."),
    ("p", "6.3. У випадку повного, часткового невиконання або несвоєчасного виконання умов п.п. 4.2.1, 5.1.3. даного Договору, Виконавець звільняється від фінансової відповідальності та зобов'язань перед Замовником. Протягом 2-х днів з моменту виявлення порушення Виконавець зупиняє надання послуг за даним Договором (послуги не надаються) та направляє письмове або електронне повідомлення Замовнику про даний факт. У випадку, якщо оплату послуг за договором не буде відновлено понад 3 місяці з дати направлення повідомлення, договір вважається розірваним і втрачає свою дію для Сторін.",
     "6.3. In case of full or partial non-performance or late performance of clauses 4.2.1, 5.1.3 of this Agreement, the Contractor is released from financial liability and obligations to the Customer. Within 2 days after the breach is discovered, the Contractor suspends the services under this Agreement (services are not provided) and sends the Customer a written or electronic notice thereof. If payment for the services is not resumed for more than 3 months from the date of the notice, the Agreement is deemed terminated and ceases to be effective for the Parties."),
    ("p", "6.4. У випадку, якщо Виконавець виявить порушення п. 4.2.1, він зобов’язаний протягом 24 годин із моменту виявлення направити Замовнику електронною поштою Акт порушення умов договору. При цьому сторони погоджуються, що направлення такого акту тягне за собою наслідки, передбачені п. 6.3.",
     "6.4. If the Contractor discovers a breach of clause 4.2.1, it shall send the Customer a Notice of Breach of the Agreement by e-mail within 24 hours after discovery. The Parties agree that sending such a notice entails the consequences provided for in clause 6.3."),
    ("h", "7. ПОРЯДОК ЗДАЧІ-ПРИЙМАННЯ ПОСЛУГ", "7. DELIVERY AND ACCEPTANCE OF SERVICES"),
    ("p", "7.1. Виконання послуг за Договором фіксується та підтверджується на основі Акту приймання-передачі наданих послуг, який щомісячно складається та підписується між Виконавцем та Замовником та становить невід'ємну частину даного Договору. Акт надається до 5-го числа кожного місяця за попередній, разом із Актом приймання-передачі наданих послуг Виконавець надає Звіт про виконані послуги за місяць та рахунок-фактуру на оплату послуг за наступний місяць.",
     "7.1. Performance of the services under the Agreement is recorded and confirmed by a Certificate of Acceptance of Services Rendered, drawn up and signed monthly by the Contractor and the Customer, which forms an integral part of this Agreement. The Certificate is provided by the 5th day of each month for the previous month; together with it the Contractor provides a Report on the services performed during the month and an invoice for the services of the following month."),
    ("p", "7.2. Досягнення результатів, зазначених у п. 3.1.3., відображається Виконавцем у відповідному Акті приймання-передачі наданих послуг.",
     "7.2. Achievement of the results specified in clause 3.1.3 is reflected by the Contractor in the relevant Certificate of Acceptance of Services Rendered."),
    ("p", "7.3. Замовник протягом 5-ти робочих днів з дня отримання Акту приймання-передачі наданих послуг повинен направити Виконавцю підписаний Акт приймання-передачі наданих послуг або мотивовану відмову від прийому робіт.",
     "7.3. Within 5 business days after receiving the Certificate of Acceptance of Services Rendered, the Customer shall send the Contractor the signed Certificate or a reasoned refusal to accept the work."),
    ("p", "7.4. У випадку відсутності письмових претензій з боку Замовника протягом терміну, визначеного в п. 7.3. Договору, послуги за даним Договором вважаються такими, що прийняті Замовником.",
     "7.4. If no written claims are received from the Customer within the period set out in clause 7.3 of the Agreement, the services under this Agreement are deemed accepted by the Customer."),
    ("h", "8. ФОРС-МАЖОРНІ ОБСТАВИНИ", "8. FORCE MAJEURE"),
    ("p", "8.1. Сторони звільняються від відповідальності за часткове чи повне невиконання або неналежне виконання зобов'язань за Договором, якщо вони є наслідком непереборної сили (пожежі, повені, землетрусу, стихійного лиха, військових дій, а також нестабільної роботи електронних систем Інтернету та пошукових систем, дій зі сторони державних органів і інших обставин непереборної сили). Якщо ці обставини безпосередньо вплинули на виконання Сторонами умов Договору, то виконання продовжується відповідно на строк, протягом якого діяли ці обставини.",
     "8.1. The Parties are released from liability for partial or complete non-performance or improper performance of their obligations under the Agreement if it results from force majeure (fire, flood, earthquake, natural disaster, military action, as well as unstable operation of Internet systems and search engines, actions of government authorities and other circumstances beyond the Parties' control). If such circumstances directly affected the Parties' performance of the Agreement, the time for performance is extended for the period during which such circumstances continued."),
    ("p", "8.2. Сторона, яка не може виконати зобов'язання за Договором, повинна письмово не пізніше п'яти робочих днів повідомити іншу Сторону про настання форс-мажору, припинення виконання своїх зобов'язань із проектом врегулювання взаємних зобов'язань.",
     "8.2. A Party unable to perform its obligations under the Agreement shall notify the other Party in writing within five business days of the occurrence of force majeure and the suspension of its obligations, with a proposal for settling mutual obligations."),
    ("p", "8.3. Неповідомлення або несвоєчасне повідомлення про настання чи припинення форс-мажорних обставин позбавляє Сторону права на них посилатися.",
     "8.3. Failure to notify, or late notification, of the occurrence or cessation of force majeure deprives the Party of the right to rely on it."),
    ("h", "9. КОНФІДЕНЦІЙНІСТЬ", "9. CONFIDENTIALITY"),
    ("p", "9.1. Сторони визнають, що вся інформація, яка прямо або опосередковано відноситься до даного Договору, рівно як і інформація про діяльність кожної із Сторін або про діяльність будь-якої третьої сторони, яка має відношення до Сторін, яка не є загальнодоступною і яка стала відомою Сторонам в результаті укладення та/або виконання даного Договору, вважається конфіденційною. Крім того, для цілей цього Договору конфіденційною вважається інформація, яка є секретною в тому розумінні, що вона в цілому або у певній формі і сукупності її складових є невідомою та легкодоступною для осіб, які зазвичай мають справу з даним видом інформації, у зв’язку з цим має комерційну цінність і була предметом адекватних існуючим обставинам заходів, які вживаються Сторонами відносно охорони її секретності. Також до конфіденційної інформації належить інша інформація, яка не складає комерційну таємницю у відповідності з законодавством України, однак у відношенні якої Сторонами було заявлено про те, що вона є конфіденційною.",
     "9.1. The Parties acknowledge that all information directly or indirectly related to this Agreement, as well as information about the activities of either Party or of any third party related to the Parties, which is not publicly available and which became known to the Parties as a result of concluding and/or performing this Agreement, is confidential. In addition, for the purposes of this Agreement, confidential information includes information that is secret in the sense that, as a whole or in a certain form and combination of its components, it is unknown to and not readily accessible by persons who normally deal with such information, has commercial value for that reason, and has been subject to measures reasonable under the circumstances taken by the Parties to protect its secrecy. Confidential information also includes other information that does not constitute a trade secret under the laws of Ukraine but which the Parties have declared to be confidential."),
    ("p", "9.2. Якщо Сторони не домовились про інше, то вони зобов’язуються не розголошувати та не розкривати конфіденційну інформацію третім особам та не використовувати її в будь-яких цілях інакше, ніж в цілях належного виконання Договору, як протягом строку його дії, так і після його припинення. Сторони зобов’язуються зі своєї сторони обмежити коло осіб, які матимуть доступ до такої інформації, кількістю, розумно необхідною для належного виконання умов Договору.",
     "9.2. Unless otherwise agreed by the Parties, they undertake not to divulge or disclose confidential information to third parties and not to use it for any purpose other than the proper performance of the Agreement, both during its term and after its termination. Each Party undertakes to limit the number of persons with access to such information to the number reasonably necessary for the proper performance of the Agreement."),
    ("p", "9.3. Сторони зобов’язуються протягом строку дії Договору, а також протягом трьох років після закінчення строку його дії ні при яких обставинах не розголошувати конфіденційну інформацію і забезпечувати її захист. Конфіденційна інформація може бути розкрита Стороною на підставі законної вимоги органу державної влади або рішення суду, при цьому Сторона, що розкриває конфіденційну інформацію, зобов’язана негайно повідомити іншу Сторону про факт отримання вимоги про надання такої інформації.",
     "9.3. The Parties undertake, during the term of the Agreement and for three years after its expiry, under no circumstances to disclose confidential information and to ensure its protection. Confidential information may be disclosed by a Party on the basis of a lawful demand of a government authority or a court decision, in which case the disclosing Party shall immediately notify the other Party of the receipt of such demand."),
    ("p", "9.4. Сторона, що порушує умови Договору щодо розкриття конфіденційної інформації, несе відповідальність відповідно до Договору та чинного законодавства України, а також зобов’язана відшкодувати збитки, що були завдані внаслідок розкриття конфіденційної інформації.",
     "9.4. A Party that breaches the Agreement with respect to disclosure of confidential information is liable in accordance with the Agreement and the applicable laws of Ukraine and shall compensate the losses caused by such disclosure."),
    ("h", "10. ВИРІШЕННЯ СПОРІВ", "10. DISPUTE RESOLUTION"),
    ("p", "10.1. Всі розбіжності та спори, пов'язані з виконанням даного Договору, вирішуються Сторонами шляхом переговорів, та в разі їх не вирішення - в суді.",
     "10.1. All disagreements and disputes related to the performance of this Agreement shall be resolved by the Parties through negotiations and, failing that, in court."),
    ("h", "11. СТРОК ДІЇ ДОГОВОРУ", "11. TERM OF THE AGREEMENT"),
    ("p", "11.1. Договір вступає в силу з моменту його підписання та виконання п. 5.1.2, у випадку невиконання зазначеного пункту даний Договір вважається неукладеним.",
     "11.1. The Agreement enters into force upon its signing and fulfillment of clause 5.1.2; if that clause is not fulfilled, this Agreement is deemed not concluded."),
    ("p", "11.2. Термін дії Договору складає до 31.12.2027 з моменту отримання першої попередньої оплати на розрахунковий рахунок Виконавця, з можливістю припинити роботи в будь-який момент.",
     "11.2. The Agreement is valid until 31.12.2027 from the receipt of the first prepayment to the Contractor's bank account, with the possibility to stop the work at any time."),
    ("h", "12. ЗАКЛЮЧНІ ПОЛОЖЕННЯ", "12. FINAL PROVISIONS"),
    ("p", "12.1. Зміни та доповнення до даного Договору вносяться тільки за взаємною згодою сторін.",
     "12.1. Amendments and additions to this Agreement are made only by mutual consent of the Parties."),
    ("p", "12.2. Зміни і доповнення оформляються окремим письмовим документом, що є невід'ємною частиною Договору.",
     "12.2. Amendments and additions are executed as a separate written document, which forms an integral part of the Agreement."),
    ("p", "12.3. При виконанні даного Договору сторони керуються умовами Договору та чинним законодавством України.",
     "12.3. In performing this Agreement, the Parties are guided by its terms and the applicable laws of Ukraine."),
    ("p", "12.4. Договір складений в двох примірниках, по одному для кожної із сторін, які мають однакову юридичну силу.",
     "12.4. The Agreement is executed in two counterparts, one for each Party, both having equal legal force."),
    ("p", "12.5. Сторони домовилися про те, що з метою виконання умов Договору будуть здійснювати документообіг у формі електронних документів для підтвердження описаних у них господарських операцій із використанням системи ME.DOC або ВЧАСНО. Формування електронних документів Сторони здійснюють із урахуванням положень законів України «Про електронні документи та електронний документообіг», «Про електронні довірчі послуги» та інших чинних нормативно-правових актів України. Електронні документи, які Сторони відправили та підписали з використанням КЕП (удосконалений електронний підпис, який створюється з використанням засобу кваліфікованого електронного підпису і базується на кваліфікованому сертифікаті відкритого ключа), мають повну юридичну силу, породжують права та обов’язки для Сторін, можуть бути представлені до суду в якості належних доказів та визнаються рівнозначними документам, що складаються на паперовому носії. Підпис Сторони на електронному документі означає підтвердження участі такої Сторони в оформленні електронного документа. Підтвердження передання електронних документів (відправлення, отримання тощо) вважається легітимним підтвердженням фактичного приймання-передачі таких документів уповноваженими особами Сторін і не вимагає додаткового доказування. Датою електронного документу є дата його створення (зазначена в преамбулі) незалежно від дати його підписання Сторонами.",
     "12.5. The Parties have agreed that, for the purpose of performing the Agreement, they will exchange documents in electronic form to confirm the business transactions described therein, using the ME.DOC or VCHASNO system. The Parties create electronic documents in accordance with the Laws of Ukraine “On Electronic Documents and Electronic Document Management”, “On Electronic Trust Services” and other applicable regulations of Ukraine. Electronic documents sent and signed by the Parties with a QES (an advanced electronic signature created using a qualified electronic signature creation device and based on a qualified public key certificate) have full legal force, create rights and obligations for the Parties, may be submitted to court as admissible evidence and are deemed equivalent to paper documents. A Party's signature on an electronic document confirms that Party's participation in executing the document. Confirmation of transmission of electronic documents (sending, receipt, etc.) is deemed legitimate confirmation of the actual delivery and acceptance of such documents by the Parties' authorized persons and requires no further proof. The date of an electronic document is the date of its creation (stated in the preamble), regardless of the date it is signed by the Parties."),
    ("p", "12.6. Договір складено українською та англійською мовами. У разі розбіжностей між текстами переважну силу має текст українською мовою.",
     "12.6. The Agreement is made in Ukrainian and English. In case of any discrepancy between the texts, the Ukrainian text shall prevail."),
]

PLAN = [
    ("Збір семантичного ядра на пріоритетні категорії - до 60 груп, англійською, ринок США",
     "Keyword research for priority categories - up to 60 keyword groups, in English, US market"),
    ("Формування ТЗ на допрацювання структури сайту - які сторінки потрібно додати на сайт",
     "Technical specification for improving the site structure - which pages need to be added to the site"),
    ("Написання мета-тегів по зібраній семантиці",
     "Writing meta tags based on the collected keywords"),
    ("Оптимізація шаблонних мета-тегів для сторінок товарів",
     "Optimization of template meta tags for product pages"),
    ("Формування ТЗ на функціонал фільтрації (сторінки за брендом, кольором, способом нанесення - лише там, де є пошуковий попит)",
     "Technical specification for filtering functionality (pages by brand, color, decoration method - only where there is search demand)"),
    ("Формування ТЗ на написання / оптимізацію текстів сторінок - 10 текстів (на основі зібраної семантики та аналізу конкурентів)",
     "Technical specifications for writing / optimizing page copy - 10 texts (based on the collected keywords and competitor analysis)"),
    ("Технічний SEO аудит сайту. Формування ТЗ на впровадження",
     "Technical SEO audit of the website. Technical specification for implementation"),
    ("Аналіз видимості CraftTory і конкурентів в AI сервісах (ChatGPT, Perplexity, AI Overview). Аудит карток топ-товарів і товарних фідів Google і Microsoft Merchant Center",
     "Analysis of CraftTory's and competitors' visibility in AI services (ChatGPT, Perplexity, AI Overview). Audit of top product pages and Google and Microsoft Merchant Center product feeds"),
    ("Аналіз EEAT факторів (Experience, Expertise, Authoritativeness, Trustworthiness) конкурентів. Формування ТЗ на допрацювання EEAT (відгуки, кейси клієнтів, сторінка про компанію, процес нанесення)",
     "Analysis of competitors' EEAT factors (Experience, Expertise, Authoritativeness, Trustworthiness). Technical specification for improving EEAT (reviews, client case studies, About page, decoration process)"),
]

CONDITIONS = [
    ("Вартість Послуг (робіт), що зазначені в цьому Додатку, складає 780 (сімсот вісімдесят) доларів США, звіт за якими надається після виконання Додатку 1 та/або за запитом Замовника.",
     "The cost of the Services (work) specified in this Appendix is USD 780 (seven hundred eighty US dollars); the report on them is provided after completion of Appendix 1 and/or at the Customer's request."),
    ("Оплата послуг Виконавця здійснюється у вигляді попередньої оплати у розмірі 100% грошових коштів на підставі виставленого Виконавцем рахунку протягом 5 (п’яти) банківських днів з дати підписання Сторонами цього Додатку та виставлення рахунку.",
     "The Contractor's services are paid as a 100% prepayment on the basis of the Contractor's invoice within 5 (five) banking days after the Parties sign this Appendix and the invoice is issued."),
    ("Термін надання послуг (виконання робіт), що зазначений в цьому Додатку, складає до 5 (п’яти) тижнів з моменту внесення передоплати відповідно до п. 5.1. Договору.",
     "The term for providing the services (performing the work) specified in this Appendix is up to 5 (five) weeks from the prepayment under clause 5.1 of the Agreement."),
    ("Цей Додаток складений у двох екземплярах, що мають однакову юридичну силу, по одному для кожної зі Сторін.",
     "This Appendix is executed in two counterparts of equal legal force, one for each Party."),
]

# Реквізити Виконавця англійською; UA-рядки беруться з entities/zolotaryova.yaml
EXECUTOR_EN = {
    "ФОП Золотарьова Катерина Володимирівна": "Individual Entrepreneur Kateryna Zolotarova",
    "Свідоцтво № 492659": "Certificate No. 492659",
    "Від: «28» травня 2013 р.": "dated 28 May 2013",
    "Свідоцтво про сплату єдиного податку серія АВ № 342537": "Single tax certificate series AV No. 342537",
    "Від 3 липня 2013 р.": "dated 3 July 2013",
    "ІПН: 3178815880": "Tax ID: 3178815880",
    "Р/р UA073510050000026005450205200 в АКІБ «Укрсіббанк»":
        "Account UA073510050000026005450205200 at JSCB UKRSIBBANK",
    "МФО: 351005": "Bank code: 351005",
}
CUSTOMER = [
    ("Crafttory LLC", "Crafttory LLC"),
    ("ТОВ, штат Південна Кароліна, США", "Limited Liability Company, South Carolina, USA"),
    ("Адреса: 2218 Magnolia Manor Ln, Ste 206, Fort Mill, SC 29708, USA",
     "Address: 2218 Magnolia Manor Ln, Ste 206, Fort Mill, SC 29708, USA"),
    ("EIN: ____________________", "EIN: ____________________"),
    ("Банк: ____________________", "Bank: ____________________"),
    ("Рахунок: ____________________", "Account: ____________________"),
    ("Тел.: +1 (980) 202-4393", "Phone: +1 (980) 202-4393"),
    ("E-mail: sales@crafttoryshop.com", "E-mail: sales@crafttoryshop.com"),
]

FONT, SIZE = "Times New Roman", Pt(10)


def executor_lines():
    ent = yaml.safe_load((ROOT / "entities" / "zolotaryova.yaml").read_text(encoding="utf-8"))
    lines = []
    for ua in ent["requisites"]:
        en = EXECUTOR_EN.get(ua) or ua.replace("Вчасно", "Vchasno")
        lines.append((ua, en))
    return lines


def no_borders(table):
    borders = OxmlElement("w:tblBorders")
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:val"), "nil")
        borders.append(el)
    table._tbl.tblPr.append(borders)


def write(target, text, bold=False, align=None, size=SIZE, first=False, after=Pt(3)):
    p = target.paragraphs[0] if first and target.paragraphs else target.add_paragraph()
    p.paragraph_format.space_after = after
    if align is not None:
        p.alignment = align
    run = p.add_run(text)
    run.bold, run.font.size, run.font.name = bold, size, FONT
    return p


def two_cols(doc, rows):
    """rows: [(ua, en, bold, align)] — по рядку таблиці на пункт, щоб тексти йшли поруч."""
    t = doc.add_table(rows=0, cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    no_borders(t)
    for ua, en, bold, align in rows:
        cells = t.add_row().cells
        for c, text in zip(cells, (ua, en)):
            c.width = Cm(8.7)
            write(c, text, bold=bold, align=align, first=True)
    return t


def requisites(doc):
    head = write(doc, "ЮРИДИЧНІ АДРЕСИ ТА РЕКВІЗИТИ СТОРІН / LEGAL ADDRESSES AND DETAILS OF THE PARTIES",
                 bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    head.paragraph_format.keep_with_next = True
    # рядок 0 — назви сторін, 1 — реквізити, 2 — підписи (окремий рядок тримає їх на одному рівні)
    t = doc.add_table(rows=3, cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    no_borders(t)
    parties = (("ВИКОНАВЕЦЬ / CONTRACTOR", executor_lines(), "Золотарьова К.В. / K. Zolotarova"),
               ("ЗАМОВНИК / CUSTOMER", CUSTOMER, "Vitalii Parkhomenko"))
    for col, (title, lines, sig) in enumerate(parties):
        cells = [row.cells[col] for row in t.rows]
        for c in cells:
            c.width = Cm(8.7)
        write(cells[0], title, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, first=True)
        for k, (ua, en) in enumerate(lines):
            text = ua if ua == en else f"{ua}\n{en}"
            write(cells[1], text, bold=(k == 0), first=(k == 0), after=Pt(2))
        write(cells[2], "", first=True)
        write(cells[2], f"____________________/{sig}", bold=True)
    # таблиця не розривається між сторінками
    for row in t.rows:
        tr_pr = row._tr.get_or_add_trPr()
        tr_pr.append(OxmlElement("w:cantSplit"))
        for c in row.cells:
            for p in c.paragraphs:
                p.paragraph_format.keep_with_next = True


def build():
    doc = docx.Document()
    sec = doc.sections[0]
    sec.page_height, sec.page_width = Cm(29.7), Cm(21)
    sec.left_margin = sec.right_margin = Cm(1.7)
    sec.top_margin = sec.bottom_margin = Cm(1.7)
    style = doc.styles["Normal"]
    style.font.name, style.font.size = FONT, SIZE

    write(doc, f"Договір №{NUMBER} / Agreement No. {NUMBER}", bold=True,
          align=WD_ALIGN_PARAGRAPH.CENTER, size=Pt(13), first=True)
    write(doc, "про надання послуг з інформатизації веб-проектів / on the provision of web project informatization services",
          bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)

    rows = [("м. Київ, «19» листопада 2026 р.", "Kyiv, 19 November 2026", True, None)]
    for kind, ua, en in CONTRACT:
        if kind == "h":
            rows.append((ua, en, True, WD_ALIGN_PARAGRAPH.CENTER))
        else:
            rows.append((ua, en, False, WD_ALIGN_PARAGRAPH.JUSTIFY))
    two_cols(doc, rows)
    write(doc, "")
    requisites(doc)

    # Додаток 1 — з нової сторінки
    write(doc, "").add_run().add_break(WD_BREAK.PAGE)
    write(doc, "Додаток 1 / Appendix 1", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, size=Pt(12))
    write(doc, f"до Договору №{NUMBER} від «19» листопада 2026 р. / to Agreement No. {NUMBER} dated 19 November 2026",
          bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    rows = [("І. План робіт на перший період", "I. Work plan for the first period", True, None)]
    rows += [(f"{k}. {ua}", f"{k}. {en}", False, None) for k, (ua, en) in enumerate(PLAN, 1)]
    rows.append(("ІІ. Умови надання послуг (виконання робіт).", "II. Terms of service (performance of work).", True, None))
    rows += [(f"{k}. {ua}", f"{k}. {en}", False, None) for k, (ua, en) in enumerate(CONDITIONS, 1)]
    two_cols(doc, rows)
    write(doc, "")
    requisites(doc)

    doc.save(OUT)
    print(OUT)


if __name__ == "__main__":
    build()
