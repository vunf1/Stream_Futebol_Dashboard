import os
import json
import tkinter.messagebox as messagebox
import customtkinter as ctk
from assets.colors import COLOR_INFO, COLOR_STOP, COLOR_SUCCESS, COLOR_WARNING
from helpers.filenames import BASE_FOLDER_PATH
from helpers.notification.toast import show_message_notification
from database.mongodb import MongoTeamManager

def append_team_to_mongo(name: str, abrev: str, instance: int):
    name = name.strip().upper()
    abrev = abrev.strip().upper()
    instance = instance

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
                show_message_notification(f"❌ Campo {instance} - Cancelado", f"A sigla de '{name}' não foi alterada.", bg_color=COLOR_STOP)
            return
        else:
            show_message_notification(f"ℹ️ Campo {instance} - Mantido", f"A sigla de '{name}' já é '{abrev}'.", bg_color=COLOR_INFO)
            return

    # Check if abbreviation is already used by another team (informative, not blocking)
    all_teams = mongo.load_teams()
    for other_name, other_abrev in all_teams.items():
        if other_name != name and other_abrev == abrev:
            show_message_notification(f"⚠️ Campo {instance} - Reutilização", f"A abreviação '{abrev}' já está em uso por '{other_name}', mas será reutilizada.", bg_color=COLOR_WARNING)
            break  # Just log, don’t stop

    # Save new team
    try:
        mongo.save_team(name, abrev)
        show_message_notification(f"✅ Campo {instance} - Gravado", f"Equipa '{name}' gravada com sucesso.", duration=1500, bg_color=COLOR_SUCCESS)

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao guardar equipa na base de dados: {e}")

def load_teams_json():
    json_path = os.path.join(BASE_FOLDER_PATH, "teams.json")
    print("Tentando carregar:", json_path)  # DEBUG

    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                print("Conteúdo lido:", data)  # DEBUG
                return data  # Agora já é diretamente {name: abrev}
        except Exception as e:
            print(f"Erro ao carregar JSON: {e}")
            messagebox.showerror("Erro", f"Falha ao carregar JSON:\n{e}")
    else:
        print("Arquivo não encontrado:", json_path)

    return {}