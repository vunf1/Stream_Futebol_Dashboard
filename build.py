import subprocess
import sys
import tkinter as tk
import threading
import time
import os
from pathlib import Path

from src.ui.make_drag_drop import make_it_drag_and_drop

# ───────────────────────── Bootstrap (before CTk import) ─────────────────────────

def fallback_notify(msg: str):
    print(msg)
    try:
        root = tk.Tk()
        root.withdraw()
        tk.messagebox.showerror("Erro", msg)  # type: ignore
    except Exception:
        pass

def _creationflags():
    if os.name == "nt":
        try:
            return subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
        except Exception:
            return 0
    return 0

def run_cmd_quiet(args, *, name: str):
    """
    Run a command with no console output. If it fails, re-run capturing stderr
    so we can show a helpful error.
    """
    print(f"🔧 Running: {' '.join(args)}")
    rc = subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                        creationflags=_creationflags()).returncode
    if rc != 0:
        print(f"❌ Command failed with exit code {rc}")
        cp = subprocess.run(args, capture_output=True, text=True,
                            creationflags=_creationflags())
        stderr = (cp.stderr or "").strip()
        stdout = (cp.stdout or "").strip()
        error_msg = stderr or f"{name} falhou (exit {cp.returncode})"
        if stdout:
            print(f"stdout: {stdout}")
        if stderr:
            print(f"stderr: {stderr}")
        raise RuntimeError(error_msg)
    else:
        print(f"✅ Command completed successfully")

def install_dependencies() -> None:
    """Install runtime deps once (skip when frozen)."""
    if getattr(sys, "frozen", False):
        return
    try:
        run_cmd_quiet(
            [sys.executable, "-m", "pip", "install",
             "--disable-pip-version-check", "--no-input", "--quiet",
             "-r", "requirements.txt"],
            name="pip install"
        )
    except Exception as e:
        fallback_notify(f"Falha na instalação das dependências:\n{e}")
        sys.exit(1)

def generate_secret_key() -> None:
    """Create/refresh Fernet secret before imports that need it (dev only)."""
    if getattr(sys, "frozen", False):
        return
    try:
        run_cmd_quiet([sys.executable, os.path.join("src", "security", "generate_secret.py")],
                      name="generate_secret")
    except Exception as e:
        fallback_notify(f"Erro ao gerar chave secreta:\n{e}")
        sys.exit(1)

install_dependencies()
generate_secret_key()

# ───────────────────────── Safe imports (after deps) ─────────────────────────

import customtkinter as ctk
from multiprocessing import Manager, Process
from src.ui.colors import COLOR_SUCCESS, COLOR_ERROR, COLOR_INFO

# notifications (queue + server)
from src.notification.toast import init_notification_queue, show_message_notification
from src.notification.notification_server import server_main

# UI utilities
from src.ui import get_icon_path


# ───────────────────────── Notifications glue ─────────────────────────

def start_notification_server():
    """Spin up the toast renderer process and init this process to enqueue."""
    mgr = Manager()
    q = mgr.Queue()
    init_notification_queue(q)
    p = Process(target=server_main, args=(q,), daemon=True)
    p.start()
    return q, p

def notify(title, message, *, icon="ℹ️", duration=5000, bg=None, anchor=None, group=None):
    """
    Wrapper for toasts. duration=0 => 'sticky' (~1h). User can click to dismiss.
    """
    if duration == 0:
        duration = 60 * 60 * 1000
    show_message_notification(
        title=title, message=message, duration=duration,
        icon=icon, bg_color=bg, anchor=anchor, group=group
    )

# ───────────────────────── Process / file guards ─────────────────────────

def set_build_profile(profile: str) -> None:
    os.environ["BUILD_PROFILE"] = profile

def _pids_for_exe(exe_name: str, target_path: Path | None = None) -> list[int]:
    """
    Return PIDs for running processes that match the exe name.
    Tries psutil if available (can also match full path), else falls back to tasklist.
    """
    try:
        import psutil  # optional
        exe_name_l = exe_name.lower()
        target = str(target_path.resolve()).lower() if target_path else None
        pids = []
        for p in psutil.process_iter(attrs=["name", "exe"]):
            try:
                name = (p.info.get("name") or "").lower()
                if name != exe_name_l:
                    continue
                if target:
                    exe = (p.info.get("exe") or "").lower()
                    # allow even if path differs; name match is enough to block
                    # uncomment to enforce exact path: if exe != target: continue
                pids.append(p.pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return pids
    except Exception:
        # Fallback: Windows tasklist (name-only)
        if os.name != "nt":
            return []
        import csv, io
        try:
            out = subprocess.check_output(
                ["tasklist", "/FI", f"IMAGENAME eq {exe_name}", "/FO", "CSV", "/NH"],
                creationflags=_creationflags()
            )
            lines = io.StringIO(out.decode(errors="ignore"))
            rdr = csv.reader(lines)
            pids = []
            for row in rdr:
                if not row or "No tasks" in row[0]:
                    continue
                try:
                    pids.append(int(row[1]))
                except Exception:
                    pass
            return pids
        except Exception:
            return []

def wait_until_apps_closed(exe_names: list[str], poll_ms: int = 800):
    """
    Show ONE sticky toast asking the user to close the listed apps.
    Block until no such processes are running. Then show a quick success toast.
    """
    shown = False
    label = ", ".join(exe_names)
    group_id = "close-running-apps"

    while True:
        running = []
        for name in exe_names:
            if _pids_for_exe(name):
                running.append(name)
        if not running:
            break
        if not shown:
            notify("❗ Fecha a app",
                   f"Fecha {label} antes de continuar!",
                   icon="❌", duration=0, bg=COLOR_ERROR, group=group_id)
            shown = True
        time.sleep(max(0.1, poll_ms / 1000.0))

    if shown:
        notify("✅ Fechado", f"{label} foi fechado.",
               icon="✅", duration=2000, bg=COLOR_SUCCESS, group=group_id)

def delete_old_executable(path: Path, poll_ms: int = 700):
    """
    Remove an old binary (after processes are closed). If AV temporarily locks
    the file, retry until it disappears.
    """
    if not path.exists():
        return
    while path.exists():
        try:
            path.unlink()
            break
        except (PermissionError, OSError):
            time.sleep(max(0.1, poll_ms / 1000.0))

def add_data(src, dst):
    # PyInstaller wants ';' on Windows, ':' on macOS/Linux
    sep = ';' if os.name == 'nt' else ':'
    return f"{src}{sep}{dst}"

def validate_build_environment():
    """Validate that all required files exist before starting the build"""
    required_files = [
        "src/goal_score.py",
        "src/ui/icons/icon_soft.ico",
        "version.txt",
        "requirements.txt"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        error_msg = f"Missing required files for build:\n" + "\n".join(f"  - {f}" for f in missing_files)
        print(f"❌ {error_msg}")
        raise RuntimeError(error_msg)
    
    print("✅ Build environment validation passed")
    return True
# ───────────────────────── UI ─────────────────────────

class BuildWindow(ctk.CTk):
    def __init__(self):
        super().__init__()  # type: ignore
        self.configure_gui()
        self.create_widgets()
        make_it_drag_and_drop(self)  # type: ignore
        self.attributes("-topmost", True)  # type: ignore
        threading.Thread(target=self.run_build_steps, daemon=True).start()

    # inside BuildWindow

    def _pct(self) -> int:
        if not getattr(self, "_progress_total", 0):
            return 0
        return int(round(100 * (self._progress_done / self._progress_total)))

    def configure_gui(self):
        self.overrideredirect(True)
        self.geometry("460x130")
        try:
            self.eval('tk::PlaceWindow . center')
        except Exception:
            pass
        try:
            self.iconbitmap(get_icon_path("icon_soft"))  # type: ignore
        except Exception:
            pass
        self.configure(fg_color="#222222")  # type: ignore

    def create_widgets(self):
        self.label = ctk.CTkLabel(self, text="☕ A preparar a magia...", font=("Segoe UI", 16))
        self.label.pack(pady=(20, 8))  # type: ignore

        self.progress = ctk.CTkProgressBar(self, orientation="horizontal", mode="determinate", width=320)
        self.progress.pack(pady=6)  # type: ignore
        self.progress.set(0)  # type: ignore

        self.error_label = ctk.CTkLabel(
            self, text="", font=("Segoe UI", 11), text_color="white",
            wraplength=380, justify="left", cursor="hand2"
        )
        self.error_label.pack(pady=(0, 6))  # type: ignore
        self.error_label.pack_forget()
        self.error_label.bind("<Button-1>", self.copy_error_to_clipboard)

        self.close_button = ctk.CTkButton(self, text="Fechar", command=self.quit, fg_color="gray")
        self.close_button.pack(pady=(4, 0))  # type: ignore
        self.close_button.pack_forget()

    # -------- progress/steps orchestration --------

    def step(self, msg: str, weight: float, fn):
        """Run a build step with UI + toasts (start + success) and weighted progress."""
        group_id = "build-progress"

        # START toast (sticky)
        notify(f"🔧 {msg}",
            f"Progresso: {self._pct()}%",
            icon="ℹ️", duration=0, bg=COLOR_INFO, group=group_id)

        # UI
        self.label.configure(text=msg)
        self.update_idletasks()

        # Work
        t0 = time.perf_counter()
        try:
            fn()
            self._progress_done += weight
            frac = min(1.0, self._progress_done / self._progress_total)
            self.progress.set(frac)

            # Throttle visual jitter
            elapsed = time.perf_counter() - t0
            if elapsed < 0.12:
                time.sleep(0.12 - elapsed)

            # DONE toast (your success style)
            notify("✅ Passo concluído",
                f"{msg} concluído ({self._pct()}%).",
                icon="✅", duration=2000, bg=COLOR_SUCCESS, group=group_id)
        except Exception as e:
            print(f"❌ Step '{msg}' failed: {e}")
            import traceback
            traceback.print_exc()
            raise  # Re-raise to be caught by the main error handler
            
    
    def run_build_steps(self):
        try:
            EXE_NAMES = ["goal_score.exe", "Futebol Dashboard.exe"]
            DIST_PATHS = [Path("dist") / n for n in EXE_NAMES]

            STEPS = [ 
                ("🔍 Validando ambiente…",     0.5, lambda: validate_build_environment()),
                ("🛑 Aguardando fecho…",       1.0, lambda: wait_until_apps_closed(EXE_NAMES)),
                ("🔖 Gerando version.txt…",    1.0, lambda: run_cmd_quiet([sys.executable, "version_gen.py"], name="version_gen")),
                ("🧭 Definindo perfil: release", 0.2, lambda: set_build_profile("release")), 
                ("📄 Gerando goal_score.spec…",  0.8, lambda: run_cmd_quiet([sys.executable, "spec_gen.py"], name="spec_gen")),
                ("🧹 A limpar builds antigas…", 1.0, lambda: [delete_old_executable(p) for p in DIST_PATHS]),
                ("⚙️ A montar com PyInstaller…", 5.0, lambda: run_cmd_quiet([
                    sys.executable, "-m", "PyInstaller",
                    "--clean", "--onefile", "--noconsole", "--noconfirm",
                    "--hidden-import", "customtkinter",
                    "--hidden-import", "ctkmessagebox",
                    "--add-data", add_data("src/ui/icons", "src/ui/icons"),
                    "--add-data", add_data(".env.enc", "."),
                    "--add-data", add_data("secret.key", "."),
                    "--icon", "src/ui/icons/icon_soft.ico",
                    "--version-file", "version.txt",
                    "src/goal_score.py"
                ], name="PyInstaller")),
                ("⚽ A iniciar os jogos…",      1.5, lambda: time.sleep(0.2)),
                ("🎯 Remate final…",           1.5, lambda: time.sleep(0.2)),
            ]

            self._progress_total = sum(w for _, w, _ in STEPS)
            self._progress_done = 0.0
            self.progress.set(0)

            for msg, weight, fn in STEPS:
                self.step(msg, weight, fn)

            self.label.configure(text="🏆 Golo! Build concluída com sucesso!")
            notify("🎉 Sucesso", "O executável foi criado com sucesso!",
                   icon="🎯", duration=6000, bg=COLOR_SUCCESS)
            time.sleep(0.6)
            self.quit()

        except Exception as e:
            # Print error to console for debugging
            print(f"❌ BUILD ERROR: {e}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            
            notify("💥 Erro no Build", f"Ocorreu um erro:\n{e}", icon="❌", duration=7000, bg=COLOR_ERROR)
            self.label.configure(text="💥 Algo correu mal no feitiço...")
            self.last_error_text = f"Detalhes técnicos:\n{e}"
            self.error_label.configure(text=self.last_error_text)
            self.error_label.pack()
            self.close_button.pack()
            self.update_idletasks()
            new_height = max(160, self.winfo_reqheight())
            self.geometry(f"460x{new_height}")

    def copy_error_to_clipboard(self, _event=None):
        if not hasattr(self, "last_error_text"):
            return
        self.clipboard_clear()
        self.clipboard_append(self.last_error_text)
        notify("📋 Copiado", "O erro foi copiado.", icon="✅", duration=3000, bg=COLOR_SUCCESS)


# ───────────────────────── Entrypoint ─────────────────────────

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    q, _p = start_notification_server()

    # stop toast server on exit
    import atexit
    atexit.register(lambda: q.put(None))

    app = BuildWindow()
    app.mainloop()
