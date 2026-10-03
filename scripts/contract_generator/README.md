# contract_generator

Generates a filled-in PDF of the Aimo charging-services agreement
(`Avtal Laddningstjänster`) from structured data, reproducing the original
Word template's header banner, footer icon, fonts and table styling exactly
- because it *is* the original template, with only its content-control
placeholders replaced before exporting to PDF.

## How it works

`template/Avtal_Aimo_Charge_Fee_to_Landlord_v1.2.docx` is the source
template. Its fillable spots are native Word content controls (not plain
`XXX` text), so `generate_contract.py` edits `word/document.xml` directly:
for each field in `fields.py` it finds the corresponding control (by
position, `sdt_index`) and replaces its text - or, for checkboxes, swaps
`☐`/`☒` and flips the control's internal checked state. The result is
re-zipped into a `.docx` and converted to PDF with LibreOffice, so every
other part of the document (header, footer, logo, table borders, fonts) is
untouched pixel-for-pixel.

## No install at all: the web version

**https://claude.ai/artifact/MiAnE7LKoJYhnEtvUGK53z**

Same form, running entirely in your browser - no Python, no LibreOffice,
nothing to install. See `web/README.md` for how it works.

## Setup (desktop versions below)

```bash
pip install -r requirements.txt
```

The `--out` (PDF) option additionally needs LibreOffice installed for the
export step (`sudo apt-get install -y libreoffice-writer`, or the desktop
installer from libreoffice.org). If LibreOffice isn't available - e.g. it's
blocked by IT policy - skip `--out` entirely and use `--keep-docx` instead;
see "No LibreOffice?" below.

## Easiest way: the fill-in-the-boxes form

No YAML editing required - `contract_form.py` opens a window with one
labeled box per field, grouped and ordered to match the contract's own
sections, with radio buttons for the either/or choices (public/private
chargers, billing cadence) and a checkbox for the SIM-card add-on. It uses
only Python's built-in `tkinter`, so nothing beyond `pip install -r
requirements.txt` is needed:

```bash
python3 contract_form.py
```

Fill in the boxes, click **"Generera avtal..."**. Anything left empty or
oddly formatted (not an email address, a date not in ÅÅÅÅ-MM-DD, a price
field with non-numeric characters, an either/or choice with nothing picked)
is listed before you commit, but the checks are advisory - you can still
choose to continue. You're then asked where to save the `.docx`, and
whether to also export a PDF (skip this if LibreOffice isn't installed -
see "No LibreOffice?" below, opening the `.docx` in Word works the same
way). A field left empty keeps the template's placeholder (`XXX`, `XX`,
`DATUM`) rather than being left blank, so it stays visible as a reminder to
fill it in later.

## Scripted way: edit data.yaml and run generate_contract.py

Useful for repeat runs, or generating several contracts from a script
instead of clicking through a form each time.

```bash
cp data.example.yaml data.yaml
# edit data.yaml with the real party names, addresses, prices, dates...

python3 generate_contract.py --data data.yaml --out contract.pdf
```

Any field left out of `data.yaml` keeps the template's placeholder (`XXX`,
`XX`, `DATUM`, or unchecked) - the script prints which ones after running,
so you can catch anything you forgot before sending the contract out.

Add `--keep-docx filled.docx` to also save the intermediate, editable Word
document (useful if the recipient wants a `.docx` instead of / alongside
the PDF).

### No LibreOffice?

Drop `--out` and pass `--keep-docx` on its own - this skips the PDF export
step entirely, so LibreOffice isn't needed at all:

```bash
python3 generate_contract.py --data data.yaml --keep-docx contract.docx
```

Then open `contract.docx` in Microsoft Word and use **File > Save As >
PDF** (or **Export > Create PDF/XPS**) to get the PDF - Word does the same
conversion LibreOffice would, no install required if Word is already on
the machine.

## Fields

See `fields.py` for the full list of `field_id`s (in document order) and
`data.example.yaml` for a filled-in sample covering every field, grouped by
the section of the contract they appear in. A few pricing-table fields sit
right before a unit the template already prints statically (`kr/mån`, `%`,
...) - give bare numbers for those (see the comment in `fields.py`), not
pre-formatted strings, or the unit will be duplicated.

Checkbox fields that share a `group` in `fields.py` (which option is
public/private, and which billing cadence) are mutually exclusive - the
script raises an error if more than one in a group is set to `true`.

## Extending to a different template

`fields.py`'s `sdt_index` values are specific to this template's content
controls. To adapt this to a different contract template, unzip it and walk
its `<w:sdt>` elements in `word/document.xml` in document order to rebuild
the field list (each one's surrounding paragraph/table-cell text tells you
what it's for).
