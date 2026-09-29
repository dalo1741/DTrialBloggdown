#!/usr/bin/env python3
"""A fill-in-the-boxes form for generating the Aimo contract - no YAML
editing required.

Run it with:
    python3 contract_form.py

It opens a window with one tab per section of the contract. Fill in the
boxes (radio buttons for the either/or choices, a checkbox for the SIM-card
option), click "Generera", and pick where to save the result. Fields that
look empty or oddly formatted are flagged before generating, but you can
still choose to continue - the checks are a safety net, not a hard stop.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from fields import FIELDS
from form_fields import SECTIONS
from form_validation import validate_value, validate_radio
from generate_contract import fill_template, convert_to_pdf, LibreOfficeNotFound, DEFAULT_TEMPLATE

CHECKBOX_DEFAULTS = {f.field_id for f in FIELDS if f.kind == "checkbox"}


class ContractForm(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Aimo-avtal - generator")
        self.geometry("720x700")
        self.minsize(560, 400)

        self.entries: dict[str, tk.Entry] = {}
        self.radio_vars: dict[str, tk.StringVar] = {}
        self.check_vars: dict[str, tk.BooleanVar] = {}
        self.field_kind: dict[str, str] = {}
        self.field_label: dict[str, str] = {}

        # A scrollable form (one long page, section by section) instead of
        # tabs: with ~11 sections, a tab strip either overflows the window
        # or truncates its labels down to "Mo", "Fakt", "Bes" - unreadable.
        # Scrolling top-to-bottom also mirrors the paper contract's order.
        outer = ttk.Frame(self)
        outer.pack(fill="both", expand=True)

        canvas = tk.Canvas(outer, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        scrollbar.pack(side="right", fill="y", pady=8)

        inner = ttk.Frame(canvas)
        inner_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def on_inner_configure(_event: object) -> None:
            canvas.configure(scrollregion=canvas.bbox("all"))

        def on_canvas_configure(event: tk.Event) -> None:
            canvas.itemconfig(inner_id, width=event.width)

        inner.bind("<Configure>", on_inner_configure)
        canvas.bind("<Configure>", on_canvas_configure)

        def on_mousewheel(event: tk.Event) -> None:
            # Windows/Mac deliver <MouseWheel> with event.delta; X11/Linux
            # delivers wheel movement as Button-4 (up) / Button-5 (down).
            if event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")
            else:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", on_mousewheel)
        canvas.bind_all("<Button-4>", on_mousewheel)
        canvas.bind_all("<Button-5>", on_mousewheel)

        for section in SECTIONS:
            header = ttk.Label(inner, text=section.title, font=("TkDefaultFont", 11, "bold"))
            header.pack(fill="x", padx=6, pady=(14, 2), anchor="w")
            ttk.Separator(inner, orient="horizontal").pack(fill="x", padx=6, pady=(0, 6))
            self._build_section(inner, section)

        bottom = ttk.Frame(self)
        bottom.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(bottom, text="Generera avtal...", command=self.on_generate).pack(side="right")

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
            else:
                entry = ttk.Entry(section_frame, width=f.width)
                entry.grid(row=row, column=1, sticky="we", padx=6, pady=4)
                self.entries[f.field_id] = entry
                self.field_kind[f.field_id] = f.kind
                self.field_label[f.field_id] = f.label

        section_frame.columnconfigure(1, weight=1)

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
        for group_field_id, var in self.radio_vars.items():
            selected = var.get()
            section = next(s for s in SECTIONS for f in s.fields if f.field_id == group_field_id)
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
            section = next(s for s in SECTIONS for f in s.fields if f.field_id == group_field_id)
            form_field = next(f for f in section.fields if f.field_id == group_field_id)
            msg = validate_radio(form_field.label, var.get() or None)
            if msg:
                warnings.append(msg)
        return warnings

    def on_generate(self) -> None:
        warnings = self.collect_warnings()
        if warnings:
            # A long list (e.g. most fields still empty) would otherwise
            # grow the dialog past the screen, pushing its own Yes/No
            # buttons out of view - so cap what's shown.
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
            filetypes=[("Word-dokument", "*.docx")],
        )
        if not docx_path:
            return

        data = self.collect_data()
        try:
            from pathlib import Path
            unfilled = fill_template(DEFAULT_TEMPLATE, data, Path(docx_path))
        except Exception as exc:
            messagebox.showerror("Fel", f"Kunde inte skapa dokumentet:\n{exc}")
            return

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
                    from pathlib import Path
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
