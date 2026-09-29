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

## Setup

```bash
pip install -r requirements.txt
# needs LibreOffice for the PDF export step
sudo apt-get install -y libreoffice-writer
```

## Usage

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
