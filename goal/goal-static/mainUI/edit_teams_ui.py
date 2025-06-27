# edit_popup.py
import customtkinter as ctk
from helpers import show_message_notification
from colors  import COLOR_WARNING, COLOR_SUCCESS, COLOR_STOP

class TeamManagerWindow(ctk.CTkToplevel):
    def __init__(self, parent, mongo, pin):
        super().__init__(parent)
        self.mongo      = mongo
        self.pin        = str(pin).strip()

        if not self._prompt_for_pin():  # ask PIN first
            self.destroy()
            return

        self.title("Team Manager")
        self.geometry("400x400")
        self.lift()
        self.iconbitmap("assets/icons/gear.ico")
        
        self.scrollable_frame = ctk.CTkScrollableFrame(self, corner_radius=0)
        self.scrollable_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self._build_team_list()

    def _prompt_for_pin(self):
        while True:
            admin_popup_window = ctk.CTkToplevel(self)
            admin_popup_window.title("Admin Access")
            admin_popup_window.geometry("300x150")
            admin_popup_window.attributes("-topmost", True)
            admin_popup_window.grab_set()

            ctk.CTkLabel(admin_popup_window, text="Enter admin PIN").pack(pady=(20,10))
            entry = ctk.CTkEntry(admin_popup_window, show="*")
            entry.pack(pady=5)
            entry.after(100, lambda: entry.focus())

            result = {"value": None}
            def submit(event=None):
                result["value"] = entry.get()
                admin_popup_window.destroy()

            entry.bind("<Return>", submit)
            ctk.CTkButton(admin_popup_window, text="Submit", command=submit).pack(pady=(10,5))
            admin_popup_window.wait_window()

            if result["value"] is None:
                return False
            if result["value"].strip() == self.pin:
                return True

            show_message_notification("🔒 Acesso Negado","PIN incorreto. Tenta novamente.",icon="❌", bg_color=COLOR_WARNING)

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
        self.refresh_cb()
        self._build_team_list()


class EditTeamPopup(ctk.CTkToplevel):
    def __init__(self, parent, mongo, original_name, original_abrev, on_done):
        super().__init__(parent)
        self.mongo         = mongo
        self.orig_name     = original_name
        self.on_done       = on_done

        self.title("Edit Team")
        self.geometry("300x220")
        self.iconbitmap("assets/icons/icon_soft.ico")
        self.grab_set()
        self.attributes("-topmost", True)

        ctk.CTkLabel(self, text="Team Name").pack(pady=(10,0))
        self.name_entry = ctk.CTkEntry(self)
        self.name_entry.insert(0, original_name)
        self.name_entry.pack(pady=5)

        ctk.CTkLabel(self, text="Abbreviation").pack()
        self.abrev_entry = ctk.CTkEntry(self)
        self.abrev_entry.insert(0, original_abrev)
        self.abrev_entry.pack(pady=5)

        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=10)

        ctk.CTkButton(btn_frame, text="Salvar", command=self._save).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Apagar", fg_color="red", command=self._delete).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Cancelar", command=self.destroy).pack(side="left", padx=5)

    def _save(self):
        new_name  = self.name_entry.get().strip().upper()
        new_abrev = self.abrev_entry.get().strip().upper()
        if new_name and new_abrev:
            self.mongo.save_team(new_name, new_abrev)
            show_message_notification("✅ Atualizado",f"Equipa '{new_name}' atualizada.",icon="✅", bg_color=COLOR_SUCCESS)
            self.destroy()
            self.on_done()

    def _delete(self):
        confirm = ctk.CTkInputDialog(
            title="Confirmação",
            text=f"Escreve 'DELETE' para apagar '{self.orig_name}'"
        )
        if confirm.get_input().strip().upper() == "DELETE":
            self.mongo.delete_team(self.orig_name)
            show_message_notification(
                "❌ Apagado",
                f"Equipa '{self.orig_name}' apagada.",
                icon="❌", bg_color=COLOR_STOP
            )
            self.destroy()
            self.on_done()
