"""Field map for template/Avtal_Aimo_Charge_Hardvara_och_Installation_v1.2.docx.

Same content-control (<w:sdt>) mechanism as fields.py - index 0-39 are the
same fields, in the same order, as fields.py's FIELDS (party/invoicing/
facility/pricing/public-charger/SIM); this template extends that one with
hardware/installation costs and subsidy-application checkboxes. Indices
63-65 ("Bifogas ej"/"Bifogas vid behov" appendix labels in the template)
are intentionally left out, same rationale as every other field left
unfilled: the template's own text stays as-is.

Ported 1:1 from FIELDS_HARDWARE in web/aimo_contract_form.html - keep
both in sync by hand if this template changes.
"""

from fields import Field

FIELDS_HARDWARE: list[Field] = [
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
    Field(27, "anlaggning_matare_id_suffix", "text", "XXX"),
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
    Field(40, "hardvara_kostnad", "text", "XXX"),
    Field(41, "installation_kostnad", "text", "XXX"),
    Field(42, "tillbehor_kostnad", "text", "XXX"),
    Field(43, "totalkostnad", "text", "XXX"),
    Field(44, "antal_laddboxar", "text", "XX"),
    Field(45, "antal_ladduttag", "text", "XX"),
    Field(46, "sim_pris_per_manad", "text", "89"),
    Field(47, "sim_ska_levereras", "checkbox", False),
    Field(48, "sim_antal", "text", "X"),
    Field(49, "sim_summa_manad", "text", "XX"),
    Field(50, "bidrag_ladda_bilen", "checkbox", False),
    Field(51, "bidrag_ladda_bilen_kostnad", "text", "XX"),
    Field(52, "bidrag_klimatklivet", "checkbox", False),
    Field(53, "bidrag_klimatklivet_kostnad", "text", "XX"),
    Field(54, "bidrag_slutrapportering", "checkbox", False),
    Field(55, "bidrag_slutrapportering_kostnad", "text", "XX"),
    Field(56, "arlig_kontroll", "checkbox", False),
    Field(57, "arlig_kontroll_kostnad", "text", "XX"),
    Field(58, "avtal_start_datum", "text", "DATUM"),
    Field(59, "avtal_slut_datum", "text", "DATUM"),
    Field(60, "betalning_manadsvis", "checkbox", False, group="betalningsvillkor"),
    Field(61, "betalning_kvartalsvis", "checkbox", False, group="betalningsvillkor"),
    Field(62, "betalning_arsvis", "checkbox", False, group="betalningsvillkor"),
]
