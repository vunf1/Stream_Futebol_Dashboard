import subprocess
import sys
import tkinter as tk
import threading
import time
import os
from pathlib import Path

from helpers.make_drag_drop import make_it_drag_and_drop

# Fallback para erros antes da GUI customtkinter estar disponível
def fallback_notify(msg):
    print(msg)
    try:
        root = tk.Tk()
        root.withdraw()
        tk.messagebox.showerror("Erro", msg)
    except Exception:
        pass

def install_dependencies():
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
    except subprocess.CalledProcessError as e:
        fallback_notify(f"Falha na instalação das dependências:\n{e}")
        sys.exit(1)

def generate_secret_key():
    try:
        subprocess.run([sys.executable, os.path.join("helpers", "generate_secret.py")], check=True)
    except subprocess.CalledProcessError as e:
        fallback_notify(f"Erro ao gerar chave secreta:\n{e}")
        sys.exit(1)

install_dependencies()
generate_secret_key()

# Imports seguros após dependências
import customtkinter as ctk
from assets.colors import COLOR_SUCCESS, COLOR_ERROR, COLOR_INFO
from helpers.notification.toast import display_notification as show_message_notification

def delete_old_executable(path: Path):
    if not path.exists():
        return
    show_message_notification("❗ Fecha a app", "Fecha o ficheiro goal_score.exe antes de continuar!", icon="❌", duration=0, bg_color=COLOR_ERROR)
    while path.exists():
        try:
            path.unlink()
        except PermissionError:
            time.sleep(1)
        else:
            break
    show_message_notification("✅ Fechado", "Executável antigo removido com sucesso!", icon="✅", duration=2000, bg_color=COLOR_SUCCESS)

class BuildWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.configure_gui()
        self.create_widgets()
        make_it_drag_and_drop(self)
        self.attributes("-topmost", True)
        threading.Thread(target=self.run_build_steps, daemon=True).start()

    def configure_gui(self):
        self.overrideredirect(True)
        self.geometry("450x110")        
        self.eval('tk::PlaceWindow . center')
        self.iconbitmap("assets/icons/icon_soft.ico")
        self.configure(fg_color="#222222")

    def create_widgets(self):
        self.label = ctk.CTkLabel(self, text="☕ A preparar a magia...", font=("Segoe UI", 16))
        self.label.pack(pady=(25, 10))

        self.progress = ctk.CTkProgressBar(self, orientation="horizontal", mode="determinate", width=300)
        self.progress.pack(pady=10)
        self.progress.set(0)

        self.error_label = ctk.CTkLabel(
            self,
            text="",
            font=("Segoe UI", 11),
            text_color="white",
            wraplength=360,
            justify="left",
            cursor="hand2"  # Indica que pode ser clicado
        )
        self.error_label.pack(pady=(0, 5))
        self.error_label.pack_forget()
        self.error_label.bind("<Button-1>", self.copy_error_to_clipboard)

        
        self.close_button = ctk.CTkButton(self, text="Fechar", command=self.quit, fg_color="gray")
        self.close_button.pack(pady=(10, 0))
        self.close_button.pack_forget()

    def update_status(self, value, message, delay=400):
        self.progress.set(value)
        self.label.configure(text=message)
        self.update_idletasks()
        time.sleep(delay / 1000)

    def run_build_steps(self):
        try:
            self.update_status(0.05, "🏟️ A preparar o relvado para os grandes jogos...")
            time.sleep(0.5)

            self.update_status(0.10, "🧴 A aquecer os jogadores e lubrificar as chuteiras...")
            result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip())

            self.update_status(0.25, "🎽 A distribuir camisolas e estratégias nos balneários...")
            result = subprocess.run([sys.executable, os.path.join("helpers", "generate_secret.py")], capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip())

            self.update_status(0.35, "🧹 A limpar os campos de objetos indesejados (builds antigas)...")
            delete_old_executable(Path("dist") / "goal_score.exe")

            self.update_status(0.50, "⚙️ A montar o onze inicial com PyInstaller...")
            pyinstaller_command = [
                sys.executable, "-m", "PyInstaller",
                "--clean", "--onefile", "--noconsole",
                "--hidden-import", "customtkinter",
                "--hidden-import", "ctkmessagebox",
                "--add-data", ".env.enc;.",
                "--add-data", "secret.key;.",
                "--add-data", "assets/icons;assets/icons",
                "--icon", "assets/icons/icon_soft.ico",
                "--version-file", "version.txt",
                "goal_score.py"
            ]
            result = subprocess.run(pyinstaller_command, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip())

            self.update_status(0.80, "⚽ A iniciar os jogos: primeira parte em andamento...")
            time.sleep(0.4)
            self.update_status(0.90, "🎯 Remate final — a colocar o nome no placard...")
            time.sleep(0.4)
            self.update_status(1.00, "🏆 Golo! Build concluída com sucesso!")
            show_message_notification("🎉 Sucesso", "O executável foi criado com sucesso!", icon="🎯", duration=6000, bg_color=COLOR_SUCCESS)
            time.sleep(3)
            self.quit()

        except Exception as e:
            show_message_notification("💥 Erro no Build", f"Ocorreu um erro:\n{e}", icon="❌", duration=7000, bg_color=COLOR_ERROR)
            self.label.configure(text="💥 Algo correu mal no feitiço...")
            self.last_error_text = f"Detalhes técnicos:\n{e}"
            self.error_label.configure(text=f"Detalhes técnicos:\n{e}")

            self.error_label.pack()
            self.close_button.pack()
            # Espera o sistema calcular os tamanhos
            self.update_idletasks()
            # Ajusta dinamicamente a altura da janela
            new_height = self.winfo_reqheight()
            self.geometry(f"400x{new_height}")

    def copy_error_to_clipboard(self, _event=None):
        if not hasattr(self, "last_error_text"):
            return
        self.clipboard_clear()
        self.clipboard_append(self.last_error_text)
        show_message_notification("📋 Copiado", "O erro foi copiado.", icon="✅", duration=3000, bg_color=COLOR_SUCCESS)


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    app = BuildWindow()
    app.mainloop()
