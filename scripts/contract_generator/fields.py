"""Field map for template/Avtal_Aimo_Charge_Fee_to_Landlord_v1.2.docx.

Each entry describes one content-control placeholder in the template, in
document order. `index` is that control's position among all <w:sdt>
elements in word/document.xml (0-based) - this is how generate_contract.py
locates it. `group` links radio-button-style checkboxes so selecting one
clears the others.

`Field` is shared by every template's field-map module (fields.py,
fields_hardware.py, fields_arrende.py) - see fields_arrende.py's module
docstring for what `kind="dropdown"`/`opts`/`blank_positions` are for
(they only apply to templates using the legacy Form Field mechanism, not
this one).

Several pricing-table fields (charge_pris_per_uttag, charge_summa_manad,
startavgift_pris_per_uttag, startavgift_summa, summa_per_manad_total,
summa_engangskostnad_total, konsument_pris_kwh, konsument_ersattning_procent,
sim_summa_manad) sit right before static unit text already in the template
(" kr/mån", " kr", " %", ...) - give bare numbers for these, not
pre-formatted strings with units, or the unit will appear twice.
"""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Field:
    index: int
    field_id: str
    kind: Literal["text", "checkbox", "dropdown"]
    default: object
    group: str | None = None
    opts: tuple[str, ...] | None = None          # dropdown only
    blank_positions: tuple[int, ...] = ()         # formtext mechanism only


FIELDS: list[Field] = [
    Field(0, "party2_namn", "text", "XXX"),
    Field(1, "party2_orgnr", "text", "XXX"),

    Field(2, "aimo_ombud_namn", "text", "XXX"),
    Field(3, "aimo_ombud_tel", "text", "XXX"),
    Field(4, "aimo_ombud_epost", "text", "XXX"),

    Field(5, "bestallare_adress", "text", "XXX"),
    Field(6, "bestallare_postnummer", "text", "XXX"),
    Field(7, "bestallare_ort", "text", "XXX"),
    Field(8, "bestallare_ombud_namn", "text", "XXX"),
    Field(9, "bestallare_ombud_tel", "text", "XXX"),
    Field(10, "bestallare_ombud_epost", "text", "XXX@XXX.se"),

    Field(11, "faktura_epost", "text", "XXX@XXX.se"),
    Field(12, "faktura_adress", "text", "XXX"),
    Field(13, "faktura_postnummer", "text", "XXX"),
    Field(14, "faktura_ort", "text", "XXX"),
    Field(15, "faktura_markning", "text", "XXX"),

    Field(16, "sjalvfaktura_ombud_namn", "text", "XXX"),
    Field(17, "sjalvfaktura_ombud_tel", "text", "XXX"),
    Field(18, "sjalvfaktura_ombud_epost", "text", "XXX@XXX.se"),
    Field(19, "sjalvfaktura_bankgiro", "text", "XXX"),
    Field(20, "sjalvfaktura_epost", "text", "XXX@XXX.se"),
    Field(21, "sjalvfaktura_markning", "text", "XXX"),

    Field(22, "anlaggning_adress", "text", "XXX"),
    Field(23, "anlaggning_postnummer", "text", "XXX"),
    Field(24, "anlaggning_ort", "text", "XXX"),
    Field(25, "anlaggning_fastighetsbeteckning", "text", "XXX"),
    Field(26, "anlaggning_facility_uid", "text", "XXX"),
    Field(27, "anlaggning_matare_id_suffix", "text", "XXX"),  # appended after literal "735999" in the template

    Field(28, "charge_antal_uttag", "text", "XX"),
    Field(29, "charge_pris_per_uttag", "text", "XX"),
    Field(30, "charge_summa_manad", "text", "XX"),
    Field(31, "startavgift_antal_uttag", "text", "XX"),
    Field(32, "startavgift_pris_per_uttag", "text", "XX"),
    Field(33, "startavgift_summa", "text", "XX"),
    Field(34, "summa_per_manad_total", "text", "XX"),
    Field(35, "summa_engangskostnad_total", "text", "XX"),

    Field(36, "konsument_pris_kwh", "text", "XX"),
    Field(37, "konsument_ersattning_procent", "text", "XX"),
    Field(38, "laddare_publika_ja", "checkbox", False, group="laddare_publika"),
    Field(39, "laddare_publika_nej", "checkbox", False, group="laddare_publika"),

    Field(40, "sim_pris_per_manad", "text", "89"),
    Field(41, "sim_ska_levereras", "checkbox", False),
    Field(42, "sim_antal", "text", "X"),
    Field(43, "sim_summa_manad", "text", "XX"),

    Field(44, "avtal_start_datum", "text", "DATUM"),
    Field(45, "avtal_slut_datum", "text", "DATUM"),

    Field(46, "betalning_manadsvis", "checkbox", False, group="betalningsvillkor"),
    Field(47, "betalning_kvartalsvis", "checkbox", False, group="betalningsvillkor"),
    Field(48, "betalning_arsvis", "checkbox", False, group="betalningsvillkor"),
]

CHECKED = "☒"    # ☒
UNCHECKED = "☐"  # ☐
