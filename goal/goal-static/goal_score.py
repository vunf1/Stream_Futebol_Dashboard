import os
import customtkinter as ctk
import tkinter.messagebox
from typing import Optional

# Get the desktop path dynamically
desktop_path: str = os.path.join(os.path.expanduser("~"), "Desktop")
folder_path: str = os.path.join(desktop_path, "OBS_MARCADOR_FUTEBOL")

# Create the folder if it doesn't exist
os.makedirs(folder_path, exist_ok=True)

# Paths to the text files on the desktop
CasaFicheiro: str = os.path.join(folder_path, "golo casa.txt")
ForaFicheiro: str = os.path.join(folder_path, "golo fora.txt")

def read_number(file_path: str) -> int:
    try:
        with open(file_path, 'r') as file:
            return int(file.read().strip())
    except (FileNotFoundError, ValueError):
        write_number(file_path, 0)
        return 0

def write_number(file_path: str, number: int) -> None:
    with open(file_path, 'w') as file:
        file.write(str(number))

def update_label(file_path: str, label: ctk.CTkLabel, prefix: str) -> None:
    """
    Updates the label with the current number from the file.
    """
    current_number = read_number(file_path)
    label.configure(text=f"{prefix}{current_number}")

def change_number(file_path: str, label: ctk.CTkLabel, prefix: str, delta: int) -> None:
    """
    Changes the number in a file by a given delta and updates the label.
    """
    current_number = read_number(file_path) + delta
    current_number = max(current_number, 0)
    write_number(file_path, current_number)
    update_label(file_path, label, prefix)

def reset_numbers(casa: str, fora: str) -> None:
    """
    Resets the numbers in all files to zero and updates the labels.

    Args:
        casa (str): The prefix text for the home label.
        fora (str): The prefix text for the away label.
    """
    write_number(CasaFicheiro, 0)
    write_number(ForaFicheiro, 0)
    casa_label.configure(text=f"{casa}0")
    fora_label.configure(text=f"{fora}0")

def confirm_reset(casa: str, fora: str) -> None:
    """
    Asks for confirmation to reset the numbers and resets them if confirmed.
    """
    if tkinter.messagebox.askokcancel("Zerar", "Zerar Marcador?"):
        reset_numbers(casa, fora)

def toggle_decrement_buttons() -> None:
    """
    Toggles the state of the decrement buttons between enabled and disabled.
    """
    global decrement_buttons_enabled
    decrement_buttons_enabled = not decrement_buttons_enabled
    state = "normal" if decrement_buttons_enabled else "disabled"
    decrement_casa_button.configure(state=state)
    decrement_fora_button.configure(state=state)

# Create the main window
root: ctk.CTk = ctk.CTk()
root.title("Score - One game")
root.geometry("210x240")
root.minsize(190, 195)

# Icons and labels text
minusIcon: str = '\u268A'
warnIcon: str = "\u267B"
ballIcon: str = "\u26BD"
casa_text: str = "Casa:  "
fora_text: str = "Fora:  "

# Create a frame to hold the labels
labels_frame: ctk.CTkFrame = ctk.CTkFrame(root)
labels_frame.pack(padx=10, pady=10)

# Create labels to display the current numbers
casa_label: ctk.CTkLabel = ctk.CTkLabel(labels_frame, text=f"{casa_text}{read_number(CasaFicheiro)}", font=("Helvetica", 16))
casa_label.pack(side="left", padx=10)

fora_label: ctk.CTkLabel = ctk.CTkLabel(labels_frame, text=f"{fora_text}{read_number(ForaFicheiro)}", font=("Helvetica", 16))
fora_label.pack(side="left", padx=10)

# Create frames for buttons
casa_frame: ctk.CTkFrame = ctk.CTkFrame(root)
casa_frame.pack(padx=5, pady=5)

fora_frame: ctk.CTkFrame = ctk.CTkFrame(root)
fora_frame.pack(padx=5, pady=5)

# Create increment and decrement buttons for casa and fora
increment_casa_button: ctk.CTkButton = ctk.CTkButton(casa_frame, text=f"{ballIcon} Casa", command=lambda: change_number(CasaFicheiro, casa_label, casa_text, 1), fg_color="green")
increment_casa_button.pack(side="left", padx=5, pady=5)

decrement_casa_button: ctk.CTkButton = ctk.CTkButton(casa_frame, text=f"{minusIcon} 1", command=lambda: change_number(CasaFicheiro, casa_label, casa_text, -1), fg_color="red")
decrement_casa_button.pack(side="left", padx=5, pady=5)

increment_fora_button: ctk.CTkButton = ctk.CTkButton(fora_frame, text=f"{ballIcon} Fora", command=lambda: change_number(ForaFicheiro, fora_label, fora_text, 1), fg_color="green")
increment_fora_button.pack(side="left", padx=5, pady=5)

decrement_fora_button: ctk.CTkButton = ctk.CTkButton(fora_frame, text=f"{minusIcon} 1", command=lambda: change_number(ForaFicheiro, fora_label, fora_text, -1), fg_color="red")
decrement_fora_button.pack(side="left", padx=5, pady=5)

# Create toggle button for enabling/disabling decrement buttons
decrement_buttons_enabled: bool = True
toggle_frame: ctk.CTkFrame = ctk.CTkFrame(root)
toggle_frame.pack(padx=5, pady=5)
toggle_decrement_button: ctk.CTkButton = ctk.CTkButton(toggle_frame, text="Block", command=toggle_decrement_buttons, fg_color="orange")
toggle_decrement_button.pack(padx=2, pady=2, fill='both', expand=True)

# Create button to reset numbers to zero
reset_button: ctk.CTkButton = ctk.CTkButton(root, text=f"{warnIcon}  Zerar?", command=lambda: confirm_reset(casa_text, fora_text), fg_color="blue")
reset_button.pack(padx=10, pady=10)

# Run the main loop
root.mainloop()