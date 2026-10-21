---
name: invoice
description: Generate a Ukrainian рахунок-фактура (invoice) .xlsx from a fixed template, fill in service/amount/date, optionally convert USD to UAH at PrivatBank's commercial rate, and upload it to the user's Google Drive "Рахунки" folder. Use when the user asks to create/generate a new invoice/рахунок, or references this skill.
---

# Invoice generator

Generates invoices from one of several fixed templates — one per supplier
(постачальник). Different suppliers' real invoices have different cell
layouts (not just different values), so each requisites profile in
`requisites.json` names both its own template file and a "layout" (a cell
map in `generate_invoice.py`'s `LAYOUTS` dict). Keep using the exact
template/layout for a given supplier unless the user asks to change it.

Known profiles so far:
- `turchykhin` (default) — `template.xlsx`, layout `turchykhin_v1`.
- `zolotaryova` — `template_zolotaryova.xlsx`, layout `zolotaryova_v1`
  (different requisites fields: no ЄДРПОУ, instead has ІПН + адреса +
  телефони; different row positions for everything).

## Files in this skill

- `template.xlsx`, `template_zolotaryova.xlsx`, ... — one base workbook per
  supplier (sheet name is always `"Счет "` — note the trailing space, keep
  it exact). Don't change a template's formatting unless the user asks to —
  it should match the real example invoice it was derived from.
- `requisites.json` — named profiles of "постачальник" details, each with a
  `"layout"` and `"template"` key picking which `LAYOUTS` entry / file to
  use, plus whatever fields that layout needs (see `generate_invoice.py`'s
  `LAYOUTS["<name>"]["requisite_cells"]` for the exact field names it reads).
  When the user gives you a new set of requisites, add a new named entry
  here (ask for a short key name, e.g. the FOP's surname) without touching
  existing entries — see "Adding a new requisites profile / supplier" below.
- `generate_invoice.py` — fills the right template per-profile and
  recalculates formulas.

## Workflow

1. Collect from the user (or infer from their message): site/client name,
   service description, amount (USD or a fixed UAH amount), date (defaults
   to today), invoice suffix (defaults to `1` — the part after `/` in the
   invoice number; ask only if the user says it's not `1`), and which
   requisites profile to use (defaults to `turchykhin`).
2. Run:
   ```
   python3 .claude/skills/invoice/generate_invoice.py \
     --site <site> \
     --amount-uah <amount> \
     --date <YYYY-MM-DD> --suffix <n> \
     --requisites <profile> \
     --out-dir <scratch dir>
   ```
   Use `--amount-usd <amount> --rate sale` instead of `--amount-uah` if the
   user gives the amount in USD.
   - `--service` defaults to `"Консультування з питань інформатизації: SEO
     просування сайту <site>"` — leave it out unless the user asks for a
     different service text (e.g. a GEO consultation instead of SEO
     promotion), then pass `--service "..."` explicitly.
   - `--unit` defaults to `"місяць"` — leave it out unless told otherwise.
   - `--rate` is `sale` (курс продажу) by default — this is what was used
     the first time this skill was derived. Only use `buy` if the user
     explicitly asks for it.
   - The invoice number is always `DDMMYY/<suffix>` from `--date`.
   - Output filename is `рахунок_<service_code>_<site>_<MM-YYYY>.xlsx`.
     `service_code` auto-detects `SEO`/`GEO` from `--service`; pass
     `--service-code` explicitly if the service doesn't contain either (the
     fallback otherwise slugs the full `--service` text, which gets long).
3. Show the generated file to the user for review (`SendUserFile`) before
   uploading anywhere, unless they've already told you to skip that step
   for routine invoices.
4. If the user wants it uploaded to Google Drive:
   - Make sure the `Google Drive` connector is enabled (`ListConnectors`).
   - Search for a folder named "Рахунки" (`mcp__Google_Drive__search_files`
     with `title = 'Рахунки' and mimeType = 'application/vnd.google-apps.folder'`).
     Create it if missing.
   - Upload with `mcp__Google_Drive__create_file`, `contentMimeType:
     application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`,
     `disableConversionToGoogleType: true`, and `base64Content` = the file's
     base64 (`base64 -w0 file.xlsx`).
   - **Verify the upload byte-for-byte**: download it back with
     `mcp__Google_Drive__download_file_content` and compare against the
     local file (e.g. decode both to disk and `cmp`, or compare md5). Base64
     blobs this long are easy to mistype when passed through a tool call —
     always verify, never assume the upload matches.

## Amount-in-words

`generate_invoice.py` spells out the UAH amount in words itself
(`amount_in_words_uah`), with correct Ukrainian grammatical gender/number
agreement (e.g. "Одна гривня", "Двадцять одна тисяча", "П'ять гривень").
Kopecks are written as digits + a declined "копійка/копійки/копійок", matching
the original template's style. You should not need to write this by hand —
if the wording looks off for an edge case, fix the `number_to_words_uk` /
`amount_in_words_uah` functions rather than hardcoding text.

## Adding a new requisites profile / supplier

If the user gives you new requisites for a **supplier (постачальник) already
in `requisites.json`**, or a brand-new supplier whose invoice uses an
**existing layout's exact cell positions**, just add/edit the entry in
`requisites.json` with that layout's required fields (see the matching
`LAYOUTS[...]["requisite_cells"]` keys) — no code change needed.

If the user gives you an **example invoice for a new supplier** (a different
real рахунок, not just different values), check whether its cell layout
actually differs from the existing ones (row numbers, extra fields like
address/phone, missing ЄДРПОУ, etc. — inspect with openpyxl, don't assume):
1. Copy the example file into this directory as a new `template_<name>.xlsx`
   (keep its original formatting — don't "fix" it unless asked).
2. Add a new entry to `LAYOUTS` in `generate_invoice.py` with that template's
   exact cell coordinates for every field (`requisite_cells`, `invoice_no_cell`,
   `payer_cell`, the item row, the totals block, `date_cell`, ...).
3. Add the new profile to `requisites.json` with `"layout"` and `"template"`
   pointing at what you just added, plus the actual requisites values.
4. Test both the new and an existing profile end-to-end before committing,
   to make sure the shared code path (`main()` in `generate_invoice.py`)
   still works for both.
