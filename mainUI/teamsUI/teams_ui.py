import customtkinter as ctk
from typing import Dict, Any, Callable
from helpers.notification.toast import show_message_notification
from helpers.helpers import load_teams_from_json, save_teams_to_json
from mainUI.teamsUI.autocomplete import Autocomplete
from mainUI.edit_teams_ui import TeamManagerWindow
from assets.colors import COLOR_WARNING, COLOR_SUCCESS
from database.gameinfo import GameInfoStore, DEFAULT_FIELD_STATE
from database.mongodb import MongoTeamManager
import tkinter.messagebox as messagebox

BUTTON_PAD = dict(padx=5, pady=5)

def append_team_to_mongo(name: str, abrev: str, instance: int):
    """Helper function to append team to MongoDB with validation"""
    name = name.strip().upper()
    abrev = abrev.strip().upper()
    
    if not name or not abrev:
        return  # Skip empty entries
    
    mongo = MongoTeamManager()
    
    current_abrev = mongo.get_abbreviation(name)
    
    if current_abrev:
        if current_abrev != abrev:
            # Same name, different abbrev — Ask to update
            root = ctk.CTk()
            root.withdraw()
            result = messagebox.askyesno(
                title=f"Campo {instance} - Equipa já existe",
                message=(
                    f"A equipa '{name}' já existe com a sigla '{current_abrev}'.\n\n"
                    f"Deseja atualizar para '{abrev}'?"
                )
            )
            root.destroy()
            if result:
                try:
                    mongo.save_team(name, abrev)
                    show_message_notification(f"✅Campo {instance} - Atualizado", f"Equipa '{name}' atualizada para '{abrev}'.", bg_color=COLOR_SUCCESS)
                except Exception as e:
                    messagebox.showerror("Erro", f"Erro ao atualizar equipa: {e}")
            else:
                show_message_notification(f"❌ Campo {instance} - Cancelado", f"A sigla de '{name}' não foi alterada.", bg_color=COLOR_WARNING)
            return
        else:
            show_message_notification(f"ℹ️ Campo {instance} - Mantido", f"A sigla de '{name}' já é '{abrev}'.", bg_color=COLOR_WARNING)
            return

    # Check if abbreviation is already used by another team (informative, not blocking)
    all_teams = mongo.load_teams()
    for other_name, other_abrev in all_teams.items():
        if other_name != name and other_abrev == abrev:
            show_message_notification(f"⚠️ Campo {instance} - Reutilização", f"A abreviação '{abrev}' já está em uso por '{other_name}', mas será reutilizada.", bg_color=COLOR_WARNING)
            break  # Just log, don't stop

    # Save new team
    try:
        mongo.save_team(name, abrev)
        show_message_notification(f"✅ Campo {instance} - Gravado", f"Equipa '{name}' gravada com sucesso.", duration=1500, bg_color=COLOR_SUCCESS)
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao guardar equipa na base de dados: {e}")


class TeamInputManager(ctk.CTkFrame):
    """
    Cleaner team input panel backed by GameInfoStore.
    - Loads/saves home/away NAME + ABBR to gameinfo.json (per field block)
    - Autocomplete pulls teams from cached JSON (falls back to Mongo via caller)
    """
    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        mongo,
        refresh_labels_cb: Callable[[], None],
        instance: int,
        json: GameInfoStore
    ):
        super().__init__(parent, fg_color="transparent")
        self.parent = parent
        self.mongo = mongo
        self.refresh_labels = refresh_labels_cb
        self.json = json
        self.instance_number = instance

        # Shared JSON store for this field
        self.store = json

        # Local cache for team suggestions: { "TEAM NAME": "ABR" }
        self._teams_cache: Dict[str, str] = {}

        # Defer UI building for smooth loading
        self.after(100, self._deferred_build_ui)  # Faster (was 200ms, now 100ms)

    def _deferred_build_ui(self):
        """Deferred UI building to ensure smooth loading"""
        try:
            self._build_ui()
            self.after(25, self._hydrate_from_store)  # Faster (was 50ms, now 25ms)
        except Exception as e:
            print(f"Error building TeamInputManager: {e}")
            # Fallback: build UI immediately if there's an error
            self._build_ui()
            self._hydrate_from_store()

    # -------------------------- Data --------------------------
    def _hydrate_from_store(self) -> None:
        home_name  = self.store.get("home_name", DEFAULT_FIELD_STATE["home_name"]) or ""
        home_abbr  = self.store.get("home_abbr", DEFAULT_FIELD_STATE["home_abbr"]) or ""
        away_name  = self.store.get("away_name", DEFAULT_FIELD_STATE["away_name"]) or ""
        away_abbr  = self.store.get("away_abbr", DEFAULT_FIELD_STATE["away_abbr"]) or ""

        self.home_name_entry.set(home_name)
        self.home_abbrev_entry.delete(0, "end"); self.home_abbrev_entry.insert(0, home_abbr)
        self.away_name_entry.set(away_name)
        self.away_abbrev_entry.delete(0, "end"); self.away_abbrev_entry.insert(0, away_abbr)

    def _fetch_teams_cached(self) -> Dict[str, str]:
        """Return teams mapping from cache; if empty, load from JSON file; if still empty, ask Mongo and backup to JSON."""
        if self._teams_cache:
            return self._teams_cache

        teams = load_teams_from_json()
        if teams is False or not teams:
            # Fall back to Mongo, then persist a local cache
            teams = self.mongo.load_teams()  # expected {name: abbr}
            try:
                save_teams_to_json(teams)
            except Exception:
                pass

        # Normalize keys once for better matching
        self._teams_cache = {str(k).upper(): str(v).upper() for k, v in (teams or {}).items()}
        return self._teams_cache

    # -------------------------- UI --------------------------
    def _build_ui(self):
        self.pack(fill="x", padx=10)

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="x")
        container.grid_columnconfigure((0, 1), weight=1)

        # Home
        ctk.CTkLabel(container, text="Nome Casa").grid(row=0, column=0, sticky="w", padx=5)
        self.home_name_entry = Autocomplete(
            container,
            fetch_suggestions=self._fetch_teams_cached,
            selection_callback=self._on_home_selected,
            placeholder="ex: SPORTING",
        )
        self.home_name_entry.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 10))

        ctk.CTkLabel(container, text="Sigla Casa").grid(row=2, column=0, sticky="w", padx=5)
        self.home_abbrev_entry = ctk.CTkEntry(container, placeholder_text="ex: SCP")
        self.home_abbrev_entry.grid(row=3, column=0, sticky="ew", padx=5, pady=(0, 10))

        # Away
        ctk.CTkLabel(container, text="Nome Fora").grid(row=0, column=1, sticky="w", padx=5)
        self.away_name_entry = Autocomplete(
            container,
            fetch_suggestions=self._fetch_teams_cached,
            selection_callback=self._on_away_selected,
            placeholder="ex: PORTO",
        )
        self.away_name_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=(0, 10))

        ctk.CTkLabel(container, text="Sigla Fora").grid(row=2, column=1, sticky="w", padx=5)
        self.away_abbrev_entry = ctk.CTkEntry(container, placeholder_text="ex: FCP")
        self.away_abbrev_entry.grid(row=3, column=1, sticky="ew", padx=5, pady=(0, 10))

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x")
        btn_frame.grid_rowconfigure(0, weight=1)
        btn_frame.grid_columnconfigure((0, 1), weight=1, uniform="btns")

        ctk.CTkButton(btn_frame, text="Guardar", fg_color="gray", command=self._on_save)\
            .grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        ctk.CTkButton(
            btn_frame,
            text="Editar",
            fg_color="orange",
            command=lambda: TeamManagerWindow(parent=self.parent, mongo=self.mongo)
        ).grid(row=0, column=1, sticky="nsew", padx=(5, 0))

    # -------------------------- Callbacks --------------------------
    def _on_home_selected(self, name: str, abrev: str):
        self.home_abbrev_entry.delete(0, "end")
        self.home_abbrev_entry.insert(0, (abrev or "").upper())
        self.home_name_entry.set((name or "").upper())

    def _on_away_selected(self, name: str, abrev: str):
        self.away_abbrev_entry.delete(0, "end")
        self.away_abbrev_entry.insert(0, (abrev or "").upper())
        self.away_name_entry.set((name or "").upper())

    def _on_save(self):
        home_name  = (self.home_name_entry.get() or "").strip().upper()
        home_abrev = (self.home_abbrev_entry.get() or "").strip().upper()
        away_name  = (self.away_name_entry.get() or "").strip().upper()
        away_abrev = (self.away_abbrev_entry.get() or "").strip().upper()

        # Save into Mongo registry (idempotent)
        append_team_to_mongo(home_name, home_abrev, self.instance_number)
        append_team_to_mongo(away_name, away_abrev, self.instance_number)

        if not all([home_name, home_abrev, away_name, away_abrev]):
            show_message_notification(
                f"⚠️ Campo {self.instance_number} - Aviso",
                "Alguns campos estão vazios. Campos vazios serão criados.",
                icon="⚠️"
            )

        # Persist to gameinfo.json (single atomic write of the 4 keys)
        changed = self.store.update({
            "home_name": home_name,
            "home_abbr": home_abrev,
            "away_name": away_name,
            "away_abbr": away_abrev,
        }, persist=True)

        # Update cache for autocomplete if new teams were introduced
        if home_name and home_abrev:
            self._teams_cache[home_name] = home_abrev
        if away_name and away_abrev:
            self._teams_cache[away_name] = away_abrev

        # Let the caller refresh overlay labels, etc.
        self.refresh_labels()

        show_message_notification(
            f"✅ Campo {self.instance_number} - Gravado",
            "Informações da equipa foram guardadas",
            icon="✅",
            bg_color=COLOR_SUCCESS
        )
