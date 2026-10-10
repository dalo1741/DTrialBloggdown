#!/usr/bin/env python3
"""A fill-in-the-boxes form for generating Aimo contracts - no YAML editing
required, multiple contract types, local save/resume.

Run it with:
    python3 contract_form.py

Opens a window with a template picker first ("Välj avtalstyp"), then one
scrollable form per contract type (radio buttons for either/or choices, a
checkbox for yes/no options, a dropdown where the template restricts the
value to a fixed set). Click "Generera avtal...", pick where to save the
result. Fields that look empty or oddly formatted are flagged before
generating, but you can still choose to continue - the checks are a
safety net, not a hard stop.

Drafts are saved locally as JSON files under DRAFTS_DIR (one per draft,
under this user's home directory - see CLAUDE.md's Phase 3 desktop notes
for why: no shared backend here, unlike the web version's Artifact `db`).
"""

from __future__ import annotations

import json
import tkinter as tk
import uuid
from datetime import datetime, timezone
from pathlib import Path
from tkinter import ttk, filedialog, messagebox, simpledialog

from form_validation import validate_value, validate_radio
from generate_contract import fill_template_meta, convert_to_pdf, LibreOfficeNotFound
from templates import TEMPLATES, TemplateMeta

DRAFTS_DIR = Path.home() / "Aimo-avtal" / "utkast"

# Same values as SAMPLE_DATA/SAMPLE_DATA_HARDWARE/SAMPLE_DATA_ARRENDE in
# web/aimo_contract_form.html - keep in sync by hand if those change.
SAMPLE_DATA_BY_TEMPLATE: dict[str, dict] = {
    "aimo_charge_v1_2": {
        "party2_namn": "Exempelfastigheter AB", "party2_orgnr": "556000-0000",
        "aimo_ombud_namn": "Anna Andersson", "aimo_ombud_tel": "070-000 00 00",
        "aimo_ombud_epost": "anna.andersson@aimopark.se",
        "bestallare_adress": "Exempelvägen 1", "bestallare_postnummer": "123 45", "bestallare_ort": "Stockholm",
        "bestallare_ombud_namn": "Björn Björnsson", "bestallare_ombud_tel": "070-111 11 11",
        "bestallare_ombud_epost": "bjorn.bjornsson@exempelfastigheter.se",
        "faktura_epost": "faktura@exempelfastigheter.se", "faktura_adress": "Exempelvägen 1",
        "faktura_postnummer": "123 45", "faktura_ort": "Stockholm", "faktura_markning": "PO-12345",
        "sjalvfaktura_ombud_namn": "Björn Björnsson", "sjalvfaktura_ombud_tel": "070-111 11 11",
        "sjalvfaktura_ombud_epost": "bjorn.bjornsson@exempelfastigheter.se", "sjalvfaktura_bankgiro": "123-4567",
        "sjalvfaktura_epost": "sjalvfaktura@exempelfastigheter.se", "sjalvfaktura_markning": "PO-12345",
        "anlaggning_adress": "Exempelvägen 1", "anlaggning_postnummer": "123 45", "anlaggning_ort": "Stockholm",
        "anlaggning_fastighetsbeteckning": "Exempelfastigheten 1:1", "anlaggning_matare_id_suffix": "000000000000",
        "charge_antal_uttag": "10", "charge_pris_per_uttag": "295", "charge_summa_manad": "2 950",
        "startavgift_antal_uttag": "10", "startavgift_pris_per_uttag": "1 500", "startavgift_summa": "15 000",
        "summa_per_manad_total": "2 950", "summa_engangskostnad_total": "15 000",
        "konsument_pris_kwh": "4,50", "konsument_ersattning_procent": "10",
        "laddare_publika": "laddare_publika_ja",
        "sim_pris_per_manad": "89", "sim_ska_levereras": True, "sim_antal": "10", "sim_summa_manad": "890",
        "avtal_start_datum": "2026-01-01", "avtal_slut_datum": "2026-12-31",
        "betalning": "betalning_manadsvis",
    },
    "aimo_charge_hardware_v1_2": {
        "party2_namn": "Exempelfastigheter AB", "party2_orgnr": "556000-0000",
        "aimo_ombud_namn": "Anna Andersson", "aimo_ombud_tel": "070-000 00 00",
        "aimo_ombud_epost": "anna.andersson@aimopark.se",
        "bestallare_adress": "Exempelvägen 1", "bestallare_postnummer": "123 45", "bestallare_ort": "Stockholm",
        "bestallare_ombud_namn": "Björn Björnsson", "bestallare_ombud_tel": "070-111 11 11",
        "bestallare_ombud_epost": "bjorn.bjornsson@exempelfastigheter.se",
        "faktura_epost": "faktura@exempelfastigheter.se", "faktura_adress": "Exempelvägen 1",
        "faktura_postnummer": "123 45", "faktura_ort": "Stockholm", "faktura_markning": "PO-12345",
        "sjalvfaktura_ombud_namn": "Björn Björnsson", "sjalvfaktura_ombud_tel": "070-111 11 11",
        "sjalvfaktura_ombud_epost": "bjorn.bjornsson@exempelfastigheter.se", "sjalvfaktura_bankgiro": "123-4567",
        "sjalvfaktura_epost": "sjalvfaktura@exempelfastigheter.se", "sjalvfaktura_markning": "PO-12345",
        "anlaggning_adress": "Exempelvägen 1", "anlaggning_postnummer": "123 45", "anlaggning_ort": "Stockholm",
        "anlaggning_fastighetsbeteckning": "Exempelfastigheten 1:1", "anlaggning_matare_id_suffix": "000000000000",
        "charge_antal_uttag": "10", "charge_pris_per_uttag": "295", "charge_summa_manad": "2 950",
        "startavgift_antal_uttag": "10", "startavgift_pris_per_uttag": "1 500", "startavgift_summa": "15 000",
        "summa_per_manad_total": "2 950", "summa_engangskostnad_total": "15 000",
        "konsument_pris_kwh": "4,50", "konsument_ersattning_procent": "10",
        "laddare_publika": "laddare_publika_ja",
        "hardvara_kostnad": "85 000", "installation_kostnad": "25 000", "tillbehor_kostnad": "5 000",
        "totalkostnad": "115 000", "antal_laddboxar": "5", "antal_ladduttag": "10",
        "sim_pris_per_manad": "89", "sim_ska_levereras": True, "sim_antal": "10", "sim_summa_manad": "890",
        "bidrag_ladda_bilen_kostnad": "0", "bidrag_klimatklivet_kostnad": "0",
        "bidrag_slutrapportering_kostnad": "0", "arlig_kontroll": True, "arlig_kontroll_kostnad": "1 200",
        "avtal_start_datum": "2026-01-01", "avtal_slut_datum": "2026-12-31",
        "betalning": "betalning_manadsvis",
    },
    "arrende_omsattning_v1": {
        "driftstalle_nr": "4711", "avtalsnummer": "A-2026-001", "uppdragsgivarnr": "99001",
        "fastighetsagare_namn": "Exempelfastigheter AB", "fastighetsagare_orgnr": "556000-0000",
        "fastighetsagare_momsnr": "5560000000",
        "arrendestalle_kommun": "Stockholm", "arrendestalle_fastighetsbeteckning": "Exempelkvarteret 1",
        "arrendestalle_adress": "Exempelvägen 1", "antal_parkeringsplatser": "120",
        "arrendestalle_sarskilda_villkor": "Inga särskilda villkor.",
        "avtal_start_datum": "2026-01-01", "avtal_slut_datum": "2028-12-31",
        "uppsagningstid_antal_ord": "tre", "uppsagningstid_antal_siffror": "3", "uppsagningstid_enhet": "månader",
        "forlangningstid_antal_ord": "ett", "forlangningstid_antal_siffror": "1", "forlangningstid_enhet": "år",
        "arrende_procent_ord": "tio", "arrende_procent_siffror": "10",
        "faktureringsperiod": "kalendermånad", "betalningssatt": "bankgiro", "bankgiro_plusgiro_nr": "123-4567",
        "arbete_a_arrendestallet_ersattning": "Fastighetsägaren skall ersätta Arrendatorn enligt gällande månadshyra.",
        "ansvar_parkeringsovervakning": "Skall ombesörjas och bekostas av Arrendatorn.",
        "ansvar_kundservice_kontrollavgifter": "Skall ombesörjas och bekostas av Arrendatorn.",
        "ansvar_uppfoljning_indrivning": "Skall ombesörjas och bekostas av Arrendatorn.",
        "ansvar_stadning": "Skall ombesörjas och bekostas av Fastighetsägaren.",
        "ansvar_uthyrning_langtid": "Skall ombesörjas och bekostas av Arrendatorn.",
        "ansvar_eldragning": "Skall ombesörjas och bekostas av Fastighetsägaren.",
        "ansvar_motorvarmare": "Skall ombesörjas och bekostas av Fastighetsägaren.",
        "ansvar_belysning": "Skall ombesörjas och bekostas av Fastighetsägaren.",
        "ansvar_skyltprogram": "Skall ombesörjas och bekostas av Fastighetsägaren.",
        "parkeringstillstand": "parkeringstillstand_enligt_prislista", "pskivor": "pskivor_ej_aktuellt",
        "tidigare_avtal": "nytt_avtal",
        "fastighetsagare_ort_datum": "Stockholm, 2026-01-01", "arrendator_datum": "2026-01-01",
        "fastighetsagare_namnfortydligande": "Anna Andersson",
        "fastighetsagare_kontakt_redovisning_namn": "Anna Andersson",
        "fastighetsagare_kontakt_redovisning_mail": "anna.andersson@exempelfastigheter.se",
        "fastighetsagare_kontakt_redovisning_tel": "070-000 00 00",
        "fastighetsagare_redovisningsadress": "Exempelvägen 1, 123 45 Stockholm",
        "fastighetsagare_kontakt_drift_namn": "Björn Björnsson",
        "fastighetsagare_kontakt_drift_mail": "bjorn.bjornsson@exempelfastigheter.se",
        "fastighetsagare_kontakt_drift_tel": "070-111 11 11",
        "arrendator_kontakt_drift_namn": "Carl Carlsson",
        "arrendator_kontakt_drift_mail": "carl.carlsson@aimopark.se", "arrendator_kontakt_drift_tel": "08-722 15 00",
    },
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ContractForm(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Aimo-avtal - generator")
        self.geometry("780x760")
        self.minsize(560, 400)

        self.current_template: TemplateMeta | None = None
        self.current_draft_path: Path | None = None
        self.current_draft_created_at: str | None = None

        self.entries: dict[str, tk.Entry] = {}
        self.radio_vars: dict[str, tk.StringVar] = {}
        self.check_vars: dict[str, tk.BooleanVar] = {}
        self.select_vars: dict[str, tk.StringVar] = {}
        self.field_kind: dict[str, str] = {}
        self.field_label: dict[str, str] = {}

        self._build_topbar()

        self.container = ttk.Frame(self)
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.picker_frame = ttk.Frame(self.container)
        self.list_frame = ttk.Frame(self.container)
        self.form_outer = ttk.Frame(self.container)
        for f in (self.picker_frame, self.list_frame, self.form_outer):
            f.grid(row=0, column=0, sticky="nsew")

        self._build_picker()
        self._build_list_view()
        self._build_form_shell()

        self.show_picker()

    # ---------- topbar (always visible) ----------
    def _build_topbar(self) -> None:
        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=8, pady=6)
        self.template_label_var = tk.StringVar(value="Ingen avtalstyp vald")
        ttk.Label(bar, textvariable=self.template_label_var, font=("TkDefaultFont", 10, "bold")).pack(side="left")

        ttk.Button(bar, text="Generera avtal...", command=self.on_generate).pack(side="right")
        self.example_btn = ttk.Button(bar, text="Fyll i exempel", command=self.fill_example)
        self.example_btn.pack(side="right", padx=4)
        self.save_btn = ttk.Button(bar, text="Spara utkast", command=self.save_draft)
        self.save_btn.pack(side="right", padx=4)
        ttk.Button(bar, text="Mina avtal", command=self.show_list).pack(side="right", padx=4)
        ttk.Button(bar, text="Välj avtalstyp", command=self.show_picker).pack(side="right", padx=4)

    def _set_form_buttons_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        self.example_btn.configure(state=state)
        self.save_btn.configure(state=state)

    # ---------- view switching ----------
    def show_picker(self) -> None:
        self.current_template = None
        self.current_draft_path = None
        self.current_draft_created_at = None
        self.template_label_var.set("Ingen avtalstyp vald")
        self._set_form_buttons_enabled(False)
        self.picker_frame.tkraise()

    def show_list(self) -> None:
        self._refresh_list()
        self.list_frame.tkraise()

    def show_form(self) -> None:
        self.form_outer.tkraise()

    # ---------- template picker ----------
    def _build_picker(self) -> None:
        ttk.Label(self.picker_frame, text="Välj avtalstyp", font=("TkDefaultFont", 13, "bold")).pack(
            anchor="w", padx=12, pady=(14, 6)
        )
        for template_id, meta in TEMPLATES.items():
            card = ttk.Frame(self.picker_frame, relief="groove", borderwidth=1)
            card.pack(fill="x", padx=12, pady=6)
            ttk.Label(card, text=meta.name, font=("TkDefaultFont", 11, "bold")).pack(anchor="w", padx=10, pady=(8, 2))
            ttk.Label(card, text=meta.description, wraplength=600).pack(anchor="w", padx=10, pady=(0, 8))
            ttk.Button(
                card, text="Välj", command=lambda tid=template_id: self.select_template(tid)
            ).pack(anchor="e", padx=10, pady=(0, 8))

    def select_template(self, template_id: str) -> None:
        self.current_template = TEMPLATES[template_id]
        self.current_draft_path = None
        self.current_draft_created_at = None
        self.template_label_var.set(self.current_template.name)
        self._build_sections(self.current_template)
        self.populate_form({})
        self._set_form_buttons_enabled(True)
        self.show_form()

    # ---------- dynamic form (rebuilt per template) ----------
    def _build_form_shell(self) -> None:
        # Scrollable form (one long page, section by section) - see the
        # original single-template version's comment for why not tabs.
        canvas = tk.Canvas(self.form_outer, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.form_outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        scrollbar.pack(side="right", fill="y", pady=8)

        self.sections_inner = ttk.Frame(canvas)
        inner_id = canvas.create_window((0, 0), window=self.sections_inner, anchor="nw")

        def on_inner_configure(_event: object) -> None:
            canvas.configure(scrollregion=canvas.bbox("all"))

        def on_canvas_configure(event: tk.Event) -> None:
            canvas.itemconfig(inner_id, width=event.width)

        self.sections_inner.bind("<Configure>", on_inner_configure)
        canvas.bind("<Configure>", on_canvas_configure)

        def on_mousewheel(event: tk.Event) -> None:
            if event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")
            else:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", on_mousewheel)
        canvas.bind_all("<Button-4>", on_mousewheel)
        canvas.bind_all("<Button-5>", on_mousewheel)

    def _build_sections(self, template: TemplateMeta) -> None:
        for child in self.sections_inner.winfo_children():
            child.destroy()
        self.entries.clear()
        self.radio_vars.clear()
        self.check_vars.clear()
        self.select_vars.clear()
        self.field_kind.clear()
        self.field_label.clear()

        for section in template.sections:
            header = ttk.Label(self.sections_inner, text=section.title, font=("TkDefaultFont", 11, "bold"))
            header.pack(fill="x", padx=6, pady=(14, 2), anchor="w")
            ttk.Separator(self.sections_inner, orient="horizontal").pack(fill="x", padx=6, pady=(0, 6))
            self._build_section(self.sections_inner, section)

    def _build_section(self, parent: ttk.Frame, section) -> None:
        section_frame = ttk.Frame(parent)
        section_frame.pack(fill="x")

        for row, f in enumerate(section.fields):
            label_text = f.label + (f"  ({f.hint})" if f.hint else "")
            ttk.Label(section_frame, text=label_text).grid(row=row, column=0, sticky="w", padx=6, pady=4)

            if f.kind == "radio":
                var = tk.StringVar(value="")
                self.radio_vars[f.field_id] = var
                self.field_label[f.field_id] = f.label
                radio_frame = ttk.Frame(section_frame)
                radio_frame.grid(row=row, column=1, sticky="w", padx=6, pady=4)
                for option_id, option_label in f.options:
                    ttk.Radiobutton(
                        radio_frame, text=option_label, variable=var, value=option_id
                    ).pack(side="left")
            elif f.kind == "checkbox":
                var = tk.BooleanVar(value=False)
                self.check_vars[f.field_id] = var
                ttk.Checkbutton(section_frame, variable=var).grid(row=row, column=1, sticky="w", padx=6, pady=4)
            elif f.kind == "select":
                var = tk.StringVar(value=f.select_options[0] if f.select_options else "")
                self.select_vars[f.field_id] = var
                combo = ttk.Combobox(
                    section_frame, textvariable=var, values=f.select_options, state="readonly", width=f.width
                )
                combo.grid(row=row, column=1, sticky="we", padx=6, pady=4)
            else:
                entry = ttk.Entry(section_frame, width=f.width)
                entry.grid(row=row, column=1, sticky="we", padx=6, pady=4)
                self.entries[f.field_id] = entry
                self.field_kind[f.field_id] = f.kind
                self.field_label[f.field_id] = f.label

        section_frame.columnconfigure(1, weight=1)

    # ---------- data in/out ----------
    def collect_data(self) -> dict:
        data: dict = {}
        for field_id, entry in self.entries.items():
            value = entry.get().strip()
            if value:
                # Leave empty boxes out entirely: fill_template() falls
                # back to the template's own placeholder (XXX/DATUM) for
                # any field_id missing from data, which stays visible as
                # a "still needs filling in" marker. Setting an empty
                # string instead would blank it out silently.
                data[field_id] = value
        for field_id, var in self.check_vars.items():
            data[field_id] = var.get()
        for field_id, var in self.select_vars.items():
            data[field_id] = var.get()
        for group_field_id, var in self.radio_vars.items():
            selected = var.get()
            section = next(s for s in self.current_template.sections for f in s.fields if f.field_id == group_field_id)
            form_field = next(f for f in section.fields if f.field_id == group_field_id)
            for option_id, _ in form_field.options:
                data[option_id] = (option_id == selected)
        return data

    def collect_warnings(self) -> list[str]:
        warnings: list[str] = []
        for field_id, entry in self.entries.items():
            kind = self.field_kind[field_id]
            label = self.field_label[field_id]
            msg = validate_value(kind, label, entry.get())
            if msg:
                warnings.append(msg)
        for group_field_id, var in self.radio_vars.items():
            section = next(s for s in self.current_template.sections for f in s.fields if f.field_id == group_field_id)
            form_field = next(f for f in section.fields if f.field_id == group_field_id)
            msg = validate_radio(form_field.label, var.get() or None)
            if msg:
                warnings.append(msg)
        return warnings

    def populate_form(self, data: dict) -> None:
        """Resets every field to `data` (or blank/unchecked/first-option
        when a field is absent from it) - used both for "Fyll i exempel"
        and for resuming a saved draft, so stale values left over from
        whatever was in the form before don't survive the switch."""
        for section in self.current_template.sections:
            for f in section.fields:
                if f.kind == "radio":
                    selected = data.get(f.field_id)
                    self.radio_vars[f.field_id].set(selected or "")
                elif f.kind == "checkbox":
                    self.check_vars[f.field_id].set(bool(data.get(f.field_id, False)))
                elif f.kind == "select":
                    value = data.get(f.field_id)
                    self.select_vars[f.field_id].set(value if value else (f.select_options[0] if f.select_options else ""))
                else:
                    entry = self.entries[f.field_id]
                    entry.delete(0, tk.END)
                    if f.field_id in data:
                        entry.insert(0, str(data[f.field_id]))

    def fill_example(self) -> None:
        sample = SAMPLE_DATA_BY_TEMPLATE.get(self.current_template.template_id)
        if sample:
            self.populate_form(sample)
        else:
            messagebox.showinfo("Inget exempel", "Det finns inget exempel för den här avtalstypen än.")

    # ---------- local drafts (Mina avtal) ----------
    def _build_list_view(self) -> None:
        ttk.Label(self.list_frame, text="Mina avtal", font=("TkDefaultFont", 13, "bold")).pack(
            anchor="w", padx=12, pady=(14, 6)
        )
        columns = ("typ", "updated", "status")
        self.list_tree = ttk.Treeview(self.list_frame, columns=columns, show="tree headings", height=18)
        self.list_tree.heading("#0", text="Namn")
        self.list_tree.heading("typ", text="Typ")
        self.list_tree.heading("updated", text="Senast ändrad")
        self.list_tree.heading("status", text="Status")
        self.list_tree.column("#0", width=240)
        self.list_tree.column("typ", width=220)
        self.list_tree.column("updated", width=160)
        self.list_tree.column("status", width=80)
        self.list_tree.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        btn_row = ttk.Frame(self.list_frame)
        btn_row.pack(fill="x", padx=12, pady=(0, 12))
        ttk.Button(btn_row, text="Öppna", command=self._open_selected_draft).pack(side="left")
        ttk.Button(btn_row, text="Ta bort", command=self._delete_selected_draft).pack(side="left", padx=6)
        ttk.Label(
            btn_row,
            text=f"Sparas lokalt i {DRAFTS_DIR} - inte delat med kollegor.",
            foreground="#666666",
        ).pack(side="left", padx=12)

    def _list_draft_files(self) -> list[Path]:
        if not DRAFTS_DIR.is_dir():
            return []
        return sorted(DRAFTS_DIR.glob("*.json"))

    def _refresh_list(self) -> None:
        self.list_tree.delete(*self.list_tree.get_children())
        drafts = []
        for path in self._list_draft_files():
            try:
                draft = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            drafts.append((path, draft))
        drafts.sort(key=lambda pd: pd[1].get("updatedAt", ""), reverse=True)

        for path, draft in drafts:
            template = TEMPLATES.get(draft.get("templateId"))
            type_label = template.name if template else (draft.get("templateId") or "–")
            status_label = "Klar" if draft.get("status") == "final" else "Utkast"
            updated = draft.get("updatedAt", "")[:16].replace("T", " ")
            self.list_tree.insert(
                "", "end", iid=str(path),
                text=draft.get("name", "(utan namn)"),
                values=(type_label, updated, status_label),
            )

    def _open_selected_draft(self) -> None:
        selection = self.list_tree.selection()
        if not selection:
            return
        path = Path(selection[0])
        try:
            draft = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            messagebox.showerror("Fel", f"Kunde inte läsa utkastet:\n{exc}")
            return
        template = TEMPLATES.get(draft.get("templateId"))
        if template is None:
            messagebox.showerror("Fel", f"Okänd avtalstyp: {draft.get('templateId')!r}")
            return
        self.current_template = template
        self.current_draft_path = path
        self.current_draft_created_at = draft.get("createdAt")
        self.template_label_var.set(template.name)
        self._build_sections(template)
        self.populate_form(draft.get("data", {}))
        self._set_form_buttons_enabled(True)
        self.show_form()

    def _delete_selected_draft(self) -> None:
        selection = self.list_tree.selection()
        if not selection:
            return
        path = Path(selection[0])
        if not messagebox.askyesno("Ta bort", "Ta bort det här utkastet permanent?"):
            return
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            messagebox.showerror("Fel", f"Kunde inte ta bort utkastet:\n{exc}")
            return
        if self.current_draft_path == path:
            self.current_draft_path = None
        self._refresh_list()

    def save_draft(self) -> None:
        if self.current_template is None:
            return
        hint_field = self.current_template.name_hint_field
        suggested = ""
        if hint_field in self.entries:
            suggested = self.entries[hint_field].get().strip()
        suggested = suggested or "Namnlöst avtal"
        suggested = f"{suggested} - {datetime.now().strftime('%Y-%m-%d')}"

        name = simpledialog.askstring("Spara utkast", "Namn på avtalet:", initialvalue=suggested, parent=self)
        if not name:
            return

        now = _now_iso()
        draft = {
            "name": name,
            "templateId": self.current_template.template_id,
            "status": "draft",
            "data": self.collect_data(),
            "createdAt": self.current_draft_created_at or now,
            "updatedAt": now,
        }
        path = self.current_draft_path or (DRAFTS_DIR / f"{uuid.uuid4().hex}.json")
        DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8")
        self.current_draft_path = path
        self.current_draft_created_at = draft["createdAt"]
        messagebox.showinfo("Sparat", f"Utkastet “{name}” är sparat.")

    def _mark_current_draft_final(self) -> None:
        if self.current_draft_path is None:
            return
        try:
            draft = json.loads(self.current_draft_path.read_text(encoding="utf-8"))
            draft["status"] = "final"
            draft["updatedAt"] = _now_iso()
            self.current_draft_path.write_text(json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8")
        except (OSError, json.JSONDecodeError):
            pass  # non-fatal: the document already generated successfully

    # ---------- generate ----------
    def on_generate(self) -> None:
        if self.current_template is None:
            messagebox.showinfo("Välj avtalstyp", "Välj en avtalstyp innan du genererar ett avtal.")
            return

        warnings = self.collect_warnings()
        if warnings:
            max_shown = 15
            shown = warnings[:max_shown]
            more = len(warnings) - len(shown)
            body = "\n".join(f"- {w}" for w in shown)
            if more:
                body += f"\n... och {more} till"
            proceed = messagebox.askyesno(
                "Kontrollera fälten",
                f"{len(warnings)} fält kan behöva ses över:\n\n{body}\n\nFortsätta ändå?",
            )
            if not proceed:
                return

        docx_path = filedialog.asksaveasfilename(
            title="Spara .docx som",
            defaultextension=".docx",
            initialfile=self.current_template.output_filename,
            filetypes=[("Word-dokument", "*.docx")],
        )
        if not docx_path:
            return

        data = self.collect_data()
        try:
            unfilled = fill_template_meta(self.current_template, data, Path(docx_path))
        except Exception as exc:
            messagebox.showerror("Fel", f"Kunde inte skapa dokumentet:\n{exc}")
            return

        self._mark_current_draft_final()

        pdf_message = ""
        make_pdf = messagebox.askyesno("PDF", "Försöka skapa en PDF också (kräver LibreOffice)?")
        if make_pdf:
            pdf_path = filedialog.asksaveasfilename(
                title="Spara .pdf som",
                defaultextension=".pdf",
                filetypes=[("PDF", "*.pdf")],
            )
            if pdf_path:
                try:
                    convert_to_pdf(Path(docx_path), Path(pdf_path))
                    pdf_message = f"\nPDF sparad: {pdf_path}"
                except LibreOfficeNotFound:
                    pdf_message = (
                        "\n\nLibreOffice hittades inte, så ingen PDF skapades. "
                        "Öppna .docx-filen i Word och använd Arkiv > Spara som > PDF."
                    )
                except Exception as exc:
                    pdf_message = f"\n\nPDF-export misslyckades: {exc}"

        note = ""
        if unfilled:
            note = "\n\nOifyllda fält (lämnades som platshållare):\n" + "\n".join(f"- {u}" for u in unfilled)

        messagebox.showinfo("Klart", f"Word-dokument sparat: {docx_path}{pdf_message}{note}")


if __name__ == "__main__":
    ContractForm().mainloop()
