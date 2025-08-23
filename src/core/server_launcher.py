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
        self.server_started = False
        self._startup_lock = threading.Lock()
    
    def get_server_path(self) -> Path:
        """Get the path to the server executable."""
        frozen = getattr(sys, 'frozen', False)
        print(f"🔍 get_server_path - sys.frozen: {frozen}")
        
        if frozen:
            # Running as PyInstaller bundle
            meipass = getattr(sys, '_MEIPASS', None)
            print(f"📍 Bundle mode - sys._MEIPASS: {meipass}")
            
            if meipass is None:
                print("❌ Bundle mode but sys._MEIPASS is None!")
                # Fallback to development path
                base_path = Path(__file__).parent.parent.parent
                server_path = base_path / "server" / "futebol-server.exe"
                print(f"📍 Falling back to development path: {server_path}")
            else:
                base_path = Path(meipass)
                server_path = base_path / "server" / "futebol-server.exe"
                print(f"📍 Bundle path resolved: {server_path}")
        else:
            # Running in development mode
            base_path = Path(__file__).parent.parent.parent
            server_path = base_path / "server" / "futebol-server.exe"
            print(f"📍 Development mode - server path would be: {server_path}")
            print("📍 Server will not start in development mode")
        
        return server_path
    
    def is_server_running(self) -> bool:
        """Check if the server process is currently running."""
        # In development mode, always return False since we don't start the server
        if not getattr(sys, 'frozen', False):
            return False
            
        if self.server_process is None:
            return False
        
        # Check if process is still alive
        try:
            poll_result = self.server_process.poll()
            is_alive = poll_result is None
            
            # Debug information
            if hasattr(self, '_last_debug_time'):
                current_time = time.time()
                if current_time - self._last_debug_time > 5:  # Log every 5 seconds
                    print(f"📍 Server process check - PID: {self.server_process.pid}, Poll: {poll_result}, Alive: {is_alive}")
                    self._last_debug_time = current_time
            else:
                self._last_debug_time = time.time()
                print(f"📍 Server process check - PID: {self.server_process.pid}, Poll: {poll_result}, Alive: {is_alive}")
            
            return is_alive
        except Exception as e:
            print(f"❌ Error checking server process: {e}")
            return False
    
    def start_server(self) -> bool:
        """Start the futebol-server.exe process."""
        with self._startup_lock:
            if self.server_started and self.is_server_running():
                return True  # Already running
            
            # Check if we're running in development mode
            frozen = getattr(sys, 'frozen', False)
            print(f"🔍 Environment check - sys.frozen: {frozen}")
            
            if not frozen:
                print("🚫 Skipping server startup - running in development mode")
                print("📍 Server will only start when running as bundled executable")
                return True  # Return True to avoid errors, but don't actually start server
            
            print("🚀 Bundle mode detected - attempting server startup...")
            
            try:
                server_path = self.get_server_path()
                print(f"📍 Server path resolved: {server_path}")
                
                if not server_path.exists():
                    print(f"❌ Server executable not found at: {server_path}")
                    print(f"📍 Current working directory: {os.getcwd()}")
                    print(f"📍 sys._MEIPASS: {getattr(sys, '_MEIPASS', 'NOT_SET')}")
                    
                    # List contents of the directory containing the server path
                    server_dir = server_path.parent
                    if server_dir.exists():
                        print(f"📍 Server directory contents:")
                        try:
                            for item in server_dir.iterdir():
                                print(f"   - {item.name}")
                        except Exception as e:
                            print(f"   Error listing directory: {e}")
                    else:
                        print(f"📍 Server directory does not exist: {server_dir}")
                    
                    return False
                
                print(f"✅ Server executable found at: {server_path}")
                print(f"📍 Server size: {server_path.stat().st_size} bytes")
                print(f"🚀 Starting server from: {server_path}")
                
                # Start server process
                self.server_process = subprocess.Popen(
                    [str(server_path)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                
                print(f"📍 Server process PID: {self.server_process.pid}")
                print(f"📍 Server process created successfully")
                
                # Wait a moment to see if it starts successfully
                time.sleep(0.5)
                
                if self.is_server_running():
                    self.server_started = True
                    print("✅ Server started successfully")
                    print(f"📍 Server process status: {self.server_process.poll()}")
                    return True
                else:
                    print("❌ Server failed to start")
                    print(f"📍 Server process status: {self.server_process.poll()}")
                    print(f"📍 Server process return code: {self.server_process.returncode}")
                    self.server_process = None
                    return False
                    
            except Exception as e:
                print(f"❌ Error starting server: {e}")
                import traceback
                traceback.print_exc()
                self.server_process = None
                return False
    
    def stop_server(self) -> bool:
        """Stop the server process."""
        # In development mode, nothing to stop
        if not getattr(sys, 'frozen', False):
            print("🚫 No server to stop - running in development mode")
            return True
            
        if self.server_process is None:
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
            self.server_started = False
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
            
        if self.server_process:
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
