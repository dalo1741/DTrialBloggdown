"""UI layout and validation rules for contract_form.py.

Separate from fields.py (which maps field_id -> template content-control
position): this module only describes how each field should be presented
and checked in the form, grouped into the tabs the form shows.
"""

from dataclasses import dataclass, field
from typing import Literal

Kind = Literal["text", "email", "numeric", "date", "radio", "checkbox"]


@dataclass(frozen=True)
class FormField:
    field_id: str  # for radio: the field_id of the *selected* option is what's set True
    label: str
    kind: Kind
    hint: str = ""
    width: int = 40
    # radio only: list of (field_id, option_label)
    options: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class Section:
    title: str
    fields: list[FormField] = field(default_factory=list)


SECTIONS: list[Section] = [
    Section("Motpart", [
        FormField("party2_namn", "Uppdragsgivarens namn", "text"),
        FormField("party2_orgnr", "Uppdragsgivarens org.nr", "text", hint="format: 556000-0000"),
    ]),
    Section("Aimo - kontaktperson", [
        FormField("aimo_ombud_namn", "Ombud namn", "text"),
        FormField("aimo_ombud_tel", "Ombud telefon", "text"),
        FormField("aimo_ombud_epost", "Ombud e-post", "email"),
    ]),
    Section("Beställare", [
        FormField("bestallare_adress", "Adress", "text"),
        FormField("bestallare_postnummer", "Postnummer", "text", hint="format: 123 45"),
        FormField("bestallare_ort", "Ort", "text"),
        FormField("bestallare_ombud_namn", "Ombud namn", "text"),
        FormField("bestallare_ombud_tel", "Ombud telefon", "text"),
        FormField("bestallare_ombud_epost", "Ombud e-post", "email"),
    ]),
    Section("Fakturering", [
        FormField("faktura_epost", "E-postfaktura", "email"),
        FormField("faktura_adress", "Adress", "text"),
        FormField("faktura_postnummer", "Postnummer", "text", hint="format: 123 45"),
        FormField("faktura_ort", "Ort", "text"),
        FormField("faktura_markning", "Fakturamärkning", "text"),
    ]),
    Section("Självfaktura", [
        FormField("sjalvfaktura_ombud_namn", "Ombud namn", "text"),
        FormField("sjalvfaktura_ombud_tel", "Ombud telefon", "text"),
        FormField("sjalvfaktura_ombud_epost", "Ombud e-post", "email"),
        FormField("sjalvfaktura_bankgiro", "Bank-/Plusgiro", "text"),
        FormField("sjalvfaktura_epost", "E-postfaktura", "email"),
        FormField("sjalvfaktura_markning", "Fakturamärkning", "text"),
    ]),
    Section("Anläggningsadress", [
        FormField("anlaggning_adress", "Adress", "text"),
        FormField("anlaggning_postnummer", "Postnummer", "text", hint="format: 123 45"),
        FormField("anlaggning_ort", "Ort", "text"),
        FormField("anlaggning_fastighetsbeteckning", "Fastighetsbeteckning", "text"),
        FormField("anlaggning_facility_uid", "Aimo Parking Facility-UID (om finns)", "text"),
        FormField("anlaggning_matare_id_suffix", "Anläggnings-ID energimätare (efter 735999)", "numeric"),
    ]),
    Section("Aimo Charge - pris", [
        FormField("charge_antal_uttag", "Antal uttag", "numeric"),
        FormField("charge_pris_per_uttag", "Pris/uttag (kr/mån, bara siffror)", "numeric"),
        FormField("charge_summa_manad", "Summa per månad (kr, bara siffror)", "numeric"),
        FormField("startavgift_antal_uttag", "Startavgift - antal uttag", "numeric"),
        FormField("startavgift_pris_per_uttag", "Startavgift - pris/uttag (kr, bara siffror)", "numeric"),
        FormField("startavgift_summa", "Startavgift - summa (kr, bara siffror)", "numeric"),
        FormField("summa_per_manad_total", "Totalsumma per månad (kr, bara siffror)", "numeric"),
        FormField("summa_engangskostnad_total", "Total engångskostnad (kr, bara siffror)", "numeric"),
    ]),
    Section("Konsumentpris", [
        FormField("konsument_pris_kwh", "Pris för konsument (kr/kWh, bara siffror)", "numeric"),
        FormField("konsument_ersattning_procent", "Aimos ersättning till Uppdragsgivaren (%, bara siffror)", "numeric"),
        FormField("laddare_publika", "Är laddarna publika?", "radio",
                  options=(("laddare_publika_ja", "Ja"), ("laddare_publika_nej", "Nej"))),
    ]),
    Section("Tilläggstjänster (SIM-kort)", [
        FormField("sim_pris_per_manad", "Pris per SIM-kort och månad (kr, bara siffror)", "numeric"),
        FormField("sim_ska_levereras", "Aimo ska leverera SIM-kort", "checkbox"),
        FormField("sim_antal", "Antal SIM-kort", "numeric"),
        FormField("sim_summa_manad", "Summa per månad (kr, bara siffror)", "numeric"),
    ]),
    Section("Avtalstid", [
        FormField("avtal_start_datum", "Startdatum", "date", hint="format: ÅÅÅÅ-MM-DD"),
        FormField("avtal_slut_datum", "Slutdatum", "date", hint="format: ÅÅÅÅ-MM-DD"),
    ]),
    Section("Betalningsvillkor", [
        FormField("betalning", "Faktureringsintervall", "radio",
                  options=(
                      ("betalning_manadsvis", "Månadsvis"),
                      ("betalning_kvartalsvis", "Kvartalsvis"),
                      ("betalning_arsvis", "Årsvis"),
                  )),
    ]),
]
