"""UI layout for the Arrendeavtal template - see form_fields.py for
FormField/Section/Kind. Labels here are a fast pass, taken straight from
the template's own wording rather than hand-polished, since there are
~15 contract types planned in total.

Ported 1:1 from SECTIONS_ARRENDE in web/aimo_contract_form.html.
"""

from form_fields import FormField, Section

_ANSVAR_OPTS_ARRENDATOR_FIRST = (
    "Skall ombesörjas och bekostas av Arrendatorn.",
    "Skall ombesörjas och bekostas av Fastighetsägaren.",
    "Ej aktuellt för Arrendestället.",
)
_ANSVAR_OPTS_FASTIGHETSAGARE_FIRST = (
    "Skall ombesörjas och bekostas av Fastighetsägaren.",
    "Skall ombesörjas och bekostas av Arrendatorn.",
    "Ej aktuellt för Arrendestället.",
)

SECTIONS_ARRENDE: list[Section] = [
    Section("Avtal", [
        FormField("driftstalle_nr", "Driftställenr", "text"),
        FormField("avtalsnummer", "Avtalsnummer", "text"),
        FormField("uppdragsgivarnr", "Uppdragsgivarnr", "text"),
    ]),
    Section("Fastighetsägare", [
        FormField("fastighetsagare_namn", "Namn", "text"),
        FormField("fastighetsagare_orgnr", "Org. nr", "text"),
        FormField("fastighetsagare_momsnr", "Momsregistreringsnummer (siffrorna mellan “SE” och “01”)", "text"),
    ]),
    Section("Arrendeställets adress", [
        FormField("arrendestalle_kommun", "Kommun", "text"),
        FormField("arrendestalle_fastighetsbeteckning", "Fastighetsbeteckning", "text"),
        FormField("arrendestalle_adress", "Adress", "text"),
    ]),
    Section("Arrendeställets omfattning", [
        FormField("antal_parkeringsplatser", "Antal fullgoda parkeringsplatser (ca)", "numeric"),
    ]),
    Section("Arrendeställets ändamål", [
        FormField("arrendestalle_sarskilda_villkor", "Särskilda villkor (t.ex. reklamupplåtelse)", "text"),
    ]),
    Section("Avtalstid", [
        FormField("avtal_start_datum", "Startdatum", "date", hint="format: ÅÅÅÅ-MM-DD"),
        FormField("avtal_slut_datum", "Slutdatum", "date", hint="format: ÅÅÅÅ-MM-DD"),
    ]),
    Section("Uppsägningstid och förlängningstid", [
        FormField("uppsagningstid_antal_ord", "Uppsägningstid, antal (i ord, t.ex. “tre”)", "text"),
        FormField("uppsagningstid_antal_siffror", "Uppsägningstid, antal (siffror, t.ex. “3”)", "numeric"),
        FormField("uppsagningstid_enhet", "Uppsägningstid, enhet", "select", select_options=("månader", "månad")),
        FormField("forlangningstid_antal_ord", "Förlängningstid, antal (i ord)", "select", select_options=("tre", "ett", "två", "fyra")),
        FormField("forlangningstid_antal_siffror", "Förlängningstid, antal (siffror)", "select", select_options=("3", "1", "2", "4", "5")),
        FormField("forlangningstid_enhet", "Förlängningstid, enhet", "select", select_options=("år", "månader", "månad")),
    ]),
    Section("Arrende", [
        FormField("arrende_procent_ord", "Procent av årsomsättning (i ord)", "text"),
        FormField("arrende_procent_siffror", "Procent av årsomsättning (siffror)", "numeric"),
    ]),
    Section("Erläggande av arrende", [
        FormField("faktureringsperiod", "Faktureringsperiod (självfaktura)", "select", select_options=("kalenderkvartal", "kalendermånad")),
        FormField("betalningssatt", "Betalningssätt", "select", select_options=("plusgiro", "bankgiro")),
        FormField("bankgiro_plusgiro_nr", "Bankgiro-/plusgironummer", "text"),
    ]),
    Section("Arbete å arrendestället", [
        FormField("arbete_a_arrendestallet_ersattning", "Ersättning vid hinder att nyttja parkeringsplatser", "text"),
    ]),
    Section("Parternas åtaganden - ansvarsfördelning", [
        FormField("ansvar_parkeringsovervakning", "Parkeringsövervakning", "select", select_options=_ANSVAR_OPTS_ARRENDATOR_FIRST),
        FormField("ansvar_kundservice_kontrollavgifter", "Kundservice för överklagande av kontrollavgifter", "select", select_options=_ANSVAR_OPTS_ARRENDATOR_FIRST),
        FormField("ansvar_uppfoljning_indrivning", "Uppföljning och indrivning av obetalda kontrollavgifter", "select", select_options=_ANSVAR_OPTS_ARRENDATOR_FIRST),
        FormField("ansvar_stadning", "Städning och renhållning", "select", select_options=_ANSVAR_OPTS_FASTIGHETSAGARE_FIRST),
        FormField("ansvar_uthyrning_langtid", "Uthyrning till och avisering av långtidskunder", "select", select_options=_ANSVAR_OPTS_ARRENDATOR_FIRST),
        FormField("ansvar_eldragning", "Framdragning av elström till laddstationer, skyltar, motorvärmare m.m.", "select", select_options=_ANSVAR_OPTS_FASTIGHETSAGARE_FIRST),
        FormField("ansvar_motorvarmare", "Installation, drift och underhåll av motorvärmare", "select", select_options=_ANSVAR_OPTS_FASTIGHETSAGARE_FIRST),
        FormField("ansvar_belysning", "Installation, drift och underhåll av belysning", "select", select_options=_ANSVAR_OPTS_FASTIGHETSAGARE_FIRST),
        FormField("ansvar_skyltprogram", "Installation, drift och underhåll av skyltprogram", "select",
                  select_options=("Skall ombesörjas och bekostas av Fastighetsägaren.", "Ej aktuellt för Arrendestället.", "Skall ombesörjas av Arrendatorn.")),
    ]),
    Section("Parkeringstillstånd och P-skivor", [
        FormField("parkeringstillstand", "Parkeringstillstånd", "radio", options=(
            ("parkeringstillstand_enligt_prislista", "Enligt Aimos prislista"),
            ("parkeringstillstand_ej_aktuellt", "Ej aktuellt"),
        )),
        FormField("pskivor", "P-skivor", "radio", options=(
            ("pskivor_enligt_taxa", "Enligt gällande taxa"),
            ("pskivor_ej_aktuellt", "Ej aktuellt"),
        )),
    ]),
    Section("Tidigare avtal", [
        FormField("tidigare_avtal", "Status", "radio", options=(
            ("nytt_avtal", "Nytt avtal"),
            ("ersatter_tidigare_avtal", "Ersätter tidigare avtal"),
        )),
        FormField("tidigare_avtal_datum1", "Tidigare avtal, datum 1", "date", hint="format: ÅÅÅÅ-MM-DD"),
        FormField("tidigare_avtal_datum2", "Tidigare avtal, datum 2", "date", hint="format: ÅÅÅÅ-MM-DD"),
    ]),
    Section("Bilagor (utöver Bilaga 1 - Ritningsbilaga)", [
        FormField("bilaga2_inkluderad", "Bilaga 2 ska inkluderas", "checkbox"),
        FormField("bilaga2_namn", "Bilaga 2, namn", "text"),
        FormField("bilaga2_nr", "Bilaga 2, nummer", "numeric"),
        FormField("bilaga3_inkluderad", "Bilaga 3 ska inkluderas", "checkbox"),
        FormField("bilaga3_namn", "Bilaga 3, namn", "text"),
        FormField("bilaga3_nr", "Bilaga 3, nummer", "numeric"),
        FormField("bilaga4_inkluderad", "Bilaga 4 ska inkluderas", "checkbox"),
        FormField("bilaga4_namn", "Bilaga 4, namn", "text"),
        FormField("bilaga4_nr", "Bilaga 4, nummer", "numeric"),
    ]),
    Section("Signering", [
        FormField("fastighetsagare_ort_datum", "Fastighetsägare: ort och datum", "text"),
        FormField("arrendator_datum", "Arrendatorn (Aimo): datum (ort är redan “Stockholm” i mallen)", "date", hint="format: ÅÅÅÅ-MM-DD"),
        FormField("fastighetsagare_namnfortydligande", "Fastighetsägare: namnförtydligande", "text"),
    ]),
    Section("Fastighetsägarens kontaktperson - redovisning", [
        FormField("fastighetsagare_kontakt_redovisning_namn", "Namn", "text"),
        FormField("fastighetsagare_kontakt_redovisning_mail", "Mailadress", "email"),
        FormField("fastighetsagare_kontakt_redovisning_tel", "Telefon", "text"),
        FormField("fastighetsagare_redovisningsadress", "Redovisningsadress (om annan än ovan)", "text"),
    ]),
    Section("Kontaktperson - drift", [
        FormField("fastighetsagare_kontakt_drift_namn", "Fastighetsägarens kontaktperson, namn", "text"),
        FormField("fastighetsagare_kontakt_drift_mail", "Fastighetsägarens kontaktperson, mailadress", "email"),
        FormField("fastighetsagare_kontakt_drift_tel", "Fastighetsägarens kontaktperson, telefon", "text"),
        FormField("arrendator_kontakt_drift_namn", "Arrendatorns kontaktperson, namn", "text"),
        FormField("arrendator_kontakt_drift_mail", "Arrendatorns kontaktperson, mailadress", "email"),
        FormField("arrendator_kontakt_drift_tel", "Arrendatorns kontaktperson, telefon", "text"),
    ]),
]
