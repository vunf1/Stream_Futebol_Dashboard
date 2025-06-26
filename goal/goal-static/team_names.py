import os
import json
import tkinter.messagebox as messagebox
import customtkinter as ctk
from helpers import show_message_notification

def append_team_to_json(instance_folder: str, name: str, abrev: str):
    name = name.strip().upper()
    abrev = abrev.strip().upper()
    
    json_path = os.path.join(instance_folder, "teams.json")
    teams = {}

    # Carrega os dados existentes
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                teams = json.load(f)
        except Exception:
            teams = {}

    # Se já existe
    if name in teams:
        current_abrev = teams[name]
        if current_abrev != abrev:
            root = ctk.CTk()
            root.withdraw()
            result = messagebox.askyesno(
                title="Equipa já existe",
                message=f"A equipa '{name}' já existe com a sigla '{current_abrev}'.\nDeseja manter a sigla existente?"
            )
            root.destroy()
            if not result:
                messagebox.showinfo("Cancelado", "Operação cancelada.")
                return
            else:
                messagebox.showinfo("Mantido", "Sigla original mantida.")
                return

    # Salvar novo ou atualizar
    teams[name] = abrev

    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(teams, f, indent=4, ensure_ascii=False)
        show_message_notification("Gravado", f"Equipa '{name}' gravada.", duration=1000)

    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao guardar JSON: {e}")
        

def load_teams_json(instance_folder: str):
    json_path = os.path.join(instance_folder, "teams.json")
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