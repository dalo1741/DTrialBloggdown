#!/usr/bin/env python3
"""Fill in the Aimo charging-services contract template and export a PDF.

The template (template/Avtal_Aimo_Charge_Fee_to_Landlord_v1.2.docx) is used
as-is so the generated PDF keeps its exact header banner, footer icon, fonts
and table styling - only the content-control placeholders (see fields.py)
are replaced. See data.example.yaml for the field list and README.md for
usage.

Usage:
    python generate_contract.py --data data.yaml --out contract.pdf

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

from fields import FIELDS, CHECKED, UNCHECKED

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
NSMAP = {"w": W.strip("{}")}

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_TEMPLATE = SCRIPT_DIR / "template" / "Avtal_Aimo_Charge_Fee_to_Landlord_v1.2.docx"


def load_data(path: Path) -> dict:
    raw = yaml.safe_load(path.read_text()) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"{path} must contain a mapping of field_id -> value")
    return raw


def validate_groups(data: dict) -> None:
    groups: dict[str, list[str]] = {}
    for f in FIELDS:
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


def fill_template(template_path: Path, data: dict, out_docx: Path) -> list[str]:
    validate_groups(data)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        unpacked = tmp_path / "unpacked"
        with zipfile.ZipFile(template_path) as zf:
            zf.extractall(unpacked)

        doc_xml_path = unpacked / "word" / "document.xml"
        tree = etree.parse(str(doc_xml_path))
        root = tree.getroot()
        body = root.find(f"{W}body")
        sdts = list(body.iter(f"{W}sdt"))

        unfilled: list[str] = []
        for f in FIELDS:
            if f.sdt_index >= len(sdts):
                raise ValueError(f"Template has no content control at index {f.sdt_index}")
            sdt = sdts[f.sdt_index]
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

        tree.write(str(doc_xml_path), xml_declaration=True, encoding="UTF-8", standalone=True)

        out_docx.parent.mkdir(parents=True, exist_ok=True)
        if out_docx.exists():
            out_docx.unlink()
        with zipfile.ZipFile(out_docx, "w", zipfile.ZIP_DEFLATED) as zf:
            for file in sorted(unpacked.rglob("*")):
                if file.is_file():
                    zf.write(file, file.relative_to(unpacked))

        return unfilled


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
    parser.add_argument("--data", type=Path, required=True, help="YAML file with field_id -> value")
    parser.add_argument(
        "--out", type=Path, default=None,
        help="Output PDF path. Requires LibreOffice (soffice) to be installed. "
             "Omit this and use --keep-docx if it isn't available.",
    )
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE, help="Template .docx to fill in")
    parser.add_argument(
        "--keep-docx", type=Path, default=None,
        help="Save the filled .docx here. Required if --out is omitted.",
    )
    args = parser.parse_args(argv)
    if args.out is None and args.keep_docx is None:
        parser.error("pass --out (for a PDF) and/or --keep-docx (for a .docx you finish in Word)")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    data = load_data(args.data)

    with tempfile.TemporaryDirectory() as tmp:
        filled_docx = args.keep_docx or (Path(tmp) / "filled.docx")
        unfilled = fill_template(args.template, data, filled_docx)
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
