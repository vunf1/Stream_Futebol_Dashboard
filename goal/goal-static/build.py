import subprocess

pyinstaller_command = [
    "pyinstaller",
    "--clean",
    "--onefile",
    "--noconsole",
    "--icon", "assets/icons/icon_soft.ico",
    "goal_score.py"
]
try:
    subprocess.run(pyinstaller_command, check=True)
    print("Build completed successfully!")
except subprocess.CalledProcessError as e:
    print(f"Build failed: {e}")