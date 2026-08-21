# Urban Steps. A Case Study of Problematic Analytics Setup for an Online Store on Shopify

**UA-source:** https://site24.sprava1.com/urban-steps-kejs-problemnogo-nalashtuvannya-analitiki-dlya-internet-magazina-na-platformi-shopify/
**EN-URL (target):** https://site24.sprava1.com/en/urban-steps-case-of-problematic-setup-of-analytics-for-an-online-store-on-the-shopify-platform/
**Published:** 28.09.2022
**Author:** Denys Ivanov
**Status:** Translated 2026-05-15 — replaces existing WPML fallback (UA body)

---

## Meta

- **Title (≤60ch):** Urban Steps — Shopify Analytics Setup Case Study | Site24
- **Description (≤155ch):** A case study of difficult analytics setup for a Shopify online store: connecting Google Analytics and Google Ads, and fixing eCommerce tracking issues.
- **OG title:** Urban Steps. Case Study of Problematic Analytics Setup for a Shopify Online Store
- **OG description:** A case study of difficult analytics setup for a Shopify online store and the working solution.
- **OG image:** /wp-content/uploads/2026/03/80b04ffe43c71e8370669be8d94ec1407aed5658-768x305.jpg
- **OG image alt:** Urban Steps — Shopify analytics setup case study

---

## Body

### Introduction

This case study is for PPC specialists and for specialists working with analytics systems.

**Given:** an online store on the Shopify platform.
**Task:** connect the Shopify account to Google Analytics, enable eCommerce, and set up shopping campaigns.

---

### What was done

1. We created a Google Ads account and a Google Analytics account.

2. We connected analytics and eCommerce inside the Shopify dashboard following the algorithm specified in the official help documentation.

3. We created a shopping campaign directly from the Shopify dashboard and launched the advertising. Data from the Shopify advertising dashboard is pulled into the Google Ads account automatically once they are connected.

---

### Problems and the next steps

1. We monitored the advertising. After a week we saw the following: traffic was coming in, Shopify analytics recorded the first few transactions — but the transactions were not being passed to Google Analytics.

2. We rechecked the linking of every account, the settings in Shopify and Universal Analytics, cross-referenced the official documentation, and read articles online — everything was set up correctly. We decided to additionally install GA4 via Google Tag Manager, because the version of Shopify in use did not yet allow GA4 to be installed directly.

3. We installed Google Tag Manager and GA4, configured eCommerce inside GA4 as well, and set up transaction tracking in the Google Ads dashboard.

4. At this stage we realised we could not go without support, because transactions were still not being recorded in any of the Google Analytics systems — even though sales were actually happening and those transactions were displaying correctly in the Shopify dashboard. We contacted Shopify Support, explained the situation in detail with screenshots, and very quickly got the reply that on the Shopify side everything was configured correctly and we needed to contact Google Support — the issue had to be on their side.

5. Then began a back-and-forth correspondence and consultations with Google Support, during which we tried to figure out the problem with Google specialists live in online sessions.

#### What we did:

- We tried connecting different script variants, placed on the "thank you" page, that pass transaction and product data. The changes were made in the Shopify dashboard: Settings → Checkout → Order status page → Additional scripts.

- We tried different eCommerce setup variants via GTM and ran test purchases. On the "thank you" page, using the data layer checker tool, we collected the current data for the Transaction, Value, and Items event parameters, then transferred them into the tag and watched the results — whether transactions would be recorded or not.

---

### We settled on the following configuration: Transaction code GA4 tag

In the end, we did manage to make data from Shopify analytics flow into Google Analytics and from there into the Google Ads account.

---

### Summary

- number of emails with Google Tech Support — 8
- number of online consultations with Google Tech Support — 6 (almost 5 hours in total)
- number of emails with Shopify Tech Support — 9
- total hours spent on this part of the work — more than 20

**As a result, analytics started working and we were able to fully resume analysing the ad campaign and working with the client.**

---

### Ready-to-use script

P.S. An example of the working script that finally let us pass data into Google Analytics:

```
<script>
window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
gtag('js', new Date());
gtag('config', 'G-XXXXXXXXXX');
{% if first_time_accessed %}
gtag("event", "purchase", {
transaction_id: "{{ order.order_number }}",
value: {{ total_price | times: 0.01 }},
tax: {{ tax_price | times: 0.01 }},
shipping: {{ shipping_price | times: 0.01 }},
currency: "{{ order.currency }}",
items: [
{% for line_item in line_items %}
{
item_id: "{{ line_item.product_id }}",
item_name: "{{ line_item.title | remove: "'" | remove: '"' }}",
currency: "{{ order.currency }}",
price: {{ line_item.original_price | times: 0.01 }},
quantity: {{ line_item.quantity }}
},
{% endfor %}
]
});
{% endif %}
</script>
```

---

### CTA inside the article

Grow faster with a custom SEO plan.

Let's review your SEO optimisation and see where you are right now.

Submit a request.
