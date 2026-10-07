---
name: invoice
description: Generate a Ukrainian рахунок-фактура (invoice) .xlsx from a fixed template, fill in service/amount/date, optionally convert USD to UAH at PrivatBank's commercial rate, and upload it to the user's Google Drive "Рахунки" folder. Use when the user asks to create/generate a new invoice/рахунок, or references this skill.
---

# Invoice generator

Generates invoices matching the layout of `template.xlsx` (originally modeled
after a real рахунок-фактура for ФОП Турчихін). Keep using this exact
template/flow unless the user asks to change the layout.

## Files in this skill

- `template.xlsx` — the base workbook (sheet name is `"Счет "` — note the
  trailing space, keep it exact). Requisites block (A1:C5) is already
  formatted left-aligned, Times New Roman 11 — do not change this formatting
  unless asked.
- `requisites.json` — named profiles of "постачальник" details (ЄДРПОУ,
  IBAN, bank, director signature). Currently only `turchykhin` exists. When
  the user gives you a new set of requisites, add a new named entry here
  (ask them for a short key name) instead of overwriting the existing one.
- `generate_invoice.py` — fills the template and recalculates formulas.

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
     --service "<full service text, e.g. 'GEO консультація для frigat.net'>" \
     --amount-usd <amount> --rate sale \
     --date <YYYY-MM-DD> --suffix <n> \
     --requisites <profile> \
     --out-dir <scratch dir>
   ```
   Use `--amount-uah <amount>` instead of `--amount-usd`/`--rate` if the
   user gives a fixed UAH amount directly.
   - `--rate` is `sale` (курс продажу) by default — this is what was used
     the first time this skill was derived. Only use `buy` if the user
     explicitly asks for it.
   - The invoice number is always `DDMMYY/<suffix>` from `--date`.
   - Output filename is `рахунок-<site>-<service>-<DD.MM.YYYY>.xlsx` (the
     literal `для <site>` substring is stripped out of the service text
     for the filename only, not from the cell content).
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

## Adding a new requisites profile

When the user gives you a new "реквізити" (ЄДРПОУ, IBAN, bank name, bank
MFO, director signature line), add it to `requisites.json` under a new short
key (e.g. the FOP's surname), without touching existing entries. Then pass
`--requisites <key>` to use it.
