import subprocess
import sys
import tkinter as tk
import customtkinter as ctk
import threading
from goal_score import show_message_notification
from colors import COLOR_SUCCESS, COLOR_ERROR, COLOR_INFO

def delay_and_exit(root, delay_ms=5000):
    root.after(delay_ms, root.quit)

def run_build(root):
    # Step 1: Notificar instalação
    show_message_notification("📦 Instalação", "A instalar dependências...", icon="📦", duration=4000, bg_color=COLOR_INFO)

    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        show_message_notification("✅ Concluído", "Dependências instaladas com sucesso.", icon="✅", duration=4000, bg_color=COLOR_SUCCESS)
    except subprocess.CalledProcessError as e:
        show_message_notification("❌ Erro", f"Falha na instalação das dependências.\n{e}", icon="❌", duration=6000, bg_color=COLOR_ERROR)
        delay_and_exit(root)
        return

    # Step 2: Verificar PyInstaller
    try:
        subprocess.run([sys.executable, "-m", "PyInstaller", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except subprocess.CalledProcessError:
        show_message_notification("❌ PyInstaller", "O PyInstaller não está instalado!", icon="❌", duration=6000, bg_color=COLOR_ERROR)
        delay_and_exit(root)
        return

    # Step 3: Iniciar build
    show_message_notification("⚙️ Build", "A construir o executável...", icon="⚙️", duration=4000, bg_color=COLOR_INFO)

    pyinstaller_command = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--onefile",
        "--noconsole",
        "--hidden-import", "customtkinter",
        "--hidden-import", "ctkmessagebox",
        "--icon", "assets/icons/icon_soft.ico",
        "--version-file", "version.txt", 
        "goal_score.py"
    ]

    try:
        subprocess.run(pyinstaller_command, check=True)
        show_message_notification("🎉 Sucesso", "Build concluída com sucesso!", icon="✅", duration=6000, bg_color=COLOR_SUCCESS)
    except subprocess.CalledProcessError as e:
        show_message_notification("❌ Build Falhou", f"Erro durante o build.\n{e}", icon="❌", duration=6000, bg_color=COLOR_ERROR)

    delay_and_exit(root)

root = tk.Tk()
root.withdraw()

threading.Thread(target=run_build, args=(root,), daemon=True).start()

root.mainloop()
