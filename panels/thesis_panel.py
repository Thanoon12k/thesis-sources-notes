"""
panels/thesis_panel.py — Left panel: thesis list and category management.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox, colorchooser
import database as db
import file_handler as fh


class ThesisPanel(ctk.CTkFrame):
    """Left sidebar: thesis selector, file opener, and category tree."""

    def __init__(self, master, on_thesis_changed=None, on_category_filter=None, **kwargs):
        super().__init__(master, **kwargs)
        self.on_thesis_changed = on_thesis_changed
        self.on_category_filter = on_category_filter
        self.current_thesis_id = None

        self.configure(corner_radius=12)

        # ── Header ────────────────────────────────────────────────
        header = ctk.CTkLabel(
            self, text="📂  Theses & Papers",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w",
        )
        header.pack(fill="x", padx=14, pady=(14, 6))

        # ── Add thesis button ────────────────────────────────────
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=14, pady=(0, 6))

        self.btn_add = ctk.CTkButton(
            btn_frame, text="＋ Add Thesis", height=32,
            font=ctk.CTkFont(size=13),
            command=self._add_thesis,
        )
        self.btn_add.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.btn_remove = ctk.CTkButton(
            btn_frame, text="✕", width=32, height=32,
            fg_color="#EF4444", hover_color="#DC2626",
            command=self._delete_thesis,
        )
        self.btn_remove.pack(side="right")

        # ── Thesis list ──────────────────────────────────────────
        self.thesis_listbox = ctk.CTkScrollableFrame(self, height=160)
        self.thesis_listbox.pack(fill="x", padx=14, pady=(0, 8))
        self.thesis_buttons = []

        # ── Open file button ─────────────────────────────────────
        self.btn_open = ctk.CTkButton(
            self, text="📄 Open Source File", height=34,
            font=ctk.CTkFont(size=13),
            fg_color="#10B981", hover_color="#059669",
            command=self._open_file,
        )
        self.btn_open.pack(fill="x", padx=14, pady=(0, 12))

        # ── Separator ────────────────────────────────────────────
        sep = ctk.CTkFrame(self, height=2, fg_color=("gray80", "gray30"))
        sep.pack(fill="x", padx=14, pady=4)

        # ── Categories header ────────────────────────────────────
        cat_header = ctk.CTkLabel(
            self, text="🏷️  Categories",
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w",
        )
        cat_header.pack(fill="x", padx=14, pady=(8, 4))

        cat_btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        cat_btn_frame.pack(fill="x", padx=14, pady=(0, 6))

        self.btn_add_cat = ctk.CTkButton(
            cat_btn_frame, text="＋ Add", height=28,
            font=ctk.CTkFont(size=12),
            command=self._add_category,
        )
        self.btn_add_cat.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.btn_del_cat = ctk.CTkButton(
            cat_btn_frame, text="✕", width=28, height=28,
            fg_color="#EF4444", hover_color="#DC2626",
            command=self._delete_category,
        )
        self.btn_del_cat.pack(side="right")

        # ── Category list ────────────────────────────────────────
        self.category_listbox = ctk.CTkScrollableFrame(self)
        self.category_listbox.pack(fill="both", expand=True, padx=14, pady=(0, 8))
        self.category_buttons = []
        self.selected_category_id = None

        # ── Show All button ──────────────────────────────────────
        self.btn_show_all = ctk.CTkButton(
            self, text="Show All Resources", height=30,
            font=ctk.CTkFont(size=12),
            fg_color=("gray70", "gray35"), hover_color=("gray60", "gray45"),
            command=self._show_all,
        )
        self.btn_show_all.pack(fill="x", padx=14, pady=(0, 14))

        # Initial load
        self.refresh_theses()
        self.refresh_categories()

    # ── Thesis methods ────────────────────────────────────────────

    def refresh_theses(self):
        for btn in self.thesis_buttons:
            btn.destroy()
        self.thesis_buttons.clear()

        theses = db.get_all_theses()
        for thesis in theses:
            btn = ctk.CTkButton(
                self.thesis_listbox,
                text=f"📑  {thesis['title']}",
                anchor="w",
                height=36,
                font=ctk.CTkFont(size=13),
                fg_color=("gray85", "gray25") if thesis["id"] != self.current_thesis_id
                else ("#3B82F6", "#2563EB"),
                hover_color=("#60A5FA", "#3B82F6"),
                text_color=("gray10", "gray90"),
                command=lambda tid=thesis["id"]: self._select_thesis(tid),
            )
            btn.pack(fill="x", pady=2)
            self.thesis_buttons.append(btn)

    def _select_thesis(self, thesis_id):
        self.current_thesis_id = thesis_id
        self.refresh_theses()
        if self.on_thesis_changed:
            self.on_thesis_changed(thesis_id)

    def _add_thesis(self):
        dialog = ctk.CTkInputDialog(
            text="Enter thesis / paper title:", title="Add Thesis"
        )
        title = dialog.get_input()
        if not title:
            return

        file_path = filedialog.askopenfilename(
            title="Select source file (optional)",
            filetypes=fh.get_supported_file_types(),
        )
        file_type = fh.get_file_type(file_path) if file_path else None

        thesis_id = db.add_thesis(title, file_path or None, file_type)
        self.refresh_theses()
        self._select_thesis(thesis_id)

    def _delete_thesis(self):
        if not self.current_thesis_id:
            messagebox.showwarning("No Selection", "Select a thesis first.")
            return
        if messagebox.askyesno("Confirm", "Delete this thesis and ALL its resources?"):
            db.delete_thesis(self.current_thesis_id)
            self.current_thesis_id = None
            self.refresh_theses()
            if self.on_thesis_changed:
                self.on_thesis_changed(None)

    def _open_file(self):
        if not self.current_thesis_id:
            messagebox.showwarning("No Selection", "Select a thesis first.")
            return
        theses = db.get_all_theses()
        thesis = next((t for t in theses if t["id"] == self.current_thesis_id), None)
        if not thesis or not thesis["file_path"]:
            # Let user pick a file and associate it
            file_path = filedialog.askopenfilename(
                title="Select source file",
                filetypes=fh.get_supported_file_types(),
            )
            if file_path:
                file_type = fh.get_file_type(file_path)
                db.update_thesis(self.current_thesis_id, file_path=file_path, file_type=file_type)
                fh.open_file_external(file_path)
        else:
            fh.open_file_external(thesis["file_path"])

    # ── Category methods ──────────────────────────────────────────

    def refresh_categories(self):
        for btn in self.category_buttons:
            btn.destroy()
        self.category_buttons.clear()

        categories = db.get_all_categories()
        for cat in categories:
            btn = ctk.CTkButton(
                self.category_listbox,
                text=f"●  {cat['name']}",
                anchor="w",
                height=32,
                font=ctk.CTkFont(size=13),
                fg_color=cat["color"] if cat["id"] == self.selected_category_id
                else ("gray85", "gray25"),
                hover_color=cat["color"],
                text_color=("gray10", "gray90"),
                command=lambda cid=cat["id"]: self._select_category(cid),
            )
            btn.pack(fill="x", pady=2)
            self.category_buttons.append(btn)

    def _select_category(self, cat_id):
        self.selected_category_id = cat_id
        self.refresh_categories()
        if self.on_category_filter:
            self.on_category_filter(cat_id)

    def _add_category(self):
        dialog = ctk.CTkInputDialog(text="Category name:", title="Add Category")
        name = dialog.get_input()
        if not name:
            return
        color = colorchooser.askcolor(title="Pick category color", initialcolor="#3B82F6")
        hex_color = color[1] if color[1] else "#3B82F6"
        try:
            db.add_category(name, hex_color)
        except Exception:
            messagebox.showwarning("Duplicate", "Category already exists.")
            return
        self.refresh_categories()

    def _delete_category(self):
        if not self.selected_category_id:
            messagebox.showwarning("No Selection", "Select a category first.")
            return
        if messagebox.askyesno("Confirm", "Delete this category?"):
            db.delete_category(self.selected_category_id)
            self.selected_category_id = None
            self.refresh_categories()

    def _show_all(self):
        self.selected_category_id = None
        self.refresh_categories()
        if self.on_category_filter:
            self.on_category_filter(None)

    def get_current_thesis_id(self):
        return self.current_thesis_id

    def get_categories_for_dropdown(self):
        """Return list of (id, name) tuples for dropdown menus."""
        cats = db.get_all_categories()
        return [(c["id"], c["name"]) for c in cats]
