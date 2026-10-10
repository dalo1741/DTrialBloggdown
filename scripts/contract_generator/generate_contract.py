#!/usr/bin/env python3
"""Fill in an Aimo contract template and export a PDF.

The template is used as-is so the generated PDF keeps its exact header
banner, footer icon, fonts and table styling - only the placeholders (see
fields.py and templates.py) are replaced. See data.example.yaml for the
field list (Aimo Charge template) and README.md for usage.

Usage:
    python generate_contract.py --data data.yaml --out contract.pdf
    python generate_contract.py --data data.yaml --template-id arrende_omsattning_v1 --keep-docx avtal.docx

Pass --list-templates to see available --template-id values.

If LibreOffice (the "soffice" command) isn't installed - e.g. it's blocked
by IT policy - drop --out and just ask for the .docx instead:

    python generate_contract.py --data data.yaml --keep-docx contract.docx

Then open contract.docx in Microsoft Word and use File > Save As (or
Export > Create PDF/XPS) to get the PDF - no LibreOffice needed.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import yaml
from lxml import etree

from fields import Field, CHECKED, UNCHECKED
from templates import TEMPLATES, DEFAULT_TEMPLATE_ID, TemplateMeta

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
NSMAP = {"w": W.strip("{}")}

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_TEMPLATE = TEMPLATES[DEFAULT_TEMPLATE_ID].docx_path


def load_data(path: Path) -> dict:
    raw = yaml.safe_load(path.read_text()) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"{path} must contain a mapping of field_id -> value")
    return raw


def validate_groups(fields: list[Field], data: dict) -> None:
    groups: dict[str, list[str]] = {}
    for f in fields:
        if f.group:
            groups.setdefault(f.group, []).append(f.field_id)
    for group, field_ids in groups.items():
        selected = [fid for fid in field_ids if bool(data.get(fid, False))]
        if len(selected) > 1:
            raise ValueError(
                f"Group {group!r} allows only one selected option, got: {selected}"
            )


def set_text_content(sdt_content: etree._Element, value: str) -> None:
    ts = sdt_content.findall(f".//{W}t")
    if not ts:
        raise ValueError("Content control has no <w:t> to write into")
    ts[0].text = value
    for extra in ts[1:]:
        extra.text = ""


def set_checkbox(sdt: etree._Element, sdt_content: etree._Element, checked: bool) -> None:
    ts = sdt_content.findall(f".//{W}t")
    if not ts:
        raise ValueError("Checkbox content control has no <w:t> to write into")
    ts[0].text = CHECKED if checked else UNCHECKED
    for extra in ts[1:]:
        extra.text = ""

    checkbox_el = sdt.find(f"{W}sdtPr/{W}checkbox")
    if checkbox_el is None:
        # newer schema uses the w14 namespace
        for child in sdt.find(f"{W}sdtPr"):
            if child.tag.endswith("}checkbox"):
                checkbox_el = child
                break
    if checkbox_el is not None:
        for child in checkbox_el:
            if child.tag.endswith("}checked"):
                val_attr = [a for a in child.attrib if a.endswith("}val")]
                if val_attr:
                    child.attrib[val_attr[0]] = "1" if checked else "0"


def _fill_body_sdt(root: etree._Element, fields: list[Field], data: dict) -> list[str]:
    """Edits native Word content controls (<w:sdt>), addressed by position
    (Field.index) among all such elements in word/document.xml."""
    body = root.find(f"{W}body")
    sdts = list(body.iter(f"{W}sdt"))

    unfilled: list[str] = []
    for f in fields:
        if f.index >= len(sdts):
            raise ValueError(f"Template has no content control at index {f.index}")
        sdt = sdts[f.index]
        content = sdt.find(f"{W}sdtContent")
        if content is None:
            raise ValueError(f"Content control {f.field_id} has no sdtContent")

        if f.kind == "text":
            value = str(data.get(f.field_id, f.default))
            set_text_content(content, value)
            if value == f.default:
                unfilled.append(f.field_id)
        else:  # checkbox
            checked = bool(data.get(f.field_id, f.default))
            set_checkbox(sdt, content, checked)

    return unfilled


class _FormTextSlot:
    __slots__ = ("checkbox_el", "ddlist_el", "text_nodes")

    def __init__(self) -> None:
        self.checkbox_el: etree._Element | None = None
        self.ddlist_el: etree._Element | None = None
        self.text_nodes: list[etree._Element] = []


def _collect_formtext_slots(root: etree._Element) -> list[_FormTextSlot]:
    """Walks every <w:r> in document order, grouping the runs between a
    "begin" and "end" fldChar into one slot per legacy Form Field, in the
    same order they appear in the template - see fields_arrende.py's
    module docstring for why position (not the field's own w:name) is
    used to address these."""
    slots: list[_FormTextSlot] = []
    current: _FormTextSlot | None = None

    for run in root.iter(f"{W}r"):
        fld = run.find(f"{W}fldChar")
        if fld is not None:
            ftype = fld.get(f"{W}fldCharType")
            if ftype == "begin":
                current = _FormTextSlot()
                ff_data = fld.find(f"{W}ffData")
                if ff_data is not None:
                    current.checkbox_el = ff_data.find(f"{W}checkBox")
                    current.ddlist_el = ff_data.find(f"{W}ddList")
            elif ftype == "end":
                if current is not None:
                    slots.append(current)
                current = None
            continue
        if current is not None:
            for t in run.findall(f"{W}t"):
                current.text_nodes.append(t)

    return slots


def _set_slot_text(slot: _FormTextSlot, value: str) -> None:
    if not slot.text_nodes:
        raise ValueError("Fältet saknar textnod i mallen")
    slot.text_nodes[0].text = value
    for extra in slot.text_nodes[1:]:
        extra.text = ""


def _set_slot_checked(slot: _FormTextSlot, checked: bool) -> None:
    if slot.checkbox_el is None:
        raise ValueError("Fältet är inte en kryssruta i mallen")
    checked_el = slot.checkbox_el.find(f"{W}checked")
    if checked_el is None:
        checked_el = etree.SubElement(slot.checkbox_el, f"{W}checked")
    checked_el.set(f"{W}val", "1" if checked else "0")


def _set_slot_dropdown(slot: _FormTextSlot, index: int) -> None:
    if slot.ddlist_el is None:
        raise ValueError("Fältet är inte en dropdown i mallen")
    result_el = slot.ddlist_el.find(f"{W}result")
    if result_el is None:
        result_el = etree.SubElement(slot.ddlist_el, f"{W}result")
    result_el.set(f"{W}val", str(index))


def _fill_body_formtext(root: etree._Element, fields: list[Field], data: dict) -> list[str]:
    """Edits legacy Word "Form Fields" (FORMTEXT/FORMCHECKBOX/FORMDROPDOWN),
    addressed by position (Field.index) - mirrors fillFormText() in
    web/aimo_contract_form.html."""
    slots = _collect_formtext_slots(root)

    unfilled: list[str] = []
    for f in fields:
        if f.index >= len(slots):
            raise ValueError(f"Mallen saknar fält {f.index}")
        slot = slots[f.index]

        if f.kind == "text":
            value = str(data.get(f.field_id, f.default))
            _set_slot_text(slot, value)
            if value == f.default:
                unfilled.append(f.field_id)
        elif f.kind == "checkbox":
            _set_slot_checked(slot, bool(data.get(f.field_id, f.default)))
        elif f.kind == "dropdown":
            chosen = data.get(f.field_id, f.default)
            idx = f.opts.index(chosen) if f.opts and chosen in f.opts else 0
            _set_slot_dropdown(slot, idx)

        for bp in f.blank_positions:
            if bp < len(slots):
                _set_slot_text(slots[bp], "")

    return unfilled


def fill_template(
    template_path: Path, fields: list[Field], mechanism: str, data: dict, out_docx: Path
) -> list[str]:
    validate_groups(fields, data)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        unpacked = tmp_path / "unpacked"
        with zipfile.ZipFile(template_path) as zf:
            zf.extractall(unpacked)

        doc_xml_path = unpacked / "word" / "document.xml"
        # lxml/libxml2 detect encoding (including a UTF-8 byte-order mark,
        # which the Arrendeavtal template's document.xml has, unlike the
        # other two) from the raw bytes at parse time, so no BOM handling
        # is needed here the way the browser-based web version needed one
        # (JSZip hands it a pre-decoded JS string, where a BOM becomes a
        # literal leading character instead of an encoding signal).
        tree = etree.parse(str(doc_xml_path))
        root = tree.getroot()

        if mechanism == "formtext":
            unfilled = _fill_body_formtext(root, fields, data)
        else:
            unfilled = _fill_body_sdt(root, fields, data)

        tree.write(str(doc_xml_path), xml_declaration=True, encoding="UTF-8", standalone=True)

        out_docx.parent.mkdir(parents=True, exist_ok=True)
        if out_docx.exists():
            out_docx.unlink()
        with zipfile.ZipFile(out_docx, "w", zipfile.ZIP_DEFLATED) as zf:
            for file in sorted(unpacked.rglob("*")):
                if file.is_file():
                    zf.write(file, file.relative_to(unpacked))

        return unfilled


def fill_template_meta(template: TemplateMeta, data: dict, out_docx: Path, template_path: Path | None = None) -> list[str]:
    """Convenience wrapper: fill_template() driven by a TemplateMeta, with
    an optional path override (--template) that keeps that template's own
    field model."""
    return fill_template(template_path or template.docx_path, template.fields, template.mechanism, data, out_docx)


class LibreOfficeNotFound(RuntimeError):
    pass


def convert_to_pdf(docx_path: Path, out_pdf: Path) -> None:
    with tempfile.TemporaryDirectory() as profile_dir:
        try:
            result = subprocess.run(
                [
                    "soffice",
                    "--headless",
                    "--norestore",
                    f"-env:UserInstallation=file://{profile_dir}",
                    "--convert-to",
                    "pdf",
                    "--outdir",
                    str(out_pdf.parent),
                    str(docx_path),
                ],
                capture_output=True,
                text=True,
            )
        except FileNotFoundError as exc:
            raise LibreOfficeNotFound(
                "LibreOffice ('soffice') isn't installed or isn't on PATH, so the "
                "PDF export step can't run. Drop --out and pass --keep-docx instead "
                "to get the filled .docx, then open it in Microsoft Word and use "
                "File > Save As > PDF (or Export > Create PDF/XPS) to finish."
            ) from exc
        if result.returncode != 0:
            raise RuntimeError(
                f"soffice conversion failed (exit {result.returncode}):\n"
                f"{result.stdout}\n{result.stderr}"
            )

    produced = docx_path.with_suffix(".pdf")
    produced = out_pdf.parent / produced.name
    if produced != out_pdf:
        out_pdf.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(produced), str(out_pdf))


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", type=Path, help="YAML file with field_id -> value")
    parser.add_argument(
        "--template-id", default=DEFAULT_TEMPLATE_ID, choices=sorted(TEMPLATES),
        help=f"Which contract type to fill in (default: {DEFAULT_TEMPLATE_ID})",
    )
    parser.add_argument(
        "--list-templates", action="store_true",
        help="Print available --template-id values and exit",
    )
    parser.add_argument(
        "--out", type=Path, default=None,
        help="Output PDF path. Requires LibreOffice (soffice) to be installed. "
             "Omit this and use --keep-docx if it isn't available.",
    )
    parser.add_argument("--template", type=Path, default=None, help="Template .docx to fill in (overrides --template-id's default file, keeps its field model)")
    parser.add_argument(
        "--keep-docx", type=Path, default=None,
        help="Save the filled .docx here. Required if --out is omitted.",
    )
    args = parser.parse_args(argv)
    if args.list_templates:
        return args
    if args.data is None:
        parser.error("--data is required (unless --list-templates)")
    if args.out is None and args.keep_docx is None:
        parser.error("pass --out (for a PDF) and/or --keep-docx (for a .docx you finish in Word)")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])

    if args.list_templates:
        for template_id, meta in sorted(TEMPLATES.items()):
            print(f"{template_id}\t{meta.name}")
        return 0

    template = TEMPLATES[args.template_id]
    data = load_data(args.data)

    with tempfile.TemporaryDirectory() as tmp:
        filled_docx = args.keep_docx or (Path(tmp) / "filled.docx")
        unfilled = fill_template_meta(template, data, filled_docx, template_path=args.template)
        if args.out is not None:
            convert_to_pdf(filled_docx, args.out)
            print(f"Wrote {args.out}")
        if args.keep_docx is not None:
            print(f"Wrote {args.keep_docx}")
        if args.out is None:
            print(
                "No --out given, so no PDF was made. Open the .docx above in "
                "Microsoft Word and use File > Save As > PDF (or Export > Create "
                "PDF/XPS) to finish."
            )

    if unfilled:
        print(f"Note: {len(unfilled)} field(s) left at their placeholder default (not set in {args.data}):")
        for fid in unfilled:
            print(f"  - {fid}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except LibreOfficeNotFound as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
