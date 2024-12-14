
import os
import customtkinter as ctk
import tkinter.messagebox
import obswebsocket
from obswebsocket import obsws, requests
from PIL import Image, ImageTk
import pystray
from pystray import MenuItem as item
import threading
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access environment variables
obs_host = os.getenv('OBS_HOST')
obs_port = os.getenv('OBS_PORT')
obs_password = os.getenv('OBS_PASSWORD')

# Get the desktop path dynamically
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
folder_path = os.path.join(desktop_path, "OBS_MARCADOR_FUTEBOL")

# Create the folder if it doesn't exist
if not os.path.exists(folder_path):
    os.makedirs(folder_path)

# Paths to the text files 
casa_ficheiro_path = os.path.join(folder_path, "golo casa.txt")
fora_ficheiro_path = os.path.join(folder_path, "golo fora.txt")
introinfo_ficheiro_path = os.path.join(folder_path, "intro info.txt")
icon_ficheiro_path = os.path.join(folder_path, "icon_soft.ico")

# List of file paths to check and create if they don't exist
file_paths = [casa_ficheiro_path, fora_ficheiro_path, introinfo_ficheiro_path, icon_ficheiro_path]

for file_path in file_paths:
    if not os.path.exists(file_path):
        with open(file_path, 'w') as file:
            pass  # Just create an empty file by writting 

# Check if the icon file exists and is a valid image
def is_valid_image(file_path):
    try:
        with Image.open(file_path) as img:
            img.verify()
        return True
    except (IOError, SyntaxError):
        return False

# Provide a default icon path
default_icon_path = os.path.join(folder_path, "default_icon.ico")

# Ensure the default icon file exists
if not os.path.exists(default_icon_path):
    # Create a simple default icon image
    default_icon_image = Image.new('RGB', (32, 32), color='gray')
    default_icon_image.save(default_icon_path)

# Use the provided icon if it's valid, otherwise use the default icon
icon_path = icon_ficheiro_path if is_valid_image(icon_ficheiro_path) else default_icon_path

# Connect to OBS WebSocket
def connect_obs():
    global ws
    try:
        ws = obsws(obs_host, obs_port, obs_password)
        ws.connect()
    except obswebsocket.exceptions.ConnectionFailure as e:
        tkinter.messagebox.showerror("OBS Connection Error", f"Could not connect to OBS WebSocket: {e}")

# Function to open Multiview in windowed mode
def open_multiview():
    try:
        ws.call(requests.OpenProjector(type='Multiview', monitor=-1))
        #tkinter.messagebox.showinfo("Multiview", "Multiview opened in windowed mode.")
    except Exception as e:
        tkinter.messagebox.showerror("Error", f"Failed to open Multiview: {e}")
        
# Function to read the current number from a file
def read_from_file(file_path):
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
def write_to_file(file_path, number):
    with open(file_path, 'w') as file:
        file.write(str(number))

# Function to increment the number in a file
def increment_number(file_path, label,side):
    current_number = read_from_file(file_path)
    current_number += 1
    write_to_file(file_path, current_number)
    label.configure(text=side+str(current_number))

# Function to decrement the number in a file
def decrement_number(file_path, label,side):
    current_number = read_from_file(file_path)
    if current_number > 0:
        current_number -= 1
        write_to_file(file_path, current_number)
    label.configure(text=side+str(current_number))

# Function to reset the numbers in all files to zero
def reset_numbers_to_zero(casa,fora):
    write_to_file(casa_ficheiro_path, 0)
    write_to_file(fora_ficheiro_path, 0)
    casa_label.configure(text=f"{casa}0", font=("Helvetica", 16))
    fora_label.configure(text=f"{fora}0", font=("Helvetica", 16))

# Function to confirm and reset numbers
def confirm_reset(casa, fora):
    response = tkinter.messagebox.askokcancel("Zerar", "Zerar Marcador?")
    if response:
        reset_numbers_to_zero(casa, fora)

# Function to toggle the state of the decrement buttons
def toggle_decrement_buttons():
    global decrement_buttons_status
    decrement_buttons_status = not decrement_buttons_status
    state = "normal" if decrement_buttons_status else "disabled"
    decrement_casa_button.configure(state=state)
    decrement_fora_button.configure(state=state)

# Create the main window
root = ctk.CTk()
root.title("Score - One game")
root.geometry("210x240")
root.minsize(190, 240)  # Set minimum size
#root.overrideredirect(True)  # Remove window top bar, involve create a new one from strach even the move window event is needed
root.attributes("-topmost", True)  # Keep window on top
minusIcon = '\u268A'
warnIcon = '\u267B'
ballIcon = '\u26BD'
decrement_buttons_status = True
# Set the window icon
window_icon = ImageTk.PhotoImage(file=icon_path)
root.iconphoto(True, window_icon)
def on_quit(icon, item):
    icon.stop()
    root.quit()
    # Create the taskbar icon

def setup_tray_icon():
    image = Image.open(icon_ficheiro_path)
    menu = (item('Quit', on_quit),)
    icon = pystray.Icon("name", image, "Title", menu)
    icon.run()

def start_tray_icon():
    # Run the taskbar icon in a separate thread
    thread = threading.Thread(target=setup_tray_icon, daemon=True)
    thread.start()
connect_obs()
start_tray_icon()

# Create a frame to hold the labels
labels_frame = ctk.CTkFrame(root)
labels_frame.pack(padx=10, pady=10)
casa_text= "Casa:  " 
button_frame = ctk.CTkFrame(root)
button_frame.pack(padx=10, pady=10, fill="x")

# Create the "Block" button
toggle_decrement_button = ctk.CTkButton(button_frame, text="Block", command=toggle_decrement_buttons, fg_color="orange")
toggle_decrement_button.pack(side="left", padx=5, pady=5)

# Create the "View Multiview" button
multiview_button = ctk.CTkButton(button_frame, text="View Multiview", command=open_multiview, fg_color="purple")
multiview_button.pack(side="left", padx=5, pady=5)
fora_text= "Fora:  "
# Create labels to display the current numbers
casa_label = ctk.CTkLabel(labels_frame, text=casa_text+str(read_from_file(casa_ficheiro_path)), font=("Helvetica", 16))
casa_label.pack(side="left", padx=10)

fora_label = ctk.CTkLabel(labels_frame, text=fora_text + str(read_from_file(fora_ficheiro_path)), font=("Helvetica", 16))
fora_label.pack(side="left", padx=10)

# Create frames for buttons
casa_frame = ctk.CTkFrame(root)
casa_frame.pack(padx=5, pady=5)

fora_frame = ctk.CTkFrame(root)
fora_frame.pack(padx=5, pady=5)


# Create buttons for casa
increment_casa_button = ctk.CTkButton(casa_frame, text=f"{ballIcon} Casa", command=lambda: increment_number(casa_ficheiro_path, casa_label,casa_text), fg_color="green")
increment_casa_button.pack(side="left", padx=5, pady=5)

decrement_casa_button = ctk.CTkButton(casa_frame, text=f"{minusIcon} 1", command=lambda: decrement_number(casa_ficheiro_path, casa_label, casa_text), fg_color="red")
decrement_casa_button.pack(side="left", padx=5, pady=5)
# Create toggle button for enabling/disabling decrement buttons
decrement_buttons_status = True
# Create buttons for file2
increment_fora_button = ctk.CTkButton(fora_frame, text=f"{ballIcon} Fora", command=lambda: increment_number(fora_ficheiro_path, fora_label, fora_text), fg_color="green")
increment_fora_button.pack(side="left", padx=5, pady=5)

decrement_fora_button = ctk.CTkButton(fora_frame, text=f"{minusIcon} 1", command=lambda: decrement_number(fora_ficheiro_path, fora_label, fora_text), fg_color="red")
decrement_fora_button.pack(side="left", padx=5, pady=5)

# Create button to reset numbers to zero
reset_button = ctk.CTkButton(root, text=f"{warnIcon}  Zerar?", command=lambda:confirm_reset(casa_text,fora_text), fg_color="blue")
reset_button.pack(padx=10, pady=10)

# Create a new frame for the additional buttons
additional_buttons_frame = ctk.CTkFrame(root)
additional_buttons_frame.pack(padx=10, pady=10, fill="x")

# Create new buttons below the reset button, using grid for equal sizing
button_width = 18
button_height = 3

parte1 = ctk.CTkButton(additional_buttons_frame, text="P. 1", command=lambda: write_to_file(introinfo_ficheiro_path, "PARTE 1"), fg_color="blue", width=button_width, height=button_height)
parte1.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

parte2 = ctk.CTkButton(additional_buttons_frame, text="P. 2", command=lambda: write_to_file(introinfo_ficheiro_path, "PARTE 2"), fg_color="blue", width=button_width, height=button_height)
parte2.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

vazio_intro = ctk.CTkButton(additional_buttons_frame, text="vazio", command=lambda: write_to_file(introinfo_ficheiro_path,""), fg_color="blue", width=button_width, height=button_height)
vazio_intro.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

# Ensure the buttons fill the frame equally
additional_buttons_frame.grid_columnconfigure(0, weight=1)
additional_buttons_frame.grid_columnconfigure(1, weight=1)
additional_buttons_frame.grid_columnconfigure(2, weight=1)
# Create a frame to hold the "Block" and "View Multiview" buttons

root.mainloop()
