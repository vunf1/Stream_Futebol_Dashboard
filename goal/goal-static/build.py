import subprocess

# Install dependencies
subprocess.run(["python", "-m", "pip", "install", "-r", "requirements.txt"])

pyinstaller_command = [
    "python", "-m", "PyInstaller",
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
    print("Build completed successfully!")
except subprocess.CalledProcessError as e:
    print(f"Build failed: {e}")
