"""UI layout for the Hårdvara och Installation template - see form_fields.py
for FormField/Section/Kind. Shares its first 7 sections verbatim with
form_fields.py's SECTIONS (same fields, same template up to index 39); only
the pricing/subsidy sections after that are specific to this template.

Ported 1:1 from SECTIONS_HARDWARE in web/aimo_contract_form.html.
"""

from form_fields import FormField, Section

SECTIONS_HARDWARE: list[Section] = [
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
    Section("Hårdvara och installation - kostnad", [
        FormField("hardvara_kostnad", "Kostnad för hårdvara (SEK)", "numeric"),
        FormField("installation_kostnad", "Kostnad för ev. installation (SEK)", "numeric"),
        FormField("tillbehor_kostnad", "Kostnad för ev. tillbehör (SEK)", "numeric"),
        FormField("totalkostnad", "Totalkostnad (SEK)", "numeric"),
        FormField("antal_laddboxar", "Antal laddboxar (st)", "numeric"),
        FormField("antal_ladduttag", "Antal ladduttag (st)", "numeric"),
    ]),
    Section("Tilläggstjänster (SIM-kort)", [
        FormField("sim_pris_per_manad", "Pris per SIM-kort och månad (kr, bara siffror)", "numeric"),
        FormField("sim_ska_levereras", "Aimo ska leverera SIM-kort", "checkbox"),
        FormField("sim_antal", "Antal SIM-kort", "numeric"),
        FormField("sim_summa_manad", "Summa per månad (kr, bara siffror)", "numeric"),
    ]),
    Section("Bidragsansökningar", [
        FormField("bidrag_ladda_bilen", "Aimo ska ansöka om bidraget “Ladda bilen” (icke-publik laddning)", "checkbox"),
        FormField("bidrag_ladda_bilen_kostnad", "Kostnad (kr)", "numeric"),
        FormField("bidrag_klimatklivet", "Aimo ska ansöka om bidraget “Klimatklivet” (publik laddning)", "checkbox"),
        FormField("bidrag_klimatklivet_kostnad", "Kostnad (kr)", "numeric"),
        FormField("bidrag_slutrapportering", "Aimo ska genomföra slutrapportering för ansökan till relevant myndighet", "checkbox"),
        FormField("bidrag_slutrapportering_kostnad", "Kostnad (kr)", "numeric"),
        FormField("arlig_kontroll", "Årlig kontroll av laddboxarna (faktureras årligen i förskott)", "checkbox"),
        FormField("arlig_kontroll_kostnad", "Kostnad (kr/år)", "numeric"),
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
