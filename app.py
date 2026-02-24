"""
app.py — Thesis Resource Manager
A simple, modern desktop tool to collect paragraphs with their IEEE references,
organise by category/page, and maintain a reference list — all from one window.
"""

import sys
import os
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import customtkinter as ctk
from tkinter import filedialog, messagebox, colorchooser

import database as db
import citations as cite
import file_handler as fh

# ── Appearance ────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

MEDIA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "media")


class App(ctk.CTk):
    """Single-window thesis resource manager."""

    WIDTH = 680
    HEIGHT = 640

    def __init__(self):
        super().__init__()
        self.title("Thesis Resource Manager")
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.minsize(500, 500)
        self._center()
        db.init_db()

        self.current_thesis_id = None
        self.editing_id = None  # resource being edited

        self._build_ui()
        self._refresh_thesis_menu()
        self._refresh_category_menu()
        self._refresh_list()

    # ══════════════════════════════════════════════════════════════
    #  UI CONSTRUCTION
    # ══════════════════════════════════════════════════════════════

    def _build_ui(self):
        # ── Top bar ───────────────────────────────────────────────
        top = ctk.CTkFrame(self, height=40, corner_radius=0,
                           fg_color=("#CBD5E1", "#0F172A"))
        top.pack(fill="x")
        top.pack_propagate(False)

        ctk.CTkLabel(top, text="🎓  Thesis Resource Manager",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(
            side="left", padx=10)

        # theme toggle
        self.theme_var = ctk.StringVar(value="dark")
        ctk.CTkSwitch(top, text="🌙", variable=self.theme_var,
                       onvalue="dark", offvalue="light",
                       command=lambda: ctk.set_appearance_mode(
                           self.theme_var.get()),
                       width=40).pack(side="right", padx=10)

        # ── Global scrollable container ──────────────────────────
        self.scroll_container = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
        )
        self.scroll_container.pack(fill="both", expand=True, padx=0, pady=0)

        # ── Thesis selector row ──────────────────────────────────
        thesis_row = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        thesis_row.pack(fill="x", padx=16, pady=(10, 0))

        ctk.CTkLabel(thesis_row, text="Thesis / Paper:",
                     font=ctk.CTkFont(size=13)).pack(side="left", padx=(0, 6))

        self.thesis_var = ctk.StringVar(value="— select —")
        self.thesis_menu = ctk.CTkOptionMenu(
            thesis_row, variable=self.thesis_var,
            values=["— select —"], width=220, height=30,
            command=self._on_thesis_selected,
            font=ctk.CTkFont(size=12),
        )
        self.thesis_menu.pack(side="left", padx=(0, 6))

        ctk.CTkButton(thesis_row, text="＋", width=30, height=28,
                       font=ctk.CTkFont(size=12),
                       command=self._add_thesis).pack(side="left", padx=(0, 3))
        ctk.CTkButton(thesis_row, text="📄", width=30, height=28,
                       fg_color="#10B981", hover_color="#059669",
                       font=ctk.CTkFont(size=12),
                       command=self._open_thesis_file).pack(side="left", padx=(0, 3))
        ctk.CTkButton(thesis_row, text="🗑", width=30, height=28,
                       fg_color="#EF4444", hover_color="#DC2626",
                       command=self._delete_thesis).pack(side="left")

        # ── Main card (input area) ────────────────────────────────
        card = ctk.CTkFrame(self.scroll_container, corner_radius=12)
        card.pack(fill="x", padx=16, pady=10)

        # Paragraph
        ctk.CTkLabel(card, text="Paragraph / Snippet",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     anchor="w").pack(fill="x", padx=14, pady=(12, 2))

        self.para_box = ctk.CTkTextbox(card, height=80,
                                        font=ctk.CTkFont(size=12),
                                        corner_radius=8)
        self.para_box.pack(fill="x", padx=12)

        paste_row = ctk.CTkFrame(card, fg_color="transparent")
        paste_row.pack(fill="x", padx=14, pady=(2, 6))
        ctk.CTkButton(paste_row, text="📋 Paste", height=26, width=70,
                       font=ctk.CTkFont(size=11),
                       fg_color=("gray70", "gray35"),
                       command=self._paste).pack(side="right")

        # Reference text + style selector
        ref_header = ctk.CTkFrame(card, fg_color="transparent")
        ref_header.pack(fill="x", padx=14, pady=(2, 2))
        ctk.CTkLabel(ref_header, text="Reference",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     anchor="w").pack(side="left")
        self.style_var = ctk.StringVar(value="IEEE")
        ctk.CTkOptionMenu(ref_header, variable=self.style_var,
                           values=cite.CITATION_STYLES, width=80, height=26,
                           font=ctk.CTkFont(size=11),
                           command=lambda _: self._refresh_ref_list()
                           ).pack(side="right")

        self.ref_box = ctk.CTkTextbox(card, height=45,
                                       font=ctk.CTkFont(size=12),
                                       corner_radius=8)
        self.ref_box.pack(fill="x", padx=12)

        # Page + Category row
        opts = ctk.CTkFrame(card, fg_color="transparent")
        opts.pack(fill="x", padx=14, pady=(8, 4))

        ctk.CTkLabel(opts, text="Page", font=ctk.CTkFont(size=12)).pack(
            side="left", padx=(0, 4))
        self.page_entry = ctk.CTkEntry(opts, width=70, height=30,
                                        placeholder_text="e.g. 12",
                                        font=ctk.CTkFont(size=12))
        self.page_entry.pack(side="left", padx=(0, 16))

        ctk.CTkLabel(opts, text="Category", font=ctk.CTkFont(size=12)).pack(
            side="left", padx=(0, 4))
        self.cat_var = ctk.StringVar(value="General")
        self.cat_menu = ctk.CTkOptionMenu(opts, variable=self.cat_var,
                                           values=["General"], width=150,
                                           height=30,
                                           font=ctk.CTkFont(size=12))
        self.cat_menu.pack(side="left", padx=(0, 8))
        ctk.CTkButton(opts, text="＋", width=28, height=28,
                       font=ctk.CTkFont(size=12),
                       command=self._add_category).pack(side="left")

        # Attach PDF + Reference URL
        attach_row = ctk.CTkFrame(card, fg_color="transparent")
        attach_row.pack(fill="x", padx=14, pady=(2, 4))
        self.pdf_path = None
        ctk.CTkButton(attach_row, text="📄 Attach PDF", height=26,
                       width=100, font=ctk.CTkFont(size=11),
                       fg_color="#8B5CF6", hover_color="#7C3AED",
                       command=self._attach_pdf).pack(side="left", padx=(0, 6))
        self.pdf_label = ctk.CTkLabel(attach_row, text="",
                                       font=ctk.CTkFont(size=11),
                                       text_color="gray50")
        self.pdf_label.pack(side="left")

        url_row = ctk.CTkFrame(card, fg_color="transparent")
        url_row.pack(fill="x", padx=14, pady=(0, 4))
        ctk.CTkLabel(url_row, text="Ref URL", font=ctk.CTkFont(size=11)).pack(
            side="left", padx=(0, 4))
        self.url_entry = ctk.CTkEntry(url_row, height=28,
                                       placeholder_text="https://doi.org/...",
                                       font=ctk.CTkFont(size=11))
        self.url_entry.pack(side="left", fill="x", expand=True)

        # Save / Clear
        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=14, pady=(6, 14))
        self.save_btn = ctk.CTkButton(
            btn_row, text="💾  Save", height=38,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#10B981", hover_color="#059669",
            command=self._save)
        self.save_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(btn_row, text="Clear", height=38, width=80,
                       fg_color="#EF4444", hover_color="#DC2626",
                       font=ctk.CTkFont(size=13),
                       command=self._clear_form).pack(side="right")

        # ── Tabs: Resources | References ──────────────────────────
        self.tabs = ctk.CTkTabview(self.scroll_container, corner_radius=10,
                                    height=350)
        self.tabs.pack(fill="x", padx=14, pady=(0, 10))
        self.tab_res = self.tabs.add("📝 Resources")
        self.tab_ref = self.tabs.add("📚 References")

        # Resources tab — search + list
        search_row = ctk.CTkFrame(self.tab_res, fg_color="transparent")
        search_row.pack(fill="x", pady=(0, 4))
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._refresh_list())
        ctk.CTkEntry(search_row, textvariable=self.search_var,
                      placeholder_text="🔍 Search resources…",
                      height=30, font=ctk.CTkFont(size=12)).pack(
            fill="x", side="left", expand=True)

        self.res_scroll = ctk.CTkScrollableFrame(self.tab_res, height=260)
        self.res_scroll.pack(fill="both", expand=True)
        self.res_widgets = []

        # References tab — list
        ref_top = ctk.CTkFrame(self.tab_ref, fg_color="transparent")
        ref_top.pack(fill="x", pady=(0, 4))
        self.ref_search_var = ctk.StringVar()
        self.ref_search_var.trace_add("write", lambda *_: self._refresh_ref_list())
        ctk.CTkEntry(ref_top, textvariable=self.ref_search_var,
                      placeholder_text="🔍 Search references…",
                      height=30, font=ctk.CTkFont(size=12)).pack(
            fill="x", side="left", expand=True, padx=(0, 6))
        ctk.CTkButton(ref_top, text="🔢 Renumber", height=28, width=90,
                       font=ctk.CTkFont(size=11),
                       fg_color=("gray70", "gray35"),
                       command=self._renumber_refs).pack(side="right")

        self.ref_scroll = ctk.CTkScrollableFrame(self.tab_ref)
        self.ref_scroll.pack(fill="both", expand=True)
        self.ref_widgets = []

        # Keyboard shortcut
        self.bind("<Control-s>", lambda e: self._save())

    # ══════════════════════════════════════════════════════════════
    #  THESIS
    # ══════════════════════════════════════════════════════════════

    def _thesis_map(self):
        """Return {display_name: thesis_row}."""
        return {t["title"]: t for t in db.get_all_theses()}

    def _refresh_thesis_menu(self):
        tmap = self._thesis_map()
        names = list(tmap.keys()) or ["— select —"]
        self.thesis_menu.configure(values=names)
        if self.current_thesis_id:
            t = next((t for t in tmap.values()
                      if t["id"] == self.current_thesis_id), None)
            if t:
                self.thesis_var.set(t["title"])

    def _on_thesis_selected(self, name):
        tmap = self._thesis_map()
        t = tmap.get(name)
        self.current_thesis_id = t["id"] if t else None
        self._refresh_category_menu()
        self._refresh_list()
        self._refresh_ref_list()

    def _add_thesis(self):
        d = ctk.CTkInputDialog(text="Thesis / paper title:", title="New Thesis")
        title = d.get_input()
        if not title:
            return
        path = filedialog.askopenfilename(
            title="Attach source file (optional)",
            filetypes=fh.get_supported_file_types())
        ftype = fh.get_file_type(path) if path else None
        tid = db.add_thesis(title, path or None, ftype)
        self.current_thesis_id = tid
        self._refresh_thesis_menu()
        self._refresh_list()
        self._refresh_ref_list()

    def _delete_thesis(self):
        if not self.current_thesis_id:
            return
        if messagebox.askyesno("Confirm", "Delete this thesis and all its data?"):
            db.delete_thesis(self.current_thesis_id)
            self.current_thesis_id = None
            self.thesis_var.set("— select —")
            self._refresh_thesis_menu()
            self._refresh_list()
            self._refresh_ref_list()

    def _open_thesis_file(self):
        if not self.current_thesis_id:
            return
        theses = db.get_all_theses()
        t = next((x for x in theses if x["id"] == self.current_thesis_id), None)
        if t and t["file_path"]:
            fh.open_file_external(t["file_path"])
        else:
            path = filedialog.askopenfilename(
                title="Select source file",
                filetypes=fh.get_supported_file_types())
            if path:
                db.update_thesis(self.current_thesis_id,
                                 file_path=path,
                                 file_type=fh.get_file_type(path))
                fh.open_file_external(path)

    # ══════════════════════════════════════════════════════════════
    #  CATEGORIES
    # ══════════════════════════════════════════════════════════════

    def _refresh_category_menu(self):
        cats = db.get_all_categories()
        names = [c["name"] for c in cats]
        if not names:
            db.add_category("General", "#3B82F6")
            names = ["General"]
        self.cat_menu.configure(values=names)

    def _add_category(self):
        d = ctk.CTkInputDialog(text="Category name:", title="New Category")
        name = d.get_input()
        if not name:
            return
        color = colorchooser.askcolor(title="Pick colour",
                                       initialcolor="#3B82F6")
        try:
            db.add_category(name, color[1] or "#3B82F6")
        except Exception:
            messagebox.showwarning("Exists", "Category already exists.")
        self._refresh_category_menu()

    def _cat_id_by_name(self, name):
        cats = db.get_all_categories()
        c = next((c for c in cats if c["name"] == name), None)
        return c["id"] if c else None

    # ══════════════════════════════════════════════════════════════
    #  SAVE RESOURCE  (the core action)
    # ══════════════════════════════════════════════════════════════

    def _save(self):
        if not self.current_thesis_id:
            messagebox.showwarning("No Thesis", "Select or create a thesis first.")
            return

        para = self.para_box.get("1.0", "end-1c").strip()
        ref_text = self.ref_box.get("1.0", "end-1c").strip()
        page = self.page_entry.get().strip()
        cat_name = self.cat_var.get()

        if not para:
            messagebox.showwarning("Empty", "Enter a paragraph first.")
            return

        cat_id = self._cat_id_by_name(cat_name)

        # save pdf path
        pdf = self.pdf_path
        if pdf and os.path.isfile(pdf):
            os.makedirs(MEDIA_DIR, exist_ok=True)
            dest = os.path.join(MEDIA_DIR, os.path.basename(pdf))
            if not os.path.exists(dest):
                shutil.copy2(pdf, dest)
            pdf = dest

        ref_url = self.url_entry.get().strip()

        if self.editing_id:
            db.update_resource(self.editing_id, paragraph=para,
                               category_id=cat_id, page_number=page,
                               media_path=pdf)
            # update linked ref
            old = db.get_references_for_resource(self.editing_id)
            for o in old:
                db.unlink_resource_reference(self.editing_id, o["id"])
            if ref_text:
                ref_id = self._ensure_reference(ref_text, ref_url)
                db.link_resource_reference(self.editing_id, ref_id)
            self.editing_id = None
        else:
            res_id = db.add_resource(self.current_thesis_id, para,
                                      cat_id, page, pdf)
            if ref_text:
                ref_id = self._ensure_reference(ref_text, ref_url)
                db.link_resource_reference(res_id, ref_id)

        self._clear_form()
        self._refresh_list()
        self._refresh_ref_list()

    def _ensure_reference(self, text, url=""):
        """Parse citation text, find existing ref or create new one, return id."""
        parsed = cite.parse_reference(text)
        if url:
            parsed["doi_url"] = url
        # Only match duplicates if we have meaningful title or authors
        title = parsed.get("title", "").strip()
        authors = parsed.get("authors", "").strip()
        if title or authors:
            existing = db.get_references(self.current_thesis_id)
            for r in existing:
                r_title = (r["title"] or "").strip()
                r_authors = (r["authors"] or "").strip()
                if r_title and title and r_title == title and r_authors == authors:
                    if url and not r["doi_url"]:
                        db.update_reference(r["id"], doi_url=url)
                    return r["id"]
        return db.add_reference(
            self.current_thesis_id,
            ref_number=parsed.get("ref_number"),
            authors=authors,
            title=title,
            source=parsed.get("source", ""),
            year=parsed.get("year", ""),
            doi_url=parsed.get("doi_url", ""),
            ref_type=parsed.get("ref_type", "article"),
        )

    # ══════════════════════════════════════════════════════════════
    #  RESOURCE LIST
    # ══════════════════════════════════════════════════════════════

    def _refresh_list(self):
        for w in self.res_widgets:
            w.destroy()
        self.res_widgets.clear()
        if not self.current_thesis_id:
            return

        search = self.search_var.get().strip() or None
        rows = db.get_resources(self.current_thesis_id, search_term=search)

        for res in rows:
            card = ctk.CTkFrame(self.res_scroll,
                                fg_color=("#EFF6FF", "#1E293B"),
                                corner_radius=10)
            card.pack(fill="x", pady=3)

            # top: category badge + page
            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=10, pady=(8, 2))
            if res["category_name"]:
                ctk.CTkLabel(top, text=f" {res['category_name']} ",
                             font=ctk.CTkFont(size=11),
                             fg_color=res["category_color"] or "#3B82F6",
                             corner_radius=6,
                             text_color="white").pack(side="left", padx=(0, 6))
            if res["page_number"]:
                ctk.CTkLabel(top, text=f"p.{res['page_number']}",
                             font=ctk.CTkFont(size=11),
                             text_color="gray50").pack(side="left")

            # paragraph preview
            preview = (res["paragraph"] or "")[:180]
            if len(res["paragraph"] or "") > 180:
                preview += "…"
            ctk.CTkLabel(card, text=preview, anchor="w",
                         font=ctk.CTkFont(size=12), wraplength=420,
                         justify="left").pack(fill="x", padx=10, pady=2)

            # linked ref
            linked = db.get_references_for_resource(res["id"])
            ref_text = ""
            if linked:
                ref = linked[0]
                ref_text = cite.format_citation(dict(ref), self.style_var.get())
                ctk.CTkLabel(card, text=f"Ref: [{ref['ref_number']}] {ref['title'][:50]}",
                             font=ctk.CTkFont(size=11),
                             text_color="#3B82F6",
                             anchor="w").pack(fill="x", padx=10)

            # PDF indicator
            if res["media_path"] and os.path.isfile(res["media_path"]):
                ctk.CTkLabel(card, text=f"📄 {os.path.basename(res['media_path'])}",
                             font=ctk.CTkFont(size=10),
                             text_color="gray50",
                             anchor="w").pack(fill="x", padx=10)

            # buttons: Edit, Delete, Copy Ref, Open Ref
            brow = ctk.CTkFrame(card, fg_color="transparent")
            brow.pack(fill="x", padx=10, pady=(2, 8))
            ctk.CTkButton(brow, text="✏ Edit", width=50, height=24,
                           font=ctk.CTkFont(size=11),
                           fg_color="#F59E0B", hover_color="#D97706",
                           command=lambda rid=res["id"]: self._edit(rid)
                           ).pack(side="left", padx=(0, 3))
            ctk.CTkButton(brow, text="🗑", width=28, height=24,
                           fg_color="#EF4444", hover_color="#DC2626",
                           command=lambda rid=res["id"]: self._del(rid)
                           ).pack(side="left", padx=(0, 3))

            # Copy reference text button
            if linked:
                ctk.CTkButton(brow, text="📋 Ref", width=50, height=24,
                               font=ctk.CTkFont(size=11),
                               fg_color="#8B5CF6", hover_color="#7C3AED",
                               command=lambda t=ref_text: self._copy(t)
                               ).pack(side="left", padx=(0, 3))

            # Open reference URL (from linked ref's doi_url)
            ref_url = ""
            if linked:
                ref_url = linked[0]["doi_url"] or ""
            if ref_url:
                ctk.CTkButton(brow, text="🔗 Open", width=55, height=24,
                               font=ctk.CTkFont(size=11),
                               fg_color="#10B981", hover_color="#059669",
                               command=lambda u=ref_url: self._open_url(u)
                               ).pack(side="left", padx=(0, 3))

            # Open attached PDF
            res_pdf = res["media_path"] or ""
            if res_pdf and os.path.isfile(res_pdf):
                ctk.CTkButton(brow, text="📄 Open", width=55, height=24,
                               font=ctk.CTkFont(size=11),
                               fg_color="#0EA5E9", hover_color="#0284C7",
                               command=lambda p=res_pdf: fh.open_file_external(p)
                               ).pack(side="left", padx=(0, 3))

            self.res_widgets.append(card)

    def _edit(self, rid):
        rows = db.get_resources(self.current_thesis_id)
        res = next((r for r in rows if r["id"] == rid), None)
        if not res:
            return
        self.editing_id = rid
        self.para_box.delete("1.0", "end")
        self.para_box.insert("1.0", res["paragraph"] or "")
        self.page_entry.delete(0, "end")
        self.page_entry.insert(0, res["page_number"] or "")
        if res["category_name"]:
            self.cat_var.set(res["category_name"])
        linked = db.get_references_for_resource(rid)
        self.ref_box.delete("1.0", "end")
        self.url_entry.delete(0, "end")
        if linked:
            self.ref_box.insert("1.0", cite.format_citation(dict(linked[0]), self.style_var.get()))
            if linked[0]["doi_url"]:
                self.url_entry.insert(0, linked[0]["doi_url"])
        if res["media_path"]:
            self.pdf_path = res["media_path"]
            self.pdf_label.configure(text=os.path.basename(res["media_path"]))
        self.save_btn.configure(text="💾  Update")

    def _del(self, rid):
        if messagebox.askyesno("Confirm", "Delete this resource?"):
            db.delete_resource(rid)
            self._refresh_list()

    # ══════════════════════════════════════════════════════════════
    #  REFERENCE LIST TAB
    # ══════════════════════════════════════════════════════════════

    def _refresh_ref_list(self):
        for w in self.ref_widgets:
            w.destroy()
        self.ref_widgets.clear()
        if not self.current_thesis_id:
            return

        search = self.ref_search_var.get().strip() or None
        refs = db.get_references(self.current_thesis_id, search_term=search)

        for ref in refs:
            ieee = cite.format_citation(dict(ref), self.style_var.get())
            frame = ctk.CTkFrame(self.ref_scroll,
                                  fg_color=("#E0E7FF", "#1E293B"),
                                  corner_radius=8)
            frame.pack(fill="x", pady=2)
            row = ctk.CTkFrame(frame, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=6)

            ctk.CTkLabel(row, text=ieee, anchor="w",
                         font=ctk.CTkFont(size=12),
                         wraplength=400, justify="left").pack(
                side="left", fill="x", expand=True)

            ctk.CTkButton(row, text="📋", width=28, height=24,
                           fg_color="#8B5CF6", hover_color="#7C3AED",
                           command=lambda t=ieee: self._copy(t)
                           ).pack(side="right", padx=(4, 0))
            ctk.CTkButton(row, text="🗑", width=28, height=24,
                           fg_color="#EF4444", hover_color="#DC2626",
                           command=lambda rid=ref["id"]: self._del_ref(rid)
                           ).pack(side="right")

            self.ref_widgets.append(frame)

    def _del_ref(self, rid):
        if messagebox.askyesno("Confirm", "Delete this reference?"):
            db.delete_reference(rid)
            self._refresh_ref_list()

    def _renumber_refs(self):
        if self.current_thesis_id:
            db.renumber_references(self.current_thesis_id)
            self._refresh_ref_list()

    def _copy(self, text):
        cite.copy_to_clipboard(self, text)

    # ══════════════════════════════════════════════════════════════
    #  HELPERS
    # ══════════════════════════════════════════════════════════════

    def _clear_form(self):
        self.para_box.delete("1.0", "end")
        self.ref_box.delete("1.0", "end")
        self.page_entry.delete(0, "end")
        self.url_entry.delete(0, "end")
        self.pdf_path = None
        self.pdf_label.configure(text="")
        self.editing_id = None
        self.save_btn.configure(text="💾  Save")

    def _paste(self):
        try:
            self.para_box.insert("end", self.clipboard_get())
        except Exception:
            pass

    def _attach_pdf(self):
        p = filedialog.askopenfilename(
            title="Select reference PDF",
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")])
        if p:
            self.pdf_path = p
            self.pdf_label.configure(text=os.path.basename(p))

    def _open_url(self, url):
        import webbrowser
        webbrowser.open(url)

    def _center(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.WIDTH) // 2
        y = (self.winfo_screenheight() - self.HEIGHT) // 2
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")


if __name__ == "__main__":
    App().mainloop()
