# edit_popup.py
import customtkinter as ctk
from helpers.helpers import prompt_for_pin
from helpers.icons_provider import get_icon_path
from helpers.make_drag_drop import make_it_drag_and_drop
from helpers.notification.toast import show_message_notification
from assets.colors  import COLOR_WARNING, COLOR_SUCCESS, COLOR_STOP
from helpers.top_c_child_parent import top_centered_child_to_parent

class TeamManagerWindow(ctk.CTkToplevel):
    def __init__(self, parent, mongo):
        super().__init__(parent)
        self.withdraw()
        self.mongo      = mongo

        if not self._prompt_for_pin():  # ask PIN first
            self.destroy()
            return
        
        #make_it_drag_and_drop(self)
        self.deiconify()
        child_w, child_h = 400, 400
        # Center the child window at the top of the parent
        top_centered_child_to_parent(self, parent, child_w, child_h)
        self.attributes("-topmost", True)
        self.title("Team Manager")
        self.geometry("400x400")
        self.lift()
        self.iconbitmap(get_icon_path("gear")) 
        
        self.scrollable_frame = ctk.CTkScrollableFrame(self, corner_radius=0)
        self.scrollable_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self._build_team_list()

    def _prompt_for_pin(self):
        return prompt_for_pin(self)

    def _build_team_list(self):
        
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        teams = self.mongo.load_teams()
        for name, abrev in teams.items():
            btn = ctk.CTkButton(
                self.scrollable_frame,
                text=f"{name} — {abrev}",
                anchor="w",
                command=lambda n=name, a=abrev: self._open_edit_popup(n, a)
            )
            btn.pack(fill="x", pady=2)

    def _open_edit_popup(self, name, abrev):
        EditTeamPopup(
            parent=self,
            mongo=self.mongo,
            original_name=name,
            original_abrev=abrev,
            on_done=self._on_change
        )

    def _on_change(self):
        self._build_team_list()

import os
import customtkinter as ctk
from assets.colors import COLOR_SUCCESS, COLOR_STOP
from helpers.notification.toast import show_message_notification

class EditTeamPopup(ctk.CTkToplevel):
    def __init__(self, parent, mongo, original_name, original_abrev, on_done):
        super().__init__(parent)
        self.mongo         = mongo
        self.orig_name     = original_name.strip().upper()
        self.on_done       = on_done

        self.title("Edit Team")
        self.geometry("300x240")
        self.iconbitmap(get_icon_path("icon_soft")) 
        self.grab_set()
        self.attributes("-topmost", True)

        # --- build form ---
        ctk.CTkLabel(self, text="Team Name").pack(pady=(10,0))
        self.name_entry = ctk.CTkEntry(self)
        self.name_entry.insert(0, original_name)
        self.name_entry.pack(pady=5, padx=20, fill="x")

        ctk.CTkLabel(self, text="Abbreviation").pack()
        self.abrev_entry = ctk.CTkEntry(self)
        self.abrev_entry.insert(0, original_abrev)
        self.abrev_entry.pack(pady=5, padx=20, fill="x")

        # Buttons
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=15)
        ctk.CTkButton(btn_frame, text="Salvar", command=self._save).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Apagar", fg_color="red", command=self._delete).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Cancelar", command=self.destroy).pack(side="left", padx=5)

        # force focus on this popup’s entry
        self.name_entry.focus_set()

    def _save(self):
        new_name  = self.name_entry.get().strip().upper()
        new_abrev = self.abrev_entry.get().strip().upper()
        if not (new_name and new_abrev):
            return  # nothing to do

        # 1) upsert new
        self.mongo.save_team(new_name, new_abrev)

        # 2) if renamed, delete old
        if new_name != self.orig_name:
            self.mongo.delete_team(self.orig_name)

        show_message_notification("✅ Atualizado",f"Equipa '{new_name}' atualizada.",icon="✅", bg_color=COLOR_SUCCESS)

        self.destroy()
        self.on_done()

    def _delete(self):
        # custom confirm dialog so we don't leak focus_set callbacks
        dlg = ctk.CTkToplevel(self)
        dlg.title("Confirmação")
        dlg.geometry("300x140")
        dlg.grab_set()
        dlg.attributes("-topmost", True)

        ctk.CTkLabel(dlg, text=f"Type DELETE to remove '{self.orig_name}'").pack(pady=(15,5))
        entry = ctk.CTkEntry(dlg, placeholder_text="DELETE")
        entry.pack(pady=5, padx=20, fill="x")
        entry.focus_set()

        result = {"ok": False}
        def on_submit(evt=None):
            if entry.get().strip().upper() == "DELETE":
                result["ok"] = True
            dlg.destroy()

        entry.bind("<Return>", on_submit)
        ctk.CTkButton(dlg, text="OK", command=on_submit).pack(pady=(5,10))

        dlg.wait_window()

        if not result["ok"]:
            return

        self.mongo.delete_team(self.orig_name)
        show_message_notification("❌ Apagado",f"Equipa '{self.orig_name}' apagada.",icon="❌", bg_color=COLOR_STOP)
        self.destroy()
        self.on_done()
