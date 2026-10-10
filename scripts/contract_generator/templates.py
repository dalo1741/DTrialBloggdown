"""Template registry shared by generate_contract.py and contract_form.py -
the desktop/CLI counterpart of the `TEMPLATES` object in
web/aimo_contract_form.html (see CLAUDE.md's Phase 3 notes for the
rationale behind `mechanism`).

Adding a new template means: a `fields_X.py` (see fields.py's and
fields_arrende.py's docstrings for the two mechanisms), a
`form_fields_X.py` (see form_fields.py), dropping the source .docx into
template/, and one new entry here.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from fields import Field
from fields_hardware import FIELDS_HARDWARE
from fields_arrende import FIELDS_ARRENDE
from fields import FIELDS as FIELDS_CHARGE
from form_fields import Section
from form_fields import SECTIONS as SECTIONS_CHARGE
from form_fields_hardware import SECTIONS_HARDWARE
from form_fields_arrende import SECTIONS_ARRENDE

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = SCRIPT_DIR / "template"


@dataclass(frozen=True)
class TemplateMeta:
    template_id: str
    name: str
    description: str
    mechanism: Literal["sdt", "formtext"]
    docx_path: Path
    fields: list[Field]
    sections: list[Section]
    output_filename: str
    name_hint_field: str  # which field seeds a suggested draft name


TEMPLATES: dict[str, TemplateMeta] = {
    "aimo_charge_v1_2": TemplateMeta(
        template_id="aimo_charge_v1_2",
        name="Aimo Charge - Laddningstjänster",
        description="Avtal för laddningstjänster (per-uttag debitering).",
        mechanism="sdt",
        docx_path=TEMPLATE_DIR / "Avtal_Aimo_Charge_Fee_to_Landlord_v1.2.docx",
        fields=FIELDS_CHARGE,
        sections=SECTIONS_CHARGE,
        output_filename="avtal_laddningstjanster.docx",
        name_hint_field="party2_namn",
    ),
    "aimo_charge_hardware_v1_2": TemplateMeta(
        template_id="aimo_charge_hardware_v1_2",
        name="Aimo Charge - Hårdvara och Installation",
        description="Avtal för laddningshårdvara och installation, med bidragsansökningar.",
        mechanism="sdt",
        docx_path=TEMPLATE_DIR / "Avtal_Aimo_Charge_Hardvara_och_Installation_v1.2.docx",
        fields=FIELDS_HARDWARE,
        sections=SECTIONS_HARDWARE,
        output_filename="avtal_hardvara_installation.docx",
        name_hint_field="party2_namn",
    ),
    "arrende_omsattning_v1": TemplateMeta(
        template_id="arrende_omsattning_v1",
        name="Arrendeavtal - Omsättningsbaserad Arrendeavgift",
        description="Lägenhetsarrende för parkeringsverksamhet, arrende baserat på årsomsättning.",
        mechanism="formtext",
        docx_path=TEMPLATE_DIR / "Arrendeavtal_Omsattningsbaserad_Arrendeavgift.docx",
        fields=FIELDS_ARRENDE,
        sections=SECTIONS_ARRENDE,
        output_filename="arrendeavtal.docx",
        name_hint_field="fastighetsagare_namn",
    ),
}

DEFAULT_TEMPLATE_ID = "aimo_charge_v1_2"
