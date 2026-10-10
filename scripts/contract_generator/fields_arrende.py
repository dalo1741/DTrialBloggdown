"""Field map for template/Arrendeavtal_Omsattningsbaserad_Arrendeavgift.docx.

This template has no content controls at all - it uses the legacy Word
"Form Field" mechanism (FORMTEXT/FORMCHECKBOX/FORMDROPDOWN fldChar
fields), addressed here the same way as fields.py's `index`: by position
among all such fields in word/document.xml, in document order (the
field `w:name` values are mostly non-unique or blank in this template,
so they can't be used as stable keys).

`kind="dropdown"` is a FORMDROPDOWN field - `opts` is that field's exact
listEntry values, in order; the value stored for the field must be one of
these strings, and generate_contract.py writes the matching index into
the field's <w:result>, not free text.

`blank_positions` marks extra field slots immediately adjacent to one
logical field (template-authoring artifacts - the same blank split across
several field instances) that must be forced empty whenever this field is
written, so nothing duplicates in the output.

`word/document.xml` in this template also ships with a UTF-8 byte-order
mark, unlike the other two templates - generate_contract.py's XML parsing
has to tolerate that (see its module docstring).

Ported 1:1 from FIELDS_ARRENDE in web/aimo_contract_form.html - keep both
in sync by hand if this template changes.
"""

from fields import Field

FIELDS_ARRENDE: list[Field] = [
    Field(0, "driftstalle_nr", "text", "XXX"),
    Field(1, "avtalsnummer", "text", "XXX"),
    Field(2, "uppdragsgivarnr", "text", "XXX"),
    Field(3, "fastighetsagare_namn", "text", "XXX"),
    Field(4, "fastighetsagare_orgnr", "text", "XXX", blank_positions=(5, 6)),
    Field(7, "fastighetsagare_momsnr", "text", "XXX", blank_positions=(8, 9)),
    Field(10, "arrendestalle_kommun", "text", "XXX"),
    Field(11, "arrendestalle_fastighetsbeteckning", "text", "XXX"),
    Field(12, "arrendestalle_adress", "text", "XXX"),
    Field(13, "antal_parkeringsplatser", "text", "XX"),
    Field(14, "arrendestalle_sarskilda_villkor", "text", "XXX"),
    Field(15, "avtal_start_datum", "text", "DATUM"),
    Field(16, "avtal_slut_datum", "text", "DATUM"),
    Field(17, "uppsagningstid_antal_ord", "text", "XXX"),
    Field(18, "uppsagningstid_antal_siffror", "text", "XX"),
    Field(19, "uppsagningstid_enhet", "dropdown", "månader", opts=("månader", "månad")),
    Field(20, "forlangningstid_antal_ord", "dropdown", "tre", opts=("tre", "ett", "två", "fyra")),
    Field(21, "forlangningstid_antal_siffror", "dropdown", "3", opts=("3", "1", "2", "4", "5")),
    Field(22, "forlangningstid_enhet", "dropdown", "år", opts=("år", "månader", "månad")),
    Field(23, "arrende_procent_ord", "text", "XXX"),
    Field(24, "arrende_procent_siffror", "text", "XX"),
    Field(25, "faktureringsperiod", "dropdown", "kalenderkvartal", opts=("kalenderkvartal", "kalendermånad")),
    Field(26, "betalningssatt", "dropdown", "plusgiro", opts=("plusgiro", "bankgiro")),
    Field(27, "bankgiro_plusgiro_nr", "text", "XXX"),
    Field(
        28, "arbete_a_arrendestallet_ersattning", "text",
        "Fastighetsägaren skall även ersätta Arrendatorn för den intäktsförlust som härvidlag uppstår. "
        "Ersättningen beräknas efter gällande månadshyra för de parkeringsplatser som inte kan nyttjas, "
        "vilket skall reducera Arrendatorns arrendeavgift för samma tid.",
    ),
    Field(29, "ansvar_parkeringsovervakning", "dropdown", "Skall ombesörjas och bekostas av Arrendatorn.",
          opts=("Skall ombesörjas och bekostas av Arrendatorn.", "Skall ombesörjas och bekostas av Fastighetsägaren.", "Ej aktuellt för Arrendestället.")),
    Field(30, "ansvar_kundservice_kontrollavgifter", "dropdown", "Skall ombesörjas och bekostas av Arrendatorn.",
          opts=("Skall ombesörjas och bekostas av Arrendatorn.", "Skall ombesörjas och bekostas av Fastighetsägaren.", "Ej aktuellt för Arrendestället.")),
    Field(31, "ansvar_uppfoljning_indrivning", "dropdown", "Skall ombesörjas och bekostas av Arrendatorn.",
          opts=("Skall ombesörjas och bekostas av Arrendatorn.", "Skall ombesörjas och bekostas av Fastighetsägaren.", "Ej aktuellt för Arrendestället.")),
    Field(32, "ansvar_stadning", "dropdown", "Skall ombesörjas och bekostas av Fastighetsägaren.",
          opts=("Skall ombesörjas och bekostas av Fastighetsägaren.", "Skall ombesörjas och bekostas av Arrendatorn.", "Ej aktuellt för Arrendestället.")),
    Field(33, "ansvar_uthyrning_langtid", "dropdown", "Skall ombesörjas och bekostas av Arrendatorn.",
          opts=("Skall ombesörjas och bekostas av Arrendatorn.", "Skall ombesörjas och bekostas av Fastighetsägaren.", "Ej aktuellt för Arrendestället.")),
    Field(34, "ansvar_eldragning", "dropdown", "Skall ombesörjas och bekostas av Fastighetsägaren.",
          opts=("Skall ombesörjas och bekostas av Fastighetsägaren.", "Skall ombesörjas och bekostas av Arrendatorn.", "Ej aktuellt för Arrendestället.")),
    Field(35, "ansvar_motorvarmare", "dropdown", "Skall ombesörjas och bekostas av Fastighetsägaren.",
          opts=("Skall ombesörjas och bekostas av Fastighetsägaren.", "Skall ombesörjas och bekostas av Arrendatorn.", "Ej aktuellt för Arrendestället.")),
    Field(36, "ansvar_belysning", "dropdown", "Skall ombesörjas och bekostas av Fastighetsägaren.",
          opts=("Skall ombesörjas och bekostas av Fastighetsägaren.", "Skall ombesörjas och bekostas av Arrendatorn.", "Ej aktuellt för Arrendestället.")),
    Field(37, "ansvar_skyltprogram", "dropdown", "Skall ombesörjas och bekostas av Fastighetsägaren.",
          opts=("Skall ombesörjas och bekostas av Fastighetsägaren.", "Ej aktuellt för Arrendestället.", "Skall ombesörjas av Arrendatorn.")),
    Field(38, "parkeringstillstand_enligt_prislista", "checkbox", False, group="parkeringstillstand"),
    Field(39, "parkeringstillstand_ej_aktuellt", "checkbox", False, group="parkeringstillstand"),
    Field(40, "pskivor_enligt_taxa", "checkbox", False, group="pskivor"),
    Field(41, "pskivor_ej_aktuellt", "checkbox", False, group="pskivor"),
    Field(42, "nytt_avtal", "checkbox", False, group="tidigare_avtal"),
    Field(43, "ersatter_tidigare_avtal", "checkbox", False, group="tidigare_avtal"),
    Field(44, "tidigare_avtal_datum1", "text", "XXX"),
    Field(45, "tidigare_avtal_datum2", "text", "XXX"),
    Field(46, "bilaga2_inkluderad", "checkbox", False),
    Field(47, "bilaga2_namn", "text", "XXX"),
    Field(48, "bilaga2_nr", "text", "XX"),
    Field(49, "bilaga3_inkluderad", "checkbox", False),
    Field(50, "bilaga3_namn", "text", "XXX"),
    Field(51, "bilaga3_nr", "text", "XX"),
    Field(52, "bilaga4_inkluderad", "checkbox", False),
    Field(53, "bilaga4_namn", "text", "XXX"),
    Field(54, "bilaga4_nr", "text", "XX"),
    Field(55, "fastighetsagare_ort_datum", "text", "XXX", blank_positions=(56, 57)),
    Field(58, "arrendator_datum", "text", "XXX", blank_positions=(59,)),
    Field(60, "fastighetsagare_namnfortydligande", "text", "XXX"),
    Field(61, "fastighetsagare_kontakt_redovisning_namn", "text", "XXX"),
    Field(62, "fastighetsagare_kontakt_redovisning_mail", "text", "XXX@XXX.se"),
    Field(63, "fastighetsagare_kontakt_redovisning_tel", "text", "XXX"),
    Field(64, "fastighetsagare_redovisningsadress", "text", "XXX"),
    Field(65, "fastighetsagare_kontakt_drift_namn", "text", "XXX"),
    Field(66, "fastighetsagare_kontakt_drift_mail", "text", "XXX@XXX.se"),
    Field(67, "fastighetsagare_kontakt_drift_tel", "text", "XXX"),
    Field(68, "arrendator_kontakt_drift_namn", "text", "XXX"),
    Field(69, "arrendator_kontakt_drift_mail", "text", "XXX@XXX.se"),
    Field(70, "arrendator_kontakt_drift_tel", "text", "XXX"),
]
