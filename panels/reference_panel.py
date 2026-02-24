"""
panels/reference_panel.py — Right panel: reference list manager.
"""

import customtkinter as ctk
from tkinter import messagebox
import database as db
import citations as cite


class ReferencePanel(ctk.CTkFrame):
    """Right sidebar: IEEE reference list with add/edit/delete/search."""

    def __init__(self, master, get_thesis_id=None, **kwargs):
        super().__init__(master, **kwargs)
        self.get_thesis_id = get_thesis_id
        self.selected_ref_id = None
        self.configure(corner_radius=12)

        # ── Header ────────────────────────────────────────────────
        header = ctk.CTkLabel(
            self, text="📚  References (IEEE)",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w",
        )
        header.pack(fill="x", padx=14, pady=(14, 6))

        # ── Search ────────────────────────────────────────────────
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.refresh_references())
        search = ctk.CTkEntry(
            self, placeholder_text="🔍  Search references…",
            textvariable=self.search_var, height=34,
            font=ctk.CTkFont(size=13),
        )
        search.pack(fill="x", padx=14, pady=(0, 8))

        # ── Reference list ────────────────────────────────────────
        self.ref_list = ctk.CTkScrollableFrame(self)
        self.ref_list.pack(fill="both", expand=True, padx=14, pady=(0, 8))
        self.ref_widgets = []

        # ── Action buttons ────────────────────────────────────────
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", padx=14, pady=(0, 4))

        self.btn_add = ctk.CTkButton(
            actions, text="＋ Add", height=30,
            font=ctk.CTkFont(size=12),
            command=self._add_reference,
        )
        self.btn_add.pack(side="left", fill="x", expand=True, padx=(0, 3))

        self.btn_edit = ctk.CTkButton(
            actions, text="✏ Edit", height=30,
            font=ctk.CTkFont(size=12),
            fg_color="#F59E0B", hover_color="#D97706",
            command=self._edit_reference,
        )
        self.btn_edit.pack(side="left", fill="x", expand=True, padx=(0, 3))

        self.btn_del = ctk.CTkButton(
            actions, text="🗑 Del", height=30,
            font=ctk.CTkFont(size=12),
            fg_color="#EF4444", hover_color="#DC2626",
            command=self._delete_reference,
        )
        self.btn_del.pack(side="left", fill="x", expand=True)

        # ── Utility buttons ───────────────────────────────────────
        utils = ctk.CTkFrame(self, fg_color="transparent")
        utils.pack(fill="x", padx=14, pady=(4, 8))

        self.btn_copy = ctk.CTkButton(
            utils, text="📋 Copy Citation", height=30,
            font=ctk.CTkFont(size=12),
            fg_color="#8B5CF6", hover_color="#7C3AED",
            command=self._copy_citation,
        )
        self.btn_copy.pack(side="left", fill="x", expand=True, padx=(0, 3))

        self.btn_renumber = ctk.CTkButton(
            utils, text="🔢 Renumber", height=30,
            font=ctk.CTkFont(size=12),
            fg_color=("gray70", "gray35"), hover_color=("gray60", "gray45"),
            command=self._renumber,
        )
        self.btn_renumber.pack(side="left", fill="x", expand=True)

        # ── Parse input ───────────────────────────────────────────
        parse_frame = ctk.CTkFrame(self, fg_color="transparent")
        parse_frame.pack(fill="x", padx=14, pady=(0, 14))

        self.parse_entry = ctk.CTkEntry(
            parse_frame, placeholder_text="Paste IEEE ref to auto-parse…",
            height=32, font=ctk.CTkFont(size=12),
        )
        self.parse_entry.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.btn_parse = ctk.CTkButton(
            parse_frame, text="Parse", width=60, height=32,
            font=ctk.CTkFont(size=12),
            fg_color="#10B981", hover_color="#059669",
            command=self._parse_and_add,
        )
        self.btn_parse.pack(side="right")

    # ── Refresh ───────────────────────────────────────────────────

    def refresh_references(self):
        for w in self.ref_widgets:
            w.destroy()
        self.ref_widgets.clear()

        thesis_id = self._get_tid()
        if not thesis_id:
            return

        search = self.search_var.get().strip() or None
        refs = db.get_references(thesis_id, search_term=search)

        for ref in refs:
            ref_dict = dict(ref)
            ieee_text = cite.format_ieee(ref_dict)

            frame = ctk.CTkFrame(
                self.ref_list,
                fg_color=("#E0E7FF", "#1E293B") if ref["id"] != self.selected_ref_id
                else ("#3B82F6", "#2563EB"),
                corner_radius=8,
            )
            frame.pack(fill="x", pady=3)
            frame.bind("<Button-1>", lambda e, rid=ref["id"]: self._select_ref(rid))

            lbl = ctk.CTkLabel(
                frame, text=ieee_text, anchor="w",
                font=ctk.CTkFont(size=12),
                wraplength=300,
                text_color=("gray10", "gray90"),
            )
            lbl.pack(fill="x", padx=10, pady=8)
            lbl.bind("<Button-1>", lambda e, rid=ref["id"]: self._select_ref(rid))

            self.ref_widgets.append(frame)

    def _select_ref(self, ref_id):
        self.selected_ref_id = ref_id
        self.refresh_references()

    def _get_tid(self):
        if self.get_thesis_id:
            return self.get_thesis_id()
        return None

    # ── CRUD ──────────────────────────────────────────────────────

    def _add_reference(self):
        thesis_id = self._get_tid()
        if not thesis_id:
            messagebox.showwarning("No Thesis", "Select a thesis first.")
            return
        self._open_ref_editor(thesis_id)

    def _edit_reference(self):
        if not self.selected_ref_id:
            messagebox.showwarning("No Selection", "Select a reference first.")
            return
        thesis_id = self._get_tid()
        refs = db.get_references(thesis_id)
        ref = next((r for r in refs if r["id"] == self.selected_ref_id), None)
        if ref:
            self._open_ref_editor(thesis_id, dict(ref))

    def _delete_reference(self):
        if not self.selected_ref_id:
            messagebox.showwarning("No Selection", "Select a reference first.")
            return
        if messagebox.askyesno("Confirm", "Delete this reference?"):
            db.delete_reference(self.selected_ref_id)
            self.selected_ref_id = None
            self.refresh_references()

    def _copy_citation(self):
        if not self.selected_ref_id:
            messagebox.showwarning("No Selection", "Select a reference first.")
            return
        thesis_id = self._get_tid()
        refs = db.get_references(thesis_id)
        ref = next((r for r in refs if r["id"] == self.selected_ref_id), None)
        if ref:
            text = cite.format_ieee(dict(ref))
            cite.copy_to_clipboard(self.winfo_toplevel(), text)
            messagebox.showinfo("Copied", "Citation copied to clipboard!")

    def _renumber(self):
        thesis_id = self._get_tid()
        if not thesis_id:
            return
        db.renumber_references(thesis_id)
        self.refresh_references()

    def _parse_and_add(self):
        thesis_id = self._get_tid()
        if not thesis_id:
            messagebox.showwarning("No Thesis", "Select a thesis first.")
            return
        text = self.parse_entry.get().strip()
        if not text:
            return
        parsed = cite.parse_ieee(text)
        db.add_reference(
            thesis_id,
            ref_number=parsed.get("ref_number"),
            authors=parsed.get("authors", ""),
            title=parsed.get("title", ""),
            source=parsed.get("source", ""),
            year=parsed.get("year", ""),
            doi_url=parsed.get("doi_url", ""),
            ref_type=parsed.get("ref_type", "article"),
        )
        self.parse_entry.delete(0, "end")
        self.refresh_references()

    # ── Reference editor dialog ───────────────────────────────────

    def _open_ref_editor(self, thesis_id, existing=None):
        """Open a top-level dialog to add/edit a reference."""
        win = ctk.CTkToplevel(self.winfo_toplevel())
        win.title("Edit Reference" if existing else "Add Reference")
        win.geometry("500x520")
        win.resizable(False, False)
        win.grab_set()
        win.after(10, win.lift)

        fields = {}
        labels = [
            ("ref_number", "Ref Number [N]"),
            ("authors", "Authors"),
            ("title", "Title"),
            ("source", "Source / Journal"),
            ("year", "Year"),
            ("doi_url", "DOI / URL"),
        ]

        for key, label_text in labels:
            lbl = ctk.CTkLabel(win, text=label_text, font=ctk.CTkFont(size=13), anchor="w")
            lbl.pack(fill="x", padx=20, pady=(8, 0))
            entry = ctk.CTkEntry(win, height=34, font=ctk.CTkFont(size=13))
            entry.pack(fill="x", padx=20, pady=(2, 0))
            if existing and existing.get(key) is not None:
                entry.insert(0, str(existing[key]))
            fields[key] = entry

        # Ref type dropdown
        lbl = ctk.CTkLabel(win, text="Type", font=ctk.CTkFont(size=13), anchor="w")
        lbl.pack(fill="x", padx=20, pady=(8, 0))
        type_var = ctk.StringVar(value=existing.get("ref_type", "article") if existing else "article")
        type_menu = ctk.CTkOptionMenu(
            win, variable=type_var, values=cite.REF_TYPES,
            height=34, font=ctk.CTkFont(size=13),
        )
        type_menu.pack(fill="x", padx=20, pady=(2, 0))

        def _save():
            ref_num_text = fields["ref_number"].get().strip()
            ref_num = int(ref_num_text) if ref_num_text.isdigit() else None

            data = {
                "authors": fields["authors"].get().strip(),
                "title": fields["title"].get().strip(),
                "source": fields["source"].get().strip(),
                "year": fields["year"].get().strip(),
                "doi_url": fields["doi_url"].get().strip(),
                "ref_type": type_var.get(),
            }

            if existing:
                if ref_num is not None:
                    data["ref_number"] = ref_num
                db.update_reference(existing["id"], **data)
            else:
                db.add_reference(thesis_id, ref_number=ref_num, **data)

            win.destroy()
            self.refresh_references()

        btn_save = ctk.CTkButton(
            win, text="💾  Save Reference", height=38,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#10B981", hover_color="#059669",
            command=_save,
        )
        btn_save.pack(fill="x", padx=20, pady=(16, 12))

    # ── Public helpers ────────────────────────────────────────────

    def get_references_for_dropdown(self):
        """Return list of (id, display_text) for linking to resources."""
        thesis_id = self._get_tid()
        if not thesis_id:
            return []
        refs = db.get_references(thesis_id)
        return [(r["id"], f"[{r['ref_number']}] {r['title'][:40]}") for r in refs]
