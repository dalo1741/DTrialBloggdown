# web - browser version

`aimo_contract_form.html` is a self-contained web version of the form:
everything (form UI, the fill-in logic, and the contract template itself,
embedded as base64) ships in one file. No Python, no LibreOffice, no
install at all - open it and it works, or share the published link below.

Published copy: https://claude.ai/artifact/MiAnE7LKoJYhnEtvUGK53z

## How it works

The browser loads [JSZip](https://stuk.github.io/jszip/) from a CDN,
decodes the embedded template, and edits `word/document.xml` inside it the
same way `generate_contract.py` does - by position (`sdtIndex`), replacing
each content control's text or, for checkboxes, swapping ☐/☒. The result
is re-zipped client-side and handed to you as a download. There's no
server: nothing you type leaves your browser except to become the
downloaded file.

The field list in the page's `<script>` (`FIELDS` and `SECTIONS`) mirrors
`../fields.py` and `../form_fields.py` exactly - if the template ever
changes, update both the Python and this file together.

## Opening it yourself

This file can also just be opened directly as a local file
(`file://.../aimo_contract_form.html`) in any browser - double-click it.
Everything works the same way except the download step, which needs the
page to be the published, hosted copy linked above (a bare local file has
no download destination to hand the file to).

## PDF

Same as the desktop app: once you have the `.docx`, open it in Microsoft
Word and use **File > Save As > PDF** (or **Export > Create PDF/XPS**) -
there's no LibreOffice or server-side conversion here either.
