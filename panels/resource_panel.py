"""
panels/resource_panel.py — Center panel: paragraph editor with reference linking.
"""

import os
import shutil
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image

import database as db
import file_handler as fh

MEDIA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "media")


class ResourcePanel(ctk.CTkFrame):
    """Center panel: write/paste paragraphs, attach media, link references."""

    def __init__(self, master, get_thesis_id=None, get_categories=None,
                 get_references=None, **kwargs):
        super().__init__(master, **kwargs)
        self.get_thesis_id = get_thesis_id
        self.get_categories = get_categories
        self.get_references = get_references
        self.editing_resource_id = None
        self.attached_media_path = None
        self.category_map = {}
        self.reference_map = {}

        self.configure(corner_radius=12)

        # ── Header ────────────────────────────────────────────────
        header = ctk.CTkLabel(
            self, text="📝  Resource Editor",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w",
        )
        header.pack(fill="x", padx=16, pady=(14, 4))

        # ── Paragraph editor ─────────────────────────────────────
        para_label = ctk.CTkLabel(
            self, text="Paragraph / Text Snippet",
            font=ctk.CTkFont(size=13), anchor="w",
        )
        para_label.pack(fill="x", padx=16, pady=(4, 0))

        self.paragraph_box = ctk.CTkTextbox(
            self, height=160,
            font=ctk.CTkFont(size=13),
            corner_radius=8,
        )
        self.paragraph_box.pack(fill="x", padx=16, pady=(4, 0))

        paste_btn = ctk.CTkButton(
            self, text="📋  Paste from Clipboard", height=30,
            font=ctk.CTkFont(size=12),
            fg_color=("gray70", "gray35"), hover_color=("gray60", "gray45"),
            command=self._paste_clipboard,
        )
        paste_btn.pack(anchor="e", padx=16, pady=(4, 8))

        # ── Options row 1: Category + Page ────────────────────────
        row1 = ctk.CTkFrame(self, fg_color="transparent")
        row1.pack(fill="x", padx=16, pady=(0, 4))

        ctk.CTkLabel(row1, text="Category", font=ctk.CTkFont(size=12)).pack(
            side="left", padx=(0, 6))
        self.category_var = ctk.StringVar(value="None")
        self.category_menu = ctk.CTkOptionMenu(
            row1, variable=self.category_var, values=["None"],
            width=160, height=32, font=ctk.CTkFont(size=12),
        )
        self.category_menu.pack(side="left", padx=(0, 16))

        ctk.CTkLabel(row1, text="Page", font=ctk.CTkFont(size=12)).pack(
            side="left", padx=(0, 6))
        self.page_entry = ctk.CTkEntry(
            row1, width=80, height=32, placeholder_text="e.g. 42",
            font=ctk.CTkFont(size=12),
        )
        self.page_entry.pack(side="left")

        # ── Options row 2: Reference link ────────────────────────
        row2 = ctk.CTkFrame(self, fg_color="transparent")
        row2.pack(fill="x", padx=16, pady=(0, 4))

        ctk.CTkLabel(row2, text="Link Reference", font=ctk.CTkFont(size=12)).pack(
            side="left", padx=(0, 6))
        self.ref_var = ctk.StringVar(value="None")
        self.ref_menu = ctk.CTkOptionMenu(
            row2, variable=self.ref_var, values=["None"],
            width=300, height=32, font=ctk.CTkFont(size=12),
        )
        self.ref_menu.pack(side="left", fill="x", expand=True)

        # ── Options row 3: Notes ──────────────────────────────────
        notes_label = ctk.CTkLabel(
            self, text="Notes (optional)",
            font=ctk.CTkFont(size=12), anchor="w",
        )
        notes_label.pack(fill="x", padx=16, pady=(4, 0))
        self.notes_entry = ctk.CTkEntry(
            self, height=32, placeholder_text="Additional notes…",
            font=ctk.CTkFont(size=12),
        )
        self.notes_entry.pack(fill="x", padx=16, pady=(2, 6))

        # ── Media attachment ──────────────────────────────────────
        media_frame = ctk.CTkFrame(self, fg_color="transparent")
        media_frame.pack(fill="x", padx=16, pady=(0, 4))

        self.btn_attach = ctk.CTkButton(
            media_frame, text="🖼  Attach Image", height=30,
            font=ctk.CTkFont(size=12),
            fg_color="#8B5CF6", hover_color="#7C3AED",
            command=self._attach_media,
        )
        self.btn_attach.pack(side="left", padx=(0, 8))

        self.media_label = ctk.CTkLabel(
            media_frame, text="No image attached",
            font=ctk.CTkFont(size=11), text_color="gray50",
        )
        self.media_label.pack(side="left")

        self.btn_clear_media = ctk.CTkButton(
            media_frame, text="✕", width=28, height=28,
            fg_color="#EF4444", hover_color="#DC2626",
            command=self._clear_media,
        )
        self.btn_clear_media.pack(side="right")

        # ── Media preview ─────────────────────────────────────────
        self.media_preview_label = ctk.CTkLabel(self, text="")
        self.media_preview_label.pack(padx=16, pady=(0, 4))

        # ── Action buttons ────────────────────────────────────────
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=16, pady=(4, 6))

        self.btn_save = ctk.CTkButton(
            btn_frame, text="💾  Save Resource", height=38,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#10B981", hover_color="#059669",
            command=self._save_resource,
        )
        self.btn_save.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.btn_clear = ctk.CTkButton(
            btn_frame, text="🗑  Clear", height=38, width=100,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#EF4444", hover_color="#DC2626",
            command=self._clear_form,
        )
        self.btn_clear.pack(side="right")

        # ── Separator ────────────────────────────────────────────
        sep = ctk.CTkFrame(self, height=2, fg_color=("gray80", "gray30"))
        sep.pack(fill="x", padx=16, pady=6)

        # ── Resource list header ──────────────────────────────────
        list_header = ctk.CTkFrame(self, fg_color="transparent")
        list_header.pack(fill="x", padx=16, pady=(0, 4))

        ctk.CTkLabel(
            list_header, text="📄  Saved Resources",
            font=ctk.CTkFont(size=14, weight="bold"), anchor="w",
        ).pack(side="left")

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.refresh_resources())
        search = ctk.CTkEntry(
            list_header, textvariable=self.search_var,
            placeholder_text="🔍 Search…", width=180, height=30,
            font=ctk.CTkFont(size=12),
        )
        search.pack(side="right")

        # ── Resource list ─────────────────────────────────────────
        self.resource_list = ctk.CTkScrollableFrame(self)
        self.resource_list.pack(fill="both", expand=True, padx=16, pady=(0, 14))
        self.resource_widgets = []

    # ── Dropdown refresh ──────────────────────────────────────────

    def refresh_dropdowns(self):
        """Refresh category and reference dropdown options."""
        # Categories
        self.category_map = {"None": None}
        cat_values = ["None"]
        if self.get_categories:
            for cid, cname in self.get_categories():
                self.category_map[cname] = cid
                cat_values.append(cname)
        self.category_menu.configure(values=cat_values)

        # References
        self.reference_map = {"None": None}
        ref_values = ["None"]
        if self.get_references:
            for rid, rtext in self.get_references():
                self.reference_map[rtext] = rid
                ref_values.append(rtext)
        self.ref_menu.configure(values=ref_values)

    # ── Resource list ─────────────────────────────────────────────

    def refresh_resources(self):
        for w in self.resource_widgets:
            w.destroy()
        self.resource_widgets.clear()

        thesis_id = self._get_tid()
        if not thesis_id:
            return

        search = self.search_var.get().strip() or None
        resources = db.get_resources(thesis_id, search_term=search)

        for res in resources:
            card = self._build_resource_card(res)
            self.resource_widgets.append(card)

    def _build_resource_card(self, res):
        card = ctk.CTkFrame(
            self.resource_list,
            fg_color=("#F1F5F9", "#1E293B"),
            corner_radius=10,
        )
        card.pack(fill="x", pady=4)

        # Top row: category badge + page
        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=10, pady=(8, 2))

        if res["category_name"]:
            badge = ctk.CTkLabel(
                top,
                text=f" {res['category_name']} ",
                font=ctk.CTkFont(size=11),
                fg_color=res["category_color"] or "#3B82F6",
                corner_radius=6,
                text_color="white",
            )
            badge.pack(side="left", padx=(0, 8))

        if res["page_number"]:
            page_lbl = ctk.CTkLabel(
                top, text=f"p. {res['page_number']}",
                font=ctk.CTkFont(size=11), text_color="gray50",
            )
            page_lbl.pack(side="left")

        # Paragraph preview
        para_text = (res["paragraph"] or "")[:200]
        if len(res["paragraph"] or "") > 200:
            para_text += "…"
        para = ctk.CTkLabel(
            card, text=para_text, anchor="w",
            font=ctk.CTkFont(size=12), wraplength=500,
            justify="left",
        )
        para.pack(fill="x", padx=10, pady=(2, 2))

        # Linked references
        linked_refs = db.get_references_for_resource(res["id"])
        if linked_refs:
            import citations as cite
            ref_texts = [f"[{r['ref_number']}]" for r in linked_refs]
            ref_lbl = ctk.CTkLabel(
                card, text="Refs: " + " ".join(ref_texts),
                font=ctk.CTkFont(size=11), text_color="#3B82F6", anchor="w",
            )
            ref_lbl.pack(fill="x", padx=10, pady=(0, 2))

        # Media thumbnail
        if res["media_path"] and os.path.isfile(res["media_path"]):
            try:
                img = Image.open(res["media_path"])
                img.thumbnail((120, 80))
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                img_label = ctk.CTkLabel(card, image=ctk_img, text="")
                img_label.pack(padx=10, pady=(2, 2), anchor="w")
            except Exception:
                pass

        # Action buttons
        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.pack(fill="x", padx=10, pady=(2, 8))

        edit_btn = ctk.CTkButton(
            actions, text="✏ Edit", width=60, height=26,
            font=ctk.CTkFont(size=11),
            fg_color="#F59E0B", hover_color="#D97706",
            command=lambda rid=res["id"]: self._edit_resource(rid),
        )
        edit_btn.pack(side="left", padx=(0, 4))

        del_btn = ctk.CTkButton(
            actions, text="🗑 Delete", width=70, height=26,
            font=ctk.CTkFont(size=11),
            fg_color="#EF4444", hover_color="#DC2626",
            command=lambda rid=res["id"]: self._delete_resource(rid),
        )
        del_btn.pack(side="left")

        return card

    # ── CRUD ──────────────────────────────────────────────────────

    def _save_resource(self):
        thesis_id = self._get_tid()
        if not thesis_id:
            messagebox.showwarning("No Thesis", "Select a thesis first.")
            return

        paragraph = self.paragraph_box.get("1.0", "end-1c").strip()
        if not paragraph:
            messagebox.showwarning("Empty", "Write or paste a paragraph first.")
            return

        cat_name = self.category_var.get()
        category_id = self.category_map.get(cat_name)
        page = self.page_entry.get().strip()
        notes = self.notes_entry.get().strip()

        # Handle media copy to media dir
        media_path = self.attached_media_path
        if media_path and os.path.isfile(media_path):
            os.makedirs(MEDIA_DIR, exist_ok=True)
            dest = os.path.join(MEDIA_DIR, os.path.basename(media_path))
            if not os.path.exists(dest):
                shutil.copy2(media_path, dest)
            media_path = dest

        if self.editing_resource_id:
            db.update_resource(
                self.editing_resource_id,
                paragraph=paragraph,
                category_id=category_id,
                page_number=page,
                media_path=media_path,
                notes=notes,
            )
            # Update reference link
            ref_name = self.ref_var.get()
            ref_id = self.reference_map.get(ref_name)
            # Clear old links first (simple approach)
            old_refs = db.get_references_for_resource(self.editing_resource_id)
            for old in old_refs:
                db.unlink_resource_reference(self.editing_resource_id, old["id"])
            if ref_id:
                db.link_resource_reference(self.editing_resource_id, ref_id)
            self.editing_resource_id = None
        else:
            res_id = db.add_resource(
                thesis_id, paragraph, category_id, page, media_path, notes
            )
            ref_name = self.ref_var.get()
            ref_id = self.reference_map.get(ref_name)
            if ref_id:
                db.link_resource_reference(res_id, ref_id)

        self._clear_form()
        self.refresh_resources()

    def _edit_resource(self, resource_id):
        thesis_id = self._get_tid()
        resources = db.get_resources(thesis_id)
        res = next((r for r in resources if r["id"] == resource_id), None)
        if not res:
            return

        self.editing_resource_id = resource_id
        self.paragraph_box.delete("1.0", "end")
        self.paragraph_box.insert("1.0", res["paragraph"] or "")
        self.page_entry.delete(0, "end")
        self.page_entry.insert(0, res["page_number"] or "")
        self.notes_entry.delete(0, "end")
        self.notes_entry.insert(0, res["notes"] or "")

        # Set category
        if res["category_name"]:
            self.category_var.set(res["category_name"])
        else:
            self.category_var.set("None")

        # Set media
        if res["media_path"]:
            self.attached_media_path = res["media_path"]
            self.media_label.configure(text=os.path.basename(res["media_path"]))
            self._show_media_preview(res["media_path"])
        else:
            self._clear_media()

        # Set linked reference
        linked = db.get_references_for_resource(resource_id)
        if linked:
            ref = linked[0]
            display = f"[{ref['ref_number']}] {ref['title'][:40]}"
            if display in self.reference_map:
                self.ref_var.set(display)
            else:
                self.ref_var.set("None")
        else:
            self.ref_var.set("None")

        self.btn_save.configure(text="💾  Update Resource")

    def _delete_resource(self, resource_id):
        if messagebox.askyesno("Confirm", "Delete this resource?"):
            db.delete_resource(resource_id)
            self.refresh_resources()

    def _clear_form(self):
        self.paragraph_box.delete("1.0", "end")
        self.page_entry.delete(0, "end")
        self.notes_entry.delete(0, "end")
        self.category_var.set("None")
        self.ref_var.set("None")
        self._clear_media()
        self.editing_resource_id = None
        self.btn_save.configure(text="💾  Save Resource")

    # ── Media ─────────────────────────────────────────────────────

    def _attach_media(self):
        path = filedialog.askopenfilename(
            title="Select image",
            filetypes=fh.get_supported_image_types(),
        )
        if path:
            self.attached_media_path = path
            self.media_label.configure(text=os.path.basename(path))
            self._show_media_preview(path)

    def _show_media_preview(self, path):
        try:
            img = Image.open(path)
            img.thumbnail((200, 120))
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
            self.media_preview_label.configure(image=ctk_img, text="")
            self.media_preview_label._ctk_image = ctk_img  # prevent GC
        except Exception:
            self.media_preview_label.configure(image=None, text="Preview error")

    def _clear_media(self):
        self.attached_media_path = None
        self.media_label.configure(text="No image attached")
        self.media_preview_label.configure(image=None, text="")

    # ── Clipboard ─────────────────────────────────────────────────

    def _paste_clipboard(self):
        try:
            text = self.winfo_toplevel().clipboard_get()
            self.paragraph_box.insert("end", text)
        except Exception:
            pass

    # ── Helpers ────────────────────────────────────────────────────

    def _get_tid(self):
        if self.get_thesis_id:
            return self.get_thesis_id()
        return None

    def set_category_filter(self, category_id):
        """Called when user clicks a category in the left panel."""
        # Re-filter resources (already handled via main app callback)
        pass
