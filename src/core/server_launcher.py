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
from typing import Optional, IO, Any, Tuple
from src.config.settings import AppConfig
from src.core.config_manager import get_config
from src.core.path_finder import get_path_finder
from src.core.logger import get_logger

class ServerLauncher:
    """Manages the futebol-server.exe process."""
    
    def __init__(self) -> None:
        self.server_process: Optional[subprocess.Popen] = None
        self._startup_lock = threading.Lock()
        self._startup_lock_fd: Optional[int] = None
        self._log_handle: Optional[IO[str]] = None
        self._log = get_logger(__name__)
        self._last_debug_time: float = 0.0
        # Firewall tracking (delete only if we added it)
        self._firewall_rule_added = False
        # Watchdog thread for unexpected exits
        self._watchdog_thread: Optional[threading.Thread] = None
        self._watchdog_stop = threading.Event()
        # Windows named mutex handle for startup lock (optional)
        self._startup_mutex_handle: Optional[int] = None
        # Windows Job Object to reap children
        self._job_handle: Optional[int] = None
    
    def get_server_path(self) -> Path:
        """Get the path to the server executable based on AppConfig.SERVER_NAME_APP."""
        frozen = getattr(sys, 'frozen', False)
        rel = AppConfig.SERVER_NAME_APP
        rel_path = Path(rel.lstrip("/\\")) if isinstance(rel, str) else Path(rel)
        pf = get_path_finder()

        if frozen:
            # Prefer a stable per-user cache path so the firewall rule stays valid across runs
            try:
                stable_dir = pf.user_local_appdir(AppConfig.LOCAL_APP_DIRNAME, AppConfig.SERVER_CACHE_DIRNAME)
                stable_dir.mkdir(parents=True, exist_ok=True)
                stable_path = stable_dir / rel_path.name

                # If not present or different from packaged executable, copy from packaged location once
                packaged_path = pf.resource(rel_path.as_posix())
                if packaged_path.exists():
                    try:
                        need_copy = (not stable_path.exists()) or (stable_path.stat().st_size != packaged_path.stat().st_size)
                        if need_copy:
                            import shutil
                            shutil.copy2(str(packaged_path), str(stable_path))
                        else:
                            # Optional additional validation: version/hash check (best-effort)
                            try:
                                # If enabled, validate binary hash and refresh cache if mismatch
                                if getattr(AppConfig, 'SERVER_HASH_VALIDATE', False):
                                    import hashlib
                                    def _sha256(p: Path) -> str:
                                        h = hashlib.sha256()
                                        with open(p, 'rb') as f:
                                            for chunk in iter(lambda: f.read(65536), b''):
                                                h.update(chunk)
                                        return h.hexdigest()
                                    src_hash = _sha256(packaged_path)
                                    dst_hash = _sha256(stable_path)
                                    if src_hash != dst_hash:
                                        import shutil as _sh
                                        _sh.copy2(str(packaged_path), str(stable_path))
                                elif packaged_path.stat().st_mtime > stable_path.stat().st_mtime:
                                    import shutil as _sh
                                    _sh.copy2(str(packaged_path), str(stable_path))
                            except Exception:
                                pass
                    except Exception:
                        pass
                return stable_path
            except Exception:
                # Fallback to packaged path
                return pf.resource(rel_path.as_posix())
        else:
            return pf.project_root() / rel_path
    
    def _any_server_running(self) -> bool:
        """Check across the whole system if futebol-server.exe is running."""
        try:
            import psutil
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
                if getattr(AppConfig, 'DEBUG_MODE', False):
                    if hasattr(self, '_last_debug_time'):
                        current_time = time.time()
                        if current_time - self._last_debug_time > 5:
                            try:
                                self._log.debug('server_process_check', extra={"pid": self.server_process.pid, "poll": poll_result, "alive": is_alive})
                            except Exception:
                                pass
                            self._last_debug_time = current_time
                    else:
                        self._last_debug_time = time.time()
                        try:
                            self._log.debug('server_process_check', extra={"pid": self.server_process.pid, "poll": poll_result, "alive": is_alive})
                        except Exception:
                            pass
                if is_alive:
                    return True
            except Exception as e:
                try:
                    self._log.error('server_process_check_error', exc_info=True)
                except Exception:
                    pass

        # Fallback to cross-process check
        return self._any_server_running()

    def _acquire_startup_lock(self) -> Optional[int]:
        """Acquire a cross-process startup lock to avoid race conditions."""
        # Try Windows named mutex first (best-effort)
        if os.name == 'nt':
            try:
                import ctypes
                from ctypes import wintypes
                kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
                CreateMutex = kernel32.CreateMutexW
                CreateMutex.argtypes = (wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR)
                CreateMutex.restype = wintypes.HANDLE
                GetLastError = kernel32.GetLastError
                ERROR_ALREADY_EXISTS = 183
                name = f"Global\\{AppConfig.FIREWALL_RULE_NAME}.startup.lock"
                handle = CreateMutex(None, True, name)
                if handle:
                    already = (GetLastError() == ERROR_ALREADY_EXISTS)
                    if already:
                        # release and treat as not acquired
                        try:
                            kernel32.ReleaseMutex(handle)
                            kernel32.CloseHandle(handle)
                        except Exception:
                            pass
                        return None
                    self._startup_mutex_handle = int(handle)
                    # Return sentinel fd value to indicate mutex path
                    return -1
            except Exception:
                pass
        # Fallback to file lock
        try:
            import tempfile as _temp
            lock_path = Path(_temp.gettempdir()) / AppConfig.STARTUP_LOCK_FILENAME
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_RDWR)
            self._startup_lock_fd = fd
            return fd
        except FileExistsError:
            return None
        except Exception as e:
            try:
                self._log.warning('startup_lock_failed', exc_info=True)
            except Exception:
                pass
            return None

    def _release_startup_lock(self) -> None:
        try:
            # Release file lock
            if self._startup_lock_fd is not None and self._startup_lock_fd != -1:
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
        # Release mutex if held
        if self._startup_mutex_handle and os.name == 'nt':
            try:
                import ctypes
                kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
                kernel32.ReleaseMutex(self._startup_mutex_handle)
                kernel32.CloseHandle(self._startup_mutex_handle)
            except Exception:
                pass
            finally:
                self._startup_mutex_handle = None
    
    def _open_log_handle(self) -> Optional[IO[str]]:
        """Open a log file on Desktop folder to capture server output."""
        try:
            logs_dir = Path.home() / "Desktop" / AppConfig.DESKTOP_FOLDER_NAME / "logs"
            logs_dir.mkdir(parents=True, exist_ok=True)
            log_path = logs_dir / "futebol-server.log"
            fh = open(log_path, "a", encoding="utf-8", buffering=1)
            return fh
        except Exception:
            return None

    def _metrics_path(self) -> Path:
        try:
            pf = get_path_finder()
            base = pf.user_local_appdir(AppConfig.LOCAL_APP_DIRNAME, "server")
            base.mkdir(parents=True, exist_ok=True)
            return base / getattr(AppConfig, 'SERVER_METRICS_FILENAME', 'server_metrics.json')
        except Exception:
            return Path(getattr(AppConfig, 'SERVER_METRICS_FILENAME', 'server_metrics.json'))

    def _write_metrics(self, status: str, extra: Optional[dict] = None) -> None:
        try:
            import json as _json
            from datetime import datetime, timezone
            p = self._metrics_path()
            p.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "status": status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            if extra:
                data.update(extra)
            with open(p, "w", encoding="utf-8") as f:
                _json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _windows_hide_startup(self) -> Tuple[int, Optional[Any]]:
        flags: int = 0
        startupinfo: Optional[Any] = None
        if os.name == 'nt':
            flags = (
                getattr(subprocess, 'CREATE_NO_WINDOW', 0) |
                getattr(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0)
            )
            try:
                si = subprocess.STARTUPINFO()
                si.dwFlags |= getattr(subprocess, 'STARTF_USESHOWWINDOW', 0)
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
                    si = subprocess.STARTUPINFO()
                    si.dwFlags |= getattr(subprocess, 'STARTF_USESHOWWINDOW', 0)
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
            # Check if rule exists already
            try:
                out = subprocess.check_output([
                    "netsh", "advfirewall", "firewall", "show", "rule",
                    f"name={rule_name}"
                ], creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                exists = b"No rules" not in out
            except Exception:
                exists = False
            if not exists:
                self._run_hidden([
                    "netsh", "advfirewall", "firewall", "add", "rule",
                    f"name={rule_name}", "dir=in", "action=allow",
                    "program=" + str(exe_path), "enable=yes", f"profile={profiles}"
                ])
                self._firewall_rule_added = True
        except Exception:
            pass
    
    def _remove_firewall_rule(self) -> None:
        if os.name != 'nt':
            return
        try:
            rule_name = AppConfig.FIREWALL_RULE_NAME
            if self._firewall_rule_added:
                self._run_hidden([
                    "netsh", "advfirewall", "firewall", "delete", "rule",
                    f"name={rule_name}"
                ])
                self._firewall_rule_added = False
        except Exception:
            pass

    def _kill_server_processes(self) -> bool:
        """Kill any running futebol-server.exe processes by name (system-wide)."""
        exe_name = Path(AppConfig.SERVER_NAME_APP.lstrip("/\\")).name
        killed_any = False
        try:
            import psutil
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
                try:
                    self._write_metrics("started", {"pid": getattr(self.server_process, 'pid', None)})
                except Exception:
                    pass

                # Wait briefly to see if it starts successfully (non-blocking duration)
                time.sleep(max(0.02, AppConfig.SERVER_STARTUP_WAIT_MS / 1000.0))

                # Health check loop (optional, can be disabled by runtime config)
                try:
                    import urllib.request as _url
                    if not bool(get_config('server_health_check_enabled', True)):
                        total_ms = 0
                    else:
                        total_ms = int(getattr(AppConfig, 'SERVER_HEALTH_TIMEOUT_MS', 0))
                    retry_ms = max(50, int(getattr(AppConfig, 'SERVER_HEALTH_RETRY_MS', 300)))
                    url = getattr(AppConfig, 'SERVER_HEALTH_URL', '')
                    if total_ms > 0 and url:
                        deadline = time.time() + (total_ms / 1000.0)
                        ok_health = False
                        while time.time() < deadline:
                            try:
                                with _url.urlopen(url, timeout=1.0) as r:
                                    code = getattr(r, 'status', None) or r.getcode()
                                    if int(code) == 200:
                                        ok_health = True
                                        break
                            except Exception:
                                pass
                            time.sleep(retry_ms / 1000.0)
                        if not ok_health and getattr(AppConfig, 'DEBUG_MODE', False):
                            try:
                                self._log.warning('server_health_check_timeout')
                            except Exception:
                                pass
                except Exception:
                    pass

                # If it exited immediately, log return code for diagnostics
                rc = self.server_process.poll()
                if rc is not None and self._log_handle:
                    try:
                        self._log_handle.write(f"[launcher] Server exited immediately with code {rc}.\n")
                        self._log_handle.flush()
                    except Exception:
                        pass
                    try:
                        self._write_metrics("exited_immediately", {"return_code": rc})
                    except Exception:
                        pass

                ok = self._any_server_running()
                self._release_startup_lock()
                if not ok:
                    self.server_process = None
                    # Close log handle if we opened one
                    try:
                        if self._log_handle:
                            self._log_handle.close()
                    except Exception:
                        pass
                    self._log_handle = None
                    try:
                        self._write_metrics("failed_to_start")
                    except Exception:
                        pass
                return ok
                    
            except Exception as e:
                try:
                    self._log.error('server_start_error', exc_info=True)
                except Exception:
                    pass
                self.server_process = None
                self._release_startup_lock()
                # Close any open log handle on failure
                try:
                    if self._log_handle:
                        self._log_handle.close()
                except Exception:
                    pass
                self._log_handle = None
                try:
                    self._write_metrics("start_error")
                except Exception:
                    pass
                return False
            finally:
                # Start watchdog if enabled (frozen default + runtime override)
                try:
                    frozen = getattr(sys, 'frozen', False)
                    watchdog_enabled = bool(get_config('server_watchdog_enabled', False)) or (frozen and getattr(AppConfig, 'SERVER_WATCHDOG_ENABLED', False))
                    if watchdog_enabled and self.server_process is not None:
                        self._start_watchdog()
                except Exception:
                    pass
    
    def stop_server(self) -> bool:
        """Stop the server process."""
        # In development mode, nothing to stop
        if not getattr(sys, 'frozen', False):
            try:
                self._log.info('server_stop_dev_mode')
            except Exception:
                pass
            return True
            
        if self.server_process is None:
            # Ensure no leftover processes
            # Stop watchdog
            self._stop_watchdog()
            self._kill_server_processes()
            self._release_startup_lock()
            # Always remove firewall rule regardless of who spawned the server
            self._remove_firewall_rule()
            return True
        
        try:
            try:
                self._log.info('server_stopping')
            except Exception:
                pass
            self.server_process.terminate()
            
            # Wait for graceful shutdown
            try:
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    self._log.warning("server_force_kill")
                except Exception:
                    pass
                self.server_process.kill()
                self.server_process.wait()
            
            self.server_process = None
            self._release_startup_lock()
            # Stop watchdog
            self._stop_watchdog()
            try:
                if self._log_handle:
                    self._log_handle.close()
            except Exception:
                pass
            self._log_handle = None
            # Remove firewall rule on clean stop
            self._remove_firewall_rule()
            try:
                self._log.info('server_stopped')
            except Exception:
                pass
            try:
                self._write_metrics("stopped")
            except Exception:
                pass
            return True
            
        except Exception as e:
            try:
                self._log.error('server_stop_error', exc_info=True)
            except Exception:
                pass
            return False
    
    def restart_server(self) -> bool:
        """Restart the server process."""
        # In development mode, nothing to restart
        if not getattr(sys, 'frozen', False):
            try:
                self._log.info('server_restart_dev_mode')
            except Exception:
                pass
            return True
            
        try:
            self._log.info('server_restarting')
        except Exception:
            pass
        if self.stop_server():
            time.sleep(0.5)  # Brief pause before restart
            return self.start_server()
        return False
    
    def cleanup(self) -> None:
        """Clean up resources when shutting down."""
        # In development mode, nothing to clean up
        if not getattr(sys, 'frozen', False):
            return
            
        # Always attempt to stop and cleanup regardless of who spawned it
        self.stop_server()
        # Close job handle (kills children if configured)
        if self._job_handle and os.name == 'nt':
            try:
                import ctypes
                kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
                kernel32.CloseHandle(self._job_handle)
            except Exception:
                pass
            finally:
                self._job_handle = None

    # ---- Watchdog helpers ----
    def _start_watchdog(self) -> None:
        if self._watchdog_thread and self._watchdog_thread.is_alive():
            return
        self._watchdog_stop.clear()
        def run() -> None:
            import random
            base_ms = int(getattr(AppConfig, 'SERVER_WATCHDOG_BACKOFF_BASE_MS', 500))
            cap_ms = int(getattr(AppConfig, 'SERVER_WATCHDOG_BACKOFF_CAP_MS', 30000))
            jitter = float(getattr(AppConfig, 'SERVER_WATCHDOG_JITTER_PCT', 0.1))
            max_attempts = int(getattr(AppConfig, 'SERVER_WATCHDOG_MAX_ATTEMPTS', 5))
            window_ms = int(getattr(AppConfig, 'SERVER_WATCHDOG_WINDOW_MS', 10*60*1000))
            cooldown_ms = int(getattr(AppConfig, 'SERVER_WATCHDOG_COOLDOWN_MS', 5*60*1000))
            attempts: list[int] = []  # timestamps (ms) of recent restarts
            backoff_ms = base_ms
            while not self._watchdog_stop.is_set():
                try:
                    if self.server_process is None:
                        break
                    rc = self.server_process.poll()
                    if rc is None:
                        time.sleep(0.5)
                        continue
                    # Unexpected exit
                    now_ms = int(time.time() * 1000)
                    # Drop attempts outside window
                    attempts[:] = [t for t in attempts if now_ms - t <= window_ms]
                    attempts.append(now_ms)
                    if len(attempts) > max_attempts:
                        try:
                            self._log.error('server_exited_max_attempts', extra={"rc": rc})
                        except Exception:
                            pass
                        # Cooldown period
                        end = time.time() + (cooldown_ms / 1000.0)
                        while time.time() < end and not self._watchdog_stop.is_set():
                            time.sleep(0.5)
                        attempts.clear()
                        break
                    try:
                        self._log.warning('server_exited_restart', extra={"rc": rc, "attempt_count": len(attempts)})
                    except Exception:
                        pass
                    # Apply jittered backoff
                    sleep_ms = min(backoff_ms, cap_ms)
                    jitter_ms = int(sleep_ms * jitter)
                    sleep_actual = max(0, (sleep_ms + random.randint(-jitter_ms, jitter_ms)) / 1000.0)
                    end = time.time() + sleep_actual
                    while time.time() < end and not self._watchdog_stop.is_set():
                        time.sleep(0.1)
                    backoff_ms = min(backoff_ms * 2, cap_ms)
                    # Try restart
                    # Leader-only restart: only the holder of startup mutex/file lock should restart
                    # We try to acquire lock briefly; if unavailable, another process will handle
                    acquired = self._acquire_startup_lock()
                    if acquired is None:
                        # someone else will try
                        continue
                    try:
                        self.start_server()
                    finally:
                        self._release_startup_lock()
                except Exception:
                    time.sleep(1.0)
                    continue
        t = threading.Thread(target=run, daemon=True)
        self._watchdog_thread = t
        t.start()

    def _stop_watchdog(self) -> None:
        try:
            self._watchdog_stop.set()
            if self._watchdog_thread and self._watchdog_thread.is_alive():
                self._watchdog_thread.join(timeout=2.0)
        except Exception:
            pass
        finally:
            self._watchdog_thread = None

# Global instance
_server_launcher = ServerLauncher()

def get_server_launcher() -> ServerLauncher:
    """Get the global server launcher instance."""
    return _server_launcher

def start_server_after_license() -> bool:
    """Start the server after license validation."""
    return get_server_launcher().start_server()

def stop_server_on_exit() -> None:
    """Stop the server when the application exits."""
    get_server_launcher().cleanup()
