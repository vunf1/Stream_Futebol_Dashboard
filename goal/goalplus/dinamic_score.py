import os
from tkinter import PhotoImage, simpledialog, Canvas, Scrollbar, Frame
import customtkinter as ctk
import tkinter.messagebox

# Function to read the current number from a file
def read_number(file_path):
    try:
        with open(file_path, 'r') as file:
            return int(file.read().strip())
    except FileNotFoundError:
        with open(file_path, 'w') as file:
            file.write('0')
        return 0
    except ValueError:
        return 0

# Function to write a number to a file
def write_number(file_path, number):
    with open(file_path, 'w') as file:
        file.write(str(number))

# Function to increment the number in a file
def increment_number(file_path, label, side):
    current_number = read_number(file_path)
    current_number += 1
    write_number(file_path, current_number)
    label.configure(text=f"{side}   {current_number}")

# Function to decrement the number in a file
def decrement_number(file_path, label, side):
    current_number = read_number(file_path)
    if current_number > 0:
        current_number -= 1
    else:
        current_number = 0

    write_number(file_path, current_number)
    label.configure(text=f"{side}   {current_number}")

# Function to reset the numbers in all files to zero
def reset_numbers(casa_label, fora_label, casa, fora, cPath, fPath):
    write_number(cPath, 0)
    write_number(fPath, 0)
    casa_label.configure(text=f"Casa:  0", font=("Helvetica", 16))
    fora_label.configure(text=f"Fora:  0", font=("Helvetica", 16))

# Function to confirm and reset numbers
def confirm_reset(casa_label, fora_label, casa, fora, cPath, fPath):
    response = tkinter.messagebox.askokcancel("Zerar", "Zerar Marcador?")
    if response:
        reset_numbers(casa_label, fora_label, casa, fora, cPath, fPath)

# Function to toggle the state of the decrement buttons
def toggle_decrement_buttons(decrement_buttons):
    global decrement_buttons_enabled
    decrement_buttons_enabled = not decrement_buttons_enabled
    state = "normal" if decrement_buttons_enabled else "disabled"
    for button in decrement_buttons:
        button.configure(state=state)

# Function to scroll with the mouse wheel
def on_mouse_wheel(event):
    canvas.yview_scroll(int(-1*(event.delta/120)), "units")

# Create the main window
root = ctk.CTk()
root.title("Score - Multiple Games")
root.geometry("500x500")

# Ask for the number of stadiums
num_stadiums = simpledialog.askinteger("Number of Stadiums", "How many stadiums?")

desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
folders_path = os.path.join(desktop_path, "OBS_MARCADOR_FUTEBOL")

# Create the folder if it doesn't exist
if not os.path.exists(folders_path):
    os.makedirs(folders_path)

# Create the main frame and canvas with scrollbar
main_frame = Frame(root, bg="black")
main_frame.pack(fill="both", expand=True)

canvas = Canvas(main_frame, bg="black")
scrollbar = Scrollbar(main_frame, orient="vertical", command=canvas.yview)
scrollable_frame = Frame(canvas, bg="black")

scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(
        scrollregion=canvas.bbox("all")
    )
)

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

def center_scrollable_frame():
    canvas.update_idletasks()  # Ensure the canvas size is updated
    canvas_width = canvas.winfo_width()
    canvas_height = canvas.winfo_height()
    scrollable_frame_width = scrollable_frame.winfo_width()
    scrollable_frame_height = scrollable_frame.winfo_height()
    x = (canvas_width - scrollable_frame_width) // 2
    y = (canvas_height - scrollable_frame_height) // 2
    canvas.coords(canvas_window, x, y)

canvas_window = canvas.create_window(0, 0, window=scrollable_frame, anchor="center")
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True)
# Bind mouse wheel to canvas scrolling
canvas.bind_all("<MouseWheel>", on_mouse_wheel)
scrollbar.pack(side="right", fill="y")

# Generate the same content for each stadium
minusIcon = '\u268A'
warnIcon = "\u267B"
ballIcon = '\u26BD'

decrement_buttons = []
# Create toggle button for enabling/disabling decrement buttons
decrement_buttons_enabled = True
toggle_decrement_button = ctk.CTkButton(scrollable_frame, text="Block", command=lambda: toggle_decrement_buttons(decrement_buttons), fg_color="orange", width=3, height=3)
toggle_decrement_button.grid(row=0, column=0, columnspan=2, padx=2, pady=2, sticky="ew")

row = 1
column = 0

for i in range(num_stadiums):
    fol_path = os.path.join(folders_path, f"Stadium {i+1}")
    # Create the folder if it doesn't exist
    if not os.path.exists(fol_path):
        os.makedirs(fol_path)
    # Paths to the text files on the desktop for each stadium
    CasaFicheiro = os.path.join(fol_path, f"golo casa.txt")
    ForaFicheiro = os.path.join(fol_path, f"golo fora.txt")

    stadium_frame = ctk.CTkFrame(scrollable_frame, fg_color="black")
    stadium_frame.grid(row=row, column=column, padx=10, pady=10, sticky="nsew")

    title_frame = ctk.CTkFrame(stadium_frame, fg_color="black")
    title_frame.pack(padx=0, pady=0)
    # Create a frame to hold the labels for each stadium
    labels_frame = ctk.CTkFrame(stadium_frame, fg_color="black")
    labels_frame.pack(padx=10, pady=10)

    casa_text = f"Casa:  {read_number(CasaFicheiro)}"
    fora_text = f"Fora:  {read_number(ForaFicheiro)}"

    # Create labels to display the current numbers for each stadium
    casa_label = ctk.CTkLabel(title_frame, text=f"Campo {i+1}", font=("Helvetica", 16), fg_color="black")
    casa_label.pack(side="left", padx=0)

    # Create labels to display the current numbers for each stadium
    casa_label = ctk.CTkLabel(labels_frame, text=casa_text, font=("Helvetica", 16), fg_color="black")
    casa_label.pack(side="left", padx=10)

    fora_label = ctk.CTkLabel(labels_frame, text=fora_text, font=("Helvetica", 16), fg_color="black")
    fora_label.pack(side="left", padx=10)

    # Create frames for buttons for each stadium
    casa_frame = ctk.CTkFrame(stadium_frame, fg_color="black")
    casa_frame.pack(padx=5, pady=5)

    fora_frame = ctk.CTkFrame(stadium_frame, fg_color="black")
    fora_frame.pack(padx=5, pady=5)

    # Create buttons for casa
    increment_casa_button = ctk.CTkButton(casa_frame, text=f"{ballIcon} Casa", command=lambda f=CasaFicheiro, l=casa_label, t=casa_text: increment_number(f, l, t), fg_color="green", width=3, height=3)
    increment_casa_button.pack(side="left", padx=5, pady=5)

    decrement_casa_button = ctk.CTkButton(casa_frame, text=f"{minusIcon} 1", command=lambda f=CasaFicheiro, l=casa_label, t=casa_text: decrement_number(f, l, t), fg_color="red", width=3, height=3)
    decrement_casa_button.pack(side="left", padx=5, pady=5)
    decrement_buttons.append(decrement_casa_button)

    # Create buttons for fora
    increment_fora_button = ctk.CTkButton(fora_frame, text=f"{ballIcon} Fora", command=lambda f=ForaFicheiro, l=fora_label, t=fora_text: increment_number(f, l, t), fg_color="green", width=3, height=3)
    increment_fora_button.pack(side="left", padx=5, pady=5)

    decrement_fora_button = ctk.CTkButton(fora_frame, text=f"{minusIcon} 1", command=lambda f=ForaFicheiro, l=fora_label, t=fora_text: decrement_number(f, l, t), fg_color="red", width=3, height=3)
    decrement_fora_button.pack(side="left", padx=5, pady=5)
    decrement_buttons.append(decrement_fora_button)

    # Create button to reset numbers to zero for each stadium
    reset_button = ctk.CTkButton(stadium_frame, text=f"{warnIcon}  Zerar?", command=lambda l1=casa_label, l2=fora_label, t1=casa_text, t2=fora_text: confirm_reset(l1, l2, t1, t2, CasaFicheiro, ForaFicheiro), fg_color="blue")
    reset_button.pack(padx=10, pady=10)

    # Update row and column for next stadium
    column += 1
    if column > 1:
        column = 0
        row += 1

root.bind("<Configure>", lambda e: center_scrollable_frame())

# Run the main loop
root.mainloop()
