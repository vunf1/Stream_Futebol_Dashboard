"""
Server Launcher Module
Handles launching the futebol-server.exe after license validation.
"""

import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Optional
from src.config.settings import AppConfig

class ServerLauncher:
    """Manages the futebol-server.exe process."""
    
    def __init__(self):
        self.server_process: Optional[subprocess.Popen] = None
        self._startup_lock = threading.Lock()
        self._startup_lock_fd: Optional[int] = None
        self._log_handle = None
    
    def get_server_path(self) -> Path:
        """Get the path to the server executable based on AppConfig.SERVER_NAME_APP."""
        frozen = getattr(sys, 'frozen', False)
        rel = AppConfig.SERVER_NAME_APP
        rel_path = Path(rel.lstrip("/\\")) if isinstance(rel, str) else Path(rel)

        if frozen:
            # Prefer a stable per-user cache path so the firewall rule stays valid across runs
            try:
                base_cache = Path(os.getenv("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
                stable_dir = base_cache / AppConfig.LOCAL_APP_DIRNAME / AppConfig.SERVER_CACHE_DIRNAME
                stable_dir.mkdir(parents=True, exist_ok=True)
                stable_path = stable_dir / rel_path.name

                # If not present or different from packaged executable, copy from _MEIPASS once
                meipass = getattr(sys, '_MEIPASS', None)
                src_base = Path(meipass) if meipass else Path(__file__).parent.parent.parent
                packaged_path = src_base / rel_path
                if packaged_path.exists():
                    try:
                        if (not stable_path.exists()) or (stable_path.stat().st_size != packaged_path.stat().st_size):
                            import shutil
                            shutil.copy2(str(packaged_path), str(stable_path))
                    except Exception:
                        pass
                return stable_path
            except Exception:
                # Fallback to _MEIPASS packaged path
                meipass = getattr(sys, '_MEIPASS', None)
                base_path = Path(meipass) if meipass else Path(__file__).parent.parent.parent
                return base_path / rel_path
        else:
            base_path = Path(__file__).parent.parent.parent
            return base_path / rel_path
    
    def _any_server_running(self) -> bool:
        """Check across the whole system if futebol-server.exe is running."""
        try:
            import psutil  # type: ignore
            exe_name_l = Path(AppConfig.SERVER_NAME_APP.lstrip("/\\")).name.lower()
            for p in psutil.process_iter(attrs=["name"]):
                try:
                    name = (p.info.get("name") or "").lower()
                    if name == exe_name_l:
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return False
        except Exception:
            # Fallback for Windows without psutil
            if os.name != "nt":
                return False
            try:
                exe_name = Path(AppConfig.SERVER_NAME_APP.lstrip("/\\")).name
                out = subprocess.check_output(
                    ["tasklist", "/FI", f"IMAGENAME eq {exe_name}", "/FO", "CSV", "/NH"],
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
                )
                text = out.decode(errors="ignore").strip()
                return bool(text) and ("No tasks" not in text)
            except Exception:
                return False

    def is_server_running(self) -> bool:
        """Check if the server is running (local handle first, then system-wide)."""
        # In development mode, always return False since we don't start the server
        if not getattr(sys, 'frozen', False):
            return False

        # Prefer checking the tracked process if we started it
        if self.server_process is not None:
            try:
                poll_result = self.server_process.poll()
                is_alive = poll_result is None
                if hasattr(self, '_last_debug_time'):
                    current_time = time.time()
                    if current_time - self._last_debug_time > 5:
                        print(f"📍 Server process check - PID: {self.server_process.pid}, Poll: {poll_result}, Alive: {is_alive}")
                        self._last_debug_time = current_time
                else:
                    self._last_debug_time = time.time()
                    print(f"📍 Server process check - PID: {self.server_process.pid}, Poll: {poll_result}, Alive: {is_alive}")
                if is_alive:
                    return True
            except Exception as e:
                print(f"❌ Error checking server process: {e}")

        # Fallback to cross-process check
        return self._any_server_running()

    def _acquire_startup_lock(self) -> Optional[int]:
        """Acquire a cross-process startup lock to avoid race conditions."""
        try:
            import tempfile as _temp
            lock_path = Path(_temp.gettempdir()) / AppConfig.STARTUP_LOCK_FILENAME
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_RDWR)
            self._startup_lock_fd = fd
            return fd
        except FileExistsError:
            return None
        except Exception as e:
            print(f"⚠️ Could not acquire startup lock (non-fatal): {e}")
            return None

    def _release_startup_lock(self) -> None:
        try:
            if self._startup_lock_fd is not None:
                os.close(self._startup_lock_fd)
                self._startup_lock_fd = None
            import tempfile as _temp
            lock_path = Path(_temp.gettempdir()) / AppConfig.STARTUP_LOCK_FILENAME
            if lock_path.exists():
                try:
                    lock_path.unlink()
                except Exception:
                    pass
        except Exception:
            pass
    
    def _open_log_handle(self):
        """Open a log file on Desktop folder to capture server output."""
        try:
            logs_dir = Path.home() / "Desktop" / AppConfig.DESKTOP_FOLDER_NAME / "logs"
            logs_dir.mkdir(parents=True, exist_ok=True)
            log_path = logs_dir / "futebol-server.log"
            fh = open(log_path, "a", encoding="utf-8", buffering=1)
            return fh
        except Exception:
            return None

    def _windows_hide_startup(self):
        flags = 0
        startupinfo = None
        if os.name == 'nt':
            flags = (
                getattr(subprocess, 'CREATE_NO_WINDOW', 0) |
                getattr(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0)
            )
            try:
                si = subprocess.STARTUPINFO()  # type: ignore[attr-defined]
                si.dwFlags |= getattr(subprocess, 'STARTF_USESHOWWINDOW', 0)  # type: ignore[attr-defined]
                si.wShowWindow = 0  # SW_HIDE
                startupinfo = si
            except Exception:
                startupinfo = None
        return flags, startupinfo

    def _run_hidden(self, args: list[str]) -> None:
        """Run a subprocess hidden on Windows (no console flicker)."""
        try:
            flags = 0
            startupinfo = None
            if os.name == 'nt':
                flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
                try:
                    si = subprocess.STARTUPINFO()  # type: ignore[attr-defined]
                    si.dwFlags |= getattr(subprocess, 'STARTF_USESHOWWINDOW', 0)  # type: ignore[attr-defined]
                    si.wShowWindow = 0
                    startupinfo = si
                except Exception:
                    startupinfo = None
            subprocess.run(
                args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=flags,
                startupinfo=startupinfo,
            )
        except Exception:
            pass

    def _preauthorize_firewall(self, exe_path: Path) -> None:
        if os.name != 'nt':
            return
        try:
            rule_name = AppConfig.FIREWALL_RULE_NAME
            profiles = AppConfig.FIREWALL_PROFILES
            self._run_hidden([
                "netsh", "advfirewall", "firewall", "add", "rule",
                f"name={rule_name}", "dir=in", "action=allow",
                "program=" + str(exe_path), "enable=yes", f"profile={profiles}"
            ])
        except Exception:
            pass
    
    def _remove_firewall_rule(self) -> None:
        if os.name != 'nt':
            return
        try:
            rule_name = AppConfig.FIREWALL_RULE_NAME
            self._run_hidden([
                "netsh", "advfirewall", "firewall", "delete", "rule",
                f"name={rule_name}"
            ])
        except Exception:
            pass

    def _kill_server_processes(self) -> bool:
        """Kill any running futebol-server.exe processes by name (system-wide)."""
        exe_name = Path(AppConfig.SERVER_NAME_APP.lstrip("/\\")).name
        killed_any = False
        try:
            import psutil  # type: ignore
            for p in psutil.process_iter(attrs=["name"]):
                try:
                    name = (p.info.get("name") or "").lower()
                    if name == exe_name.lower():
                        try:
                            p.terminate()
                            p.wait(timeout=3)
                        except Exception:
                            try:
                                p.kill()
                                p.wait(timeout=2)
                            except Exception:
                                pass
                        killed_any = True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception:
            # Fallback to taskkill on Windows
            if os.name == 'nt':
                try:
                    self._run_hidden(["taskkill", "/IM", exe_name, "/F"])
                    killed_any = True
                except Exception:
                    pass
        return killed_any
    
    def start_server(self) -> bool:
        """Start the futebol-server.exe process."""
        with self._startup_lock:
            if self.server_process is not None and self.is_server_running():
                return True  # Already running
            
            # Check if we're running in development mode
            frozen = getattr(sys, 'frozen', False)
            if not frozen:
                return True  # Return True to avoid errors, but don't actually start server
            
            try:
                # If another instance already launched it, skip
                if self._any_server_running():
                    return True

                # Acquire startup lock to avoid race across multiple app processes
                fd = self._acquire_startup_lock()
                if fd is None:
                    for _ in range(10):  # wait up to ~5s
                        time.sleep(0.5)
                        if self._any_server_running():
                            return True
                    # Try to acquire once more; if still unavailable, abort to prevent dupes
                    fd = self._acquire_startup_lock()
                    if fd is None:
                        return self._any_server_running()

                server_path = self.get_server_path()
                if not server_path.exists():
                    return False

                # Pre-authorize firewall (best-effort)
                self._preauthorize_firewall(server_path.resolve())

                # Start server process with working directory set to the server folder
                self._log_handle = self._open_log_handle()
                flags, startupinfo = self._windows_hide_startup()
                self.server_process = subprocess.Popen(
                    [str(server_path)],
                    cwd=str(server_path.parent),
                    stdin=subprocess.DEVNULL,
                    stdout=(self._log_handle if self._log_handle else subprocess.DEVNULL),
                    stderr=(subprocess.STDOUT if self._log_handle else subprocess.DEVNULL),
                    close_fds=True,
                    creationflags=flags,
                    startupinfo=startupinfo
                )

                # Wait briefly to see if it starts successfully (non-blocking duration)
                time.sleep(max(0.02, AppConfig.SERVER_STARTUP_WAIT_MS / 1000.0))

                # If it exited immediately, log return code for diagnostics
                rc = self.server_process.poll()
                if rc is not None and self._log_handle:
                    try:
                        self._log_handle.write(f"[launcher] Server exited immediately with code {rc}.\n")
                        self._log_handle.flush()
                    except Exception:
                        pass

                ok = self._any_server_running()
                self._release_startup_lock()
                if not ok:
                    self.server_process = None
                return ok
                    
            except Exception as e:
                print(f"❌ Error starting server: {e}")
                import traceback
                traceback.print_exc()
                self.server_process = None
                self._release_startup_lock()
                return False
    
    def stop_server(self) -> bool:
        """Stop the server process."""
        # In development mode, nothing to stop
        if not getattr(sys, 'frozen', False):
            print("🚫 No server to stop - running in development mode")
            return True
            
        if self.server_process is None:
            # Ensure no leftover processes
            self._kill_server_processes()
            self._release_startup_lock()
            # Always remove firewall rule regardless of who spawned the server
            self._remove_firewall_rule()
            return True
        
        try:
            print("🛑 Stopping server...")
            self.server_process.terminate()
            
            # Wait for graceful shutdown
            try:
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print("⚠️ Server didn't stop gracefully, forcing termination...")
                self.server_process.kill()
                self.server_process.wait()
            
            self.server_process = None
            self._release_startup_lock()
            try:
                if self._log_handle:
                    self._log_handle.close()
            except Exception:
                pass
            self._log_handle = None
            # Remove firewall rule on clean stop
            self._remove_firewall_rule()
            print("✅ Server stopped")
            return True
            
        except Exception as e:
            print(f"❌ Error stopping server: {e}")
            return False
    
    def restart_server(self) -> bool:
        """Restart the server process."""
        # In development mode, nothing to restart
        if not getattr(sys, 'frozen', False):
            print("🚫 No server to restart - running in development mode")
            return True
            
        print("🔄 Restarting server...")
        if self.stop_server():
            time.sleep(0.5)  # Brief pause before restart
            return self.start_server()
        return False
    
    def cleanup(self):
        """Clean up resources when shutting down."""
        # In development mode, nothing to clean up
        if not getattr(sys, 'frozen', False):
            return
            
        # Always attempt to stop and cleanup regardless of who spawned it
        self.stop_server()

# Global instance
_server_launcher = ServerLauncher()

def get_server_launcher() -> ServerLauncher:
    """Get the global server launcher instance."""
    return _server_launcher

def start_server_after_license() -> bool:
    """Start the server after license validation."""
    return get_server_launcher().start_server()

def stop_server_on_exit():
    """Stop the server when the application exits."""
    get_server_launcher().cleanup()
