#!/usr/bin/env python3
"""
Commercial License Agreement Generator
Generates legally binding Commercial License Agreements following Portuguese law.

Author: João Maia
Email: epg.joaomaia@gmail.com
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date
import json
from typing import Dict, Any
from PIL import Image, ImageTk
import os
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

# Modern UI Constants
WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 900
DEFAULT_LICENSE_DURATION = 12
DEFAULT_MAX_USERS = 1
DEFAULT_MAX_INSTANCES = 1
DEFAULT_PAYMENT_TERMS = 30

# Modern Color Scheme
COLORS = {
    'primary': '#2563eb',      # Blue
    'secondary': '#64748b',    # Slate
    'success': '#059669',      # Green
    'warning': '#d97706',      # Amber
    'error': '#dc2626',        # Red
    'background': '#f8fafc',   # Light gray
    'surface': '#ffffff',      # White
    'border': '#e2e8f0',      # Light border
    'text': '#1e293b',        # Dark text
    'text_secondary': '#64748b'  # Secondary text
}

# Modern Styles
STYLES = {
    'title': ('Segoe UI', 23, 'bold'),
    'heading': ('Segoe UI', 12, 'bold'),
    'subheading': ('Segoe UI', 11, 'bold'),
    'body': ('Segoe UI', 9),
    'button': ('Segoe UI', 10, 'bold'),
    'label': ('Segoe UI', 9)
}


class ModernButton(tk.Button):
    """Custom modern button with hover effects"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(
            relief='flat',
            borderwidth=0,
            font=STYLES['button'],
            bg=COLORS['primary'],
            fg='white',
            activebackground=COLORS['primary'],
            activeforeground='white',
            cursor='hand2',
            padx=20,
            pady=8
        )
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)
    
    def on_enter(self, e):
        self.configure(bg='#1d4ed8')
    
    def on_leave(self, e):
        self.configure(bg=COLORS['primary'])


class ModernEntry(ttk.Entry):
    """Custom modern entry with better styling"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(
            font=STYLES['body'],
            style='Modern.TEntry'
        )


class ModernText(tk.Text):
    """Custom modern text widget with better styling"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(
            font=STYLES['body'],
            bg=COLORS['surface'],
            fg=COLORS['text'],
            relief='flat',
            borderwidth=1,
            selectbackground=COLORS['primary'],
            selectforeground='white'
        )


class CommercialLicenseGenerator:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Commercial License Agreement Generator")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.configure(bg=COLORS['background'])
        
        # Initialize form field attributes
        self.licensor_name: Any = None
        self.licensor_email: Any = None
        self.licensor_address: Any = None
        self.licensor_nif: Any = None
        self.licensor_phone: Any = None
        self.software_name: Any = None
        self.software_version: Any = None
        self.software_description: Any = None
        self.licensee_company: Any = None
        self.licensee_contact: Any = None
        self.licensee_email: Any = None
        self.licensee_address: Any = None
        self.licensee_nif: Any = None
        self.licensee_phone: Any = None
        self.licensee_website: Any = None
        self.contract_start_date: Any = None
        self.license_duration: Any = None
        self.max_users: Any = None
        self.max_instances: Any = None
        self.setup_fee: Any = None
        self.annual_fee: Any = None
        self.royalty_percentage: Any = None
        self.payment_schedule: Any = None
        self.payment_terms: Any = None
        self.currency: Any = None
        self.allow_modifications: Any = None
        self.allow_distribution: Any = None
        self.allow_sublicensing: Any = None
        self.licensor_logo_path: str = ""
        
        # Configure modern styles
        self.setup_styles()
        
        # Center window on screen
        self.center_window()
        
        self.setup_ui()
        self.load_defaults()
        
    def setup_styles(self):
        """Setup modern ttk styles"""
        style = ttk.Style()
        
        # Configure modern frame style
        style.configure('Modern.TFrame', background=COLORS['surface'])
        
        # Configure modern label styles
        style.configure('Title.TLabel', 
                       font=STYLES['title'], 
                       foreground=COLORS['text'],
                       background=COLORS['background'])
        
        style.configure('Heading.TLabel', 
                       font=STYLES['heading'], 
                       foreground=COLORS['text'],
                       background=COLORS['surface'])
        
        style.configure('Subheading.TLabel', 
                       font=STYLES['subheading'], 
                       foreground=COLORS['text'],
                       background=COLORS['surface'])
        
        style.configure('Body.TLabel', 
                       font=STYLES['body'], 
                       foreground=COLORS['text_secondary'],
                       background=COLORS['surface'])
        
        # Configure modern entry style
        style.configure('Modern.TEntry', 
                       fieldbackground=COLORS['surface'],
                       borderwidth=1,
                       relief='flat')
        
        # Configure modern notebook style
        style.configure('Modern.TNotebook', 
                       background=COLORS['background'],
                       borderwidth=0)
        
        style.configure('Modern.TNotebook.Tab', 
                       padding=[20, 10],
                       font=STYLES['body'])
        
        # Configure modern button style
        style.configure('Modern.TButton', 
                       font=STYLES['button'],
                       padding=[20, 10])
        
    def center_window(self):
        """Center the window on the screen"""
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (WINDOW_WIDTH // 2)
        y = (self.root.winfo_screenheight() // 2) - (WINDOW_HEIGHT // 2)
        self.root.geometry(f'{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}')
        
    def setup_ui(self):
        """Setup the main user interface"""
        # Main container with padding
        main_container = tk.Frame(self.root, bg=COLORS['background'])
        main_container.pack(fill='both', expand=True, padx=30, pady=30)
        
        # Action buttons section
        self.create_action_buttons(main_container)
        # Header section
        self.create_header(main_container)
        
        # Create notebook for tabs with modern styling
        self.notebook = ttk.Notebook(main_container, style='Modern.TNotebook')
        self.notebook.pack(fill='both', expand=True, pady=(20, 0))
        
        # Create tabs
        self.create_licensor_tab(self.notebook)
        self.create_licensee_tab(self.notebook)
        self.create_terms_tab(self.notebook)
        self.create_pricing_tab(self.notebook)
        self.create_preview_tab(self.notebook)
        
        # Bind scroll wheel to notebook
        self.notebook.bind('<MouseWheel>', self.on_mousewheel)
        self.notebook.bind('<Button-4>', self.on_mousewheel)  # Linux scroll up
        self.notebook.bind('<Button-5>', self.on_mousewheel)  # Linux scroll down
        
         
    def on_mousewheel(self, event):
        """Handle mouse wheel scrolling for tab navigation"""
        try:
            current_tab = self.notebook.index(self.notebook.select())
            total_tabs = self.notebook.index('end')
            
            # Determine scroll direction
            if event.num == 4 or event.delta > 0:  # Scroll up
                new_tab = (current_tab - 1) % total_tabs
            elif event.num == 5 or event.delta < 0:  # Scroll down
                new_tab = (current_tab + 1) % total_tabs
            else:
                return
            
            # Switch to the new tab
            self.notebook.select(new_tab)
        except Exception:
            pass  # Ignore any errors in scroll handling
        
    def on_text_scroll(self, event):
        """Handle mouse wheel scrolling for text widgets"""
        try:
            # Determine scroll direction and amount
            if event.num == 4 or event.delta > 0:  # Scroll up
                self.preview_text.yview_scroll(-1, "units")
            elif event.num == 5 or event.delta < 0:  # Scroll down
                self.preview_text.yview_scroll(1, "units")
        except Exception:
            pass  # Ignore any errors in scroll handling
         
    def create_header(self, parent):
        """Create modern header section"""
        header_frame = tk.Frame(parent, bg=COLORS['background'])
        header_frame.pack(fill='x', pady=(0, 20))
        
        # Main title
        title_label = tk.Label(
            header_frame,
            text="Commercial License Agreement Generator",
            font=STYLES['title'],
            fg=COLORS['text'],
            bg=COLORS['background']
        )
        title_label.pack()
        
        # Subtitle
        subtitle_label = tk.Label(
            header_frame,
            text="Generate legally binding commercial license agreements following Portuguese law",
            font=STYLES['body'],
            fg=COLORS['text_secondary'],
            bg=COLORS['background']
        )
        subtitle_label.pack(pady=(5, 0))
        
    def create_action_buttons(self, parent):
        """Create modern action buttons section"""
        button_frame = tk.Frame(parent, bg=COLORS['background'])
        button_frame.pack(fill='x', pady=(20, 0))
        
        # Generate button
        generate_btn = ModernButton(
            button_frame,
            text="Generate License Agreement",
            command=self.generate_agreement
        )
        generate_btn.pack(side='right')
        
        # Preview button
        preview_btn = ModernButton(
            button_frame,
            text="Refresh Preview",
            command=self.update_preview,
            bg=COLORS['secondary']
        )
        preview_btn.pack(side='right', padx=(0, 10))
        
    def create_licensor_tab(self, notebook):
        """Create the licensor information tab"""
        frame = tk.Frame(notebook, bg=COLORS['surface'], padx=30, pady=30)
        notebook.add(frame, text="Licensor Information")
        
        # Section title
        self.create_section_title(frame, "Licensor (Software Owner) Information", 0)
        
        # Form fields
        self.create_form_field(frame, "Full Name:", "licensor_name", 1, width=50)
        self.create_form_field(frame, "Email:", "licensor_email", 2, width=50)
        self.create_form_field(frame, "Address:", "licensor_address", 3, width=50, height=3, is_text=True)
        self.create_form_field(frame, "NIF (Tax Number):", "licensor_nif", 4, width=50)
        self.create_form_field(frame, "Phone:", "licensor_phone", 5, width=50)
        
        # Modern logo section
        self.create_modern_logo_section(frame)
        
        # Software section
        self.create_section_title(frame, "Software Information", 6)
        self.create_form_field(frame, "Software Name:", "software_name", 7, width=50)
        self.create_form_field(frame, "Software Version:", "software_version", 8, width=50)
        self.create_form_field(frame, "Software Description:", "software_description", 9, width=50, height=4, is_text=True)
        
    def create_licensee_tab(self, notebook):
        """Create the licensee information tab"""
        frame = tk.Frame(notebook, bg=COLORS['surface'], padx=30, pady=30)
        notebook.add(frame, text="Licensee Information")
        
        # Section title
        self.create_section_title(frame, "Licensee (Client) Information", 0)
        
        # Form fields
        self.create_form_field(frame, "Company/Organization:", "licensee_company", 1, width=50)
        self.create_form_field(frame, "Contact Person:", "licensee_contact", 2, width=50)
        self.create_form_field(frame, "Email:", "licensee_email", 3, width=50)
        self.create_form_field(frame, "Address:", "licensee_address", 4, width=50, height=3, is_text=True)
        self.create_form_field(frame, "NIF (Tax Number):", "licensee_nif", 5, width=50)
        self.create_form_field(frame, "Phone:", "licensee_phone", 6, width=50)
        self.create_form_field(frame, "Website:", "licensee_website", 7, width=50)
        
    def create_terms_tab(self, notebook):
        """Create the license terms tab"""
        frame = tk.Frame(notebook, bg=COLORS['surface'], padx=30, pady=30)
        notebook.add(frame, text="License Terms")
        
        # License type section
        self.create_section_title(frame, "License Type", 0)
        
        # License type display
        license_frame = tk.Frame(frame, bg=COLORS['surface'])
        license_frame.grid(row=1, column=0, columnspan=2, sticky='w', pady=(0, 20))
        
        tk.Label(
            license_frame,
            text="Commercial License",
            font=STYLES['subheading'],
            fg=COLORS['success'],
            bg=COLORS['surface']
        ).pack(anchor='w')
        
        tk.Label(
            license_frame,
            text="(Only Commercial License available)",
            font=STYLES['body'],
            fg=COLORS['text_secondary'],
            bg=COLORS['surface']
        ).pack(anchor='w')
        
        # Contract start date
        self.create_section_title(frame, "Contract Start Date", 2)
        self.create_form_field(frame, "Start Date (DD/MM/YYYY):", "contract_start_date", 3, width=20)
        
        # License duration
        self.create_section_title(frame, "License Duration", 4)
        self.create_form_field(frame, "Duration (months):", "license_duration", 5, width=20, is_spinbox=True, from_=1, to=120)
        
        # Usage restrictions
        self.create_section_title(frame, "Usage Restrictions", 6)
        
        # Checkboxes in a frame
        checkbox_frame = tk.Frame(frame, bg=COLORS['surface'])
        checkbox_frame.grid(row=7, column=0, columnspan=2, sticky='w', pady=(0, 20))
        
        self.allow_modifications = tk.BooleanVar(value=False)
        self.allow_distribution = tk.BooleanVar(value=False)
        self.allow_sublicensing = tk.BooleanVar(value=False)
        
        tk.Checkbutton(
            checkbox_frame,
            text="Allow code modifications",
            variable=self.allow_modifications,
            font=STYLES['body'],
            fg=COLORS['text'],
            bg=COLORS['surface'],
            selectcolor=COLORS['primary'],
            activebackground=COLORS['surface'],
            activeforeground=COLORS['text']
        ).pack(anchor='w', pady=2)
        
        tk.Checkbutton(
            checkbox_frame,
            text="Allow distribution/resale",
            variable=self.allow_distribution,
            font=STYLES['body'],
            fg=COLORS['text'],
            bg=COLORS['surface'],
            selectcolor=COLORS['primary'],
            activebackground=COLORS['surface'],
            activeforeground=COLORS['text']
        ).pack(anchor='w', pady=2)
        
        tk.Checkbutton(
            checkbox_frame,
            text="Allow sublicensing",
            variable=self.allow_sublicensing,
            font=STYLES['body'],
            fg=COLORS['text'],
            bg=COLORS['surface'],
            selectcolor=COLORS['primary'],
            activebackground=COLORS['surface'],
            activeforeground=COLORS['text']
        ).pack(anchor='w', pady=2)
        
        # Usage limits
        self.create_section_title(frame, "Usage Limits", 8)
        self.create_form_field(frame, "Max number of users:", "max_users", 9, width=20, is_spinbox=True, from_=1, to=10000)
        self.create_form_field(frame, "Max number of instances:", "max_instances", 10, width=20, is_spinbox=True, from_=1, to=1000)
        
    def create_pricing_tab(self, notebook):
        """Create the pricing tab"""
        frame = tk.Frame(notebook, bg=COLORS['surface'], padx=30, pady=30)
        notebook.add(frame, text="Pricing & Payment")
        
        # Pricing structure
        self.create_section_title(frame, "Pricing Structure", 0)
        self.create_form_field(frame, "Setup Fee (€):", "setup_fee", 1, width=20)
        self.create_form_field(frame, "Annual License Fee (€):", "annual_fee", 2, width=20)
        self.create_form_field(frame, "Royalty Percentage (%):", "royalty_percentage", 3, width=20)
        
        # Payment terms
        self.create_section_title(frame, "Payment Terms", 4)
        
        # Payment schedule dropdown
        tk.Label(
            frame,
            text="Payment Schedule:",
            font=STYLES['body'],
            fg=COLORS['text'],
            bg=COLORS['surface']
        ).grid(row=5, column=0, sticky='w', pady=2)
        
        self.payment_schedule = ttk.Combobox(
            frame,
            values=["Monthly", "Quarterly", "Annually", "One-time"],
            width=20,
            font=STYLES['body']
        )
        self.payment_schedule.grid(row=5, column=1, sticky='w', padx=(20, 0), pady=2)
        self.payment_schedule.set("Annually")
        
        self.create_form_field(frame, "Payment Terms (days):", "payment_terms", 6, width=20, is_spinbox=True, from_=0, to=90)
        
        # Currency
        tk.Label(
            frame,
            text="Currency:",
            font=STYLES['body'],
            fg=COLORS['text'],
            bg=COLORS['surface']
        ).grid(row=7, column=0, sticky='w', pady=2)
        
        self.currency = ttk.Combobox(
            frame,
            values=["EUR", "USD", "GBP"],
            width=20,
            font=STYLES['body']
        )
        self.currency.grid(row=7, column=1, sticky='w', padx=(20, 0), pady=2)
        self.currency.set("EUR")
        
    def create_preview_tab(self, notebook):
        """Create the preview tab"""
        frame = tk.Frame(notebook, bg=COLORS['surface'], padx=30, pady=30)
        notebook.add(frame, text="Preview")
        
        # Preview title
        tk.Label(
            frame,
            text="License Agreement Preview",
            font=STYLES['heading'],
            fg=COLORS['text'],
            bg=COLORS['surface']
        ).pack(anchor='w', pady=(0, 20))
        
        # Create text widget with scrollbar
        text_container = tk.Frame(frame, bg=COLORS['surface'])
        text_container.pack(fill='both', expand=True)
        
        # Text widget
        self.preview_text = ModernText(
             text_container,
             height=20,
             width=80,
             wrap=tk.WORD
         )
        self.preview_text.pack(side='left', fill='both', expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(text_container, orient='vertical', command=self.preview_text.yview)
        scrollbar.pack(side='right', fill='y')
        self.preview_text.configure(yscrollcommand=scrollbar.set)
        
        # Bind scroll wheel to preview text
        self.preview_text.bind('<MouseWheel>', self.on_text_scroll)
        self.preview_text.bind('<Button-4>', self.on_text_scroll)  # Linux scroll up
        self.preview_text.bind('<Button-5>', self.on_text_scroll)  # Linux scroll down
        
    def create_section_title(self, parent, text, row):
        """Create a modern section title"""
        title_label = tk.Label(
            parent,
            text=text,
            font=STYLES['heading'],
            fg=COLORS['text'],
            bg=COLORS['surface']
        )
        title_label.grid(row=row, column=0, columnspan=2, sticky='w', pady=(20, 15))
        
    def create_form_field(self, parent, label_text, attr_name, row, width=40, height=1, is_text=False, is_spinbox=False, **spinbox_kwargs):
        """Create a modern form field with label and input"""
        # Label
        label = tk.Label(
            parent,
            text=label_text,
            font=STYLES['body'],
            fg=COLORS['text'],
            bg=COLORS['surface']
        )
        label.grid(row=row, column=0, sticky='w', pady=2)
        
        # Input field
        if is_text:
            widget = ModernText(parent, height=height, width=width)
        elif is_spinbox:
            widget = ttk.Spinbox(parent, width=width, **spinbox_kwargs)
        else:
            widget = ModernEntry(parent, width=width)
        
        widget.grid(row=row, column=1, sticky='w', padx=(20, 0), pady=2)
        
        # Store reference
        setattr(self, attr_name, widget)
        
    def create_modern_logo_section(self, parent):
        """Create modern logo upload section"""
        # Logo section title
        title_label = tk.Label(
            parent,
            text="Company Logo",
            font=STYLES['heading'],
            fg=COLORS['text'],
            bg=COLORS['surface']
        )
        title_label.grid(row=10, column=0, columnspan=2, sticky='w', pady=(20, 15))
        
        # Logo upload area
        upload_frame = tk.Frame(parent, bg=COLORS['surface'])
        upload_frame.grid(row=11, column=0, columnspan=2, sticky='w', pady=(0, 20))
        
        # Left side - upload controls
        controls_frame = tk.Frame(upload_frame, bg=COLORS['surface'])
        controls_frame.pack(side='left', fill='y')
        
        # Upload button
        upload_btn = ModernButton(
            controls_frame,
            text="📁 Upload Logo",
            command=self.upload_logo,
            bg=COLORS['primary']
        )
        upload_btn.pack(anchor='w', pady=(0, 10))
        
        # File info label
        self.logo_info_label = tk.Label(
            controls_frame,
            text="No logo selected",
            font=STYLES['body'],
            fg=COLORS['text_secondary'],
            bg=COLORS['surface']
        )
        self.logo_info_label.pack(anchor='w')
        
        # Right side - preview
        preview_frame = tk.Frame(upload_frame, bg=COLORS['surface'], width=120, height=80)
        preview_frame.pack(side='right', padx=(20, 0))
        preview_frame.pack_propagate(False)
        
        # Preview label
        self.logo_preview_label = tk.Label(
            preview_frame,
            text="No Logo",
            font=STYLES['body'],
            fg=COLORS['text_secondary'],
            bg=COLORS['surface'],
            relief='solid',
            borderwidth=1
        )
        self.logo_preview_label.pack(expand=True, fill='both', padx=5, pady=5)
        
    def upload_logo(self):
        """Upload logo file with modern interface"""
        filename = filedialog.askopenfilename(
            title="Select Company Logo",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("All files", "*.*")
            ]
        )
        if filename:
            try:
                # Store the logo path as a string
                self.licensor_logo_path = filename
                
                # Update file info
                file_name = os.path.basename(filename)
                self.logo_info_label.config(text=f"Selected: {file_name}")
                
                # Update preview
                self.update_modern_logo_preview(filename)
                
            except Exception as e:
                messagebox.showerror("Error", f"Error loading logo: {str(e)}")
    
    def update_modern_logo_preview(self, logo_path):
        """Update modern logo preview"""
        try:
            if logo_path and os.path.exists(logo_path):
                # Load and resize image
                image = Image.open(logo_path)
                # Resize to fit preview frame (120x80)
                image.thumbnail((110, 70), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                
                # Update preview label
                self.logo_preview_label.configure(image=photo, text="")
                # Keep a reference to prevent garbage collection
                self.logo_preview_photo = photo
            else:
                self.logo_preview_label.configure(image="", text="No Logo")
                self.logo_preview_photo = None
        except Exception as e:
            self.logo_preview_label.configure(image="", text="Invalid Image")
            self.logo_preview_photo = None
        
    def load_defaults(self):
        """Load default values"""
        self.licensor_name.insert(0, "João Alexandre de Oliveira Maia")
        self.licensor_email.insert(0, "epg.joaomaia@gmail.com")
        self.licensor_address.insert("1.0", "Portugal")
        self.licensor_nif.insert(0, "252833902")
        self.licensor_phone.insert(0, "+351 934 330 807")
        self.software_name.insert(0, "Apito Final")
        self.software_version.insert(0, "All")
        software_desc = (
            "a lightweight, real-time graphics/data platform for live production. "
            "A Desktop Dashboard controls a terminal-based Server that renders URL overlays "
            "(add to any streaming setup that supports web/browser sources—OBS, vMix, "
            "Streamlabs, etc.). Built for efficiency and low memory use, it updates "
            "instantly over WebSocket, works on modest hardware, and supports both offline "
            "and online workflows if license has not expired."
        )
        self.software_description.insert("1.0", software_desc)
        
        # Set default values for spinboxes
        self.license_duration.set(DEFAULT_LICENSE_DURATION)
        self.max_users.set(DEFAULT_MAX_USERS)
        self.max_instances.set(DEFAULT_MAX_INSTANCES)
        self.payment_terms.set(DEFAULT_PAYMENT_TERMS)
        
        # Set default values for entries
        self.setup_fee.insert(0, "0.00")
        self.annual_fee.insert(0, "0.00")
        self.royalty_percentage.insert(0, "0.00")
        
        # Set contract start date
        self.contract_start_date.insert(0, date.today().strftime("%d/%m/%Y"))
        
    def collect_data(self) -> Dict[str, Any]:
        """Collect all form data"""
        return {
            "licensor": {
                "name": self.licensor_name.get(),
                "email": self.licensor_email.get(),
                "address": self.licensor_address.get("1.0", tk.END).strip(),
                "nif": self.licensor_nif.get(),
                "phone": self.licensor_phone.get(),
                "logo_path": self.licensor_logo_path if hasattr(self, 'licensor_logo_path') and self.licensor_logo_path else ""
            },
            "licensee": {
                "company": self.licensee_company.get(),
                "contact": self.licensee_contact.get(),
                "email": self.licensee_email.get(),
                "address": self.licensee_address.get("1.0", tk.END).strip(),
                "nif": self.licensee_nif.get(),
                "phone": self.licensee_phone.get(),
                "website": self.licensee_website.get()
            },
            "software": {
                "name": self.software_name.get(),
                "version": self.software_version.get(),
                "description": self.software_description.get("1.0", tk.END).strip()
            },
            "license": {
                "type": "commercial",
                "start_date": self.contract_start_date.get(),
                "duration": int(self.license_duration.get()),
                "allow_modifications": self.allow_modifications.get(),
                "allow_distribution": self.allow_distribution.get(),
                "allow_sublicensing": self.allow_sublicensing.get(),
                "max_users": int(self.max_users.get()),
                "max_instances": int(self.max_instances.get())
            },
            "pricing": {
                "setup_fee": float(self.setup_fee.get()),
                "annual_fee": float(self.annual_fee.get()),
                "royalty_percentage": float(self.royalty_percentage.get()),
                "payment_schedule": self.payment_schedule.get(),
                "payment_terms": int(self.payment_terms.get()),
                "currency": self.currency.get()
            }
        }
    
    def update_preview(self):
        """Update the preview with current data"""
        try:
            data = self.collect_data()
            agreement_text = self.generate_agreement_text(data)
            self.preview_text.delete("1.0", tk.END)
            self.preview_text.insert("1.0", agreement_text)
        except Exception as e:
            messagebox.showerror("Error", f"Error updating preview: {str(e)}")
    
    def generate_agreement_text(self, data: Dict[str, Any]) -> str:
        """Generate the full license agreement text"""
        current_date = datetime.now().strftime("%d/%m/%Y")
        
        # Parse start date from user input or use today's date
        try:
            start_date = data["license"]["start_date"]
            if not start_date.strip():
                start_date = date.today().strftime("%d/%m/%Y")
        except (KeyError, AttributeError):
            start_date = date.today().strftime("%d/%m/%Y")
        
        # Calculate end date based on start date and duration
        try:
            start_date_obj = datetime.strptime(start_date, "%d/%m/%Y").date()
            end_date_obj = start_date_obj.replace(
                year=start_date_obj.year + data["license"]["duration"] // 12
            )
            end_date = end_date_obj.strftime("%d/%m/%Y")
        except (ValueError, KeyError):
            end_date = (
                date.today().replace(
                    year=date.today().year + data["license"]["duration"] // 12
                )
            ).strftime("%d/%m/%Y")
        
        # Check if logo path exists
        logo_path = data.get("licensor", {}).get("logo_path", "")
        logo_placeholder = "[LOGO PLACEHOLDER]" if logo_path and os.path.exists(logo_path) else ""
        
        agreement = f"""
COMMERCIAL LICENSE AGREEMENT

This Commercial License Agreement (the "Agreement") is entered into on {current_date} by and between:

LICENSOR:                                    {logo_placeholder}
{data['licensor']['name']}                   (Logo will be inserted here
{data['licensor']['address']}                if provided)
NIF: {data['licensor']['nif']}
Email: {data['licensor']['email']}
Phone: {data['licensor']['phone']}

and

LICENSEE:
{data['licensee']['company']}
Represented by: {data['licensee']['contact']}
{data['licensee']['address']}
NIF: {data['licensee']['nif']}
Email: {data['licensee']['email']}
Phone: {data['licensee']['phone']}
Website: {data['licensee']['website']}

WHEREAS:
A. The Licensor is the owner of the proprietary software "{data['software']['name']}" version {data['software']['version']} (the "Software");
B. The Software is described as: {data['software']['description']};
C. The Licensee wishes to obtain a commercial license to use the Software;
D. The Licensor is willing to grant such license under the terms and conditions set forth herein;

NOW, THEREFORE, in consideration of the mutual promises and covenants contained herein, the parties agree as follows:

1. GRANT OF LICENSE
1.1 Subject to the terms and conditions of this Agreement, Licensor hereby grants to Licensee a non-exclusive, non-transferable license to use the Software for commercial purposes.
1.2 License Type: {data['license']['type'].title()} License
1.3 License Duration: {data['license']['duration']} months, from {start_date} to {end_date}
1.4 Usage Limits: Maximum {data['license']['max_users']} users and {data['license']['max_instances']} instances

2. LICENSE RESTRICTIONS
2.1 Licensee may NOT:
   - Modify, alter, or create derivative works of the Software without explicit written permission from Licensor
   - Reverse engineer, decompile, or disassemble the Software
   - Remove or alter any proprietary notices or labels on the Software
   - Use the Software beyond the scope of this license
   - Transfer or sublicense the Software without written consent

2.2 Code Modifications: {'Permitted with written consent' if data['license']['allow_modifications'] else 'Strictly prohibited without written permission'}
2.3 Distribution Rights: {'Permitted' if data['license']['allow_distribution'] else 'Not permitted'}
2.4 Sublicensing: {'Permitted' if data['license']['allow_sublicensing'] else 'Not permitted'}

3. PAYMENT TERMS
3.1 Setup Fee: {data['pricing']['currency']} {data['pricing']['setup_fee']:.2f}
3.2 Annual License Fee: {data['pricing']['currency']} {data['pricing']['annual_fee']:.2f}
3.3 Royalty Percentage: {data['pricing']['royalty_percentage']:.2f}% of revenue generated from Software use
3.4 Payment Schedule: {data['pricing']['payment_schedule']}
3.5 Payment Terms: {data['pricing']['payment_terms']} days from invoice date

4. INTELLECTUAL PROPERTY RIGHTS
4.1 The Software and all intellectual property rights therein remain the exclusive property of Licensor.
4.2 Licensee acknowledges that the Software contains trade secrets and proprietary information of Licensor.
4.3 Licensee agrees to maintain the confidentiality of the Software and not disclose it to third parties.

5. WARRANTIES AND DISCLAIMERS
5.1 Licensor warrants that it has the right to grant the license set forth in this Agreement.
5.2 THE SOFTWARE IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED.
5.3 Licensor disclaims all warranties, including but not limited to warranties of merchantability, fitness for a particular purpose, and non-infringement.

6. LIMITATION OF LIABILITY
6.1 IN NO EVENT SHALL LICENSOR BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES.
6.2 Licensor's total liability under this Agreement shall not exceed the total amount paid by Licensee under this Agreement.

7. TERMINATION
7.1 This Agreement may be terminated by either party upon written notice if the other party breaches any material term of this Agreement.
7.2 Upon termination, Licensee must cease all use of the Software and destroy all copies.
7.3 Sections 4, 5, 6, and 8 shall survive termination of this Agreement.

8. GENERAL PROVISIONS
8.1 Governing Law: This Agreement shall be governed by and construed in accordance with the laws of Portugal.
8.2 Jurisdiction: Any disputes arising from this Agreement shall be subject to the exclusive jurisdiction of the courts of Portugal.
8.3 Entire Agreement: This Agreement constitutes the entire agreement between the parties concerning the Software.
8.4 Amendments: This Agreement may only be amended by written agreement of both parties.
8.5 Force Majeure: Neither party shall be liable for any delay or failure to perform due to circumstances beyond their reasonable control.

9. NOTICES
9.1 All notices under this Agreement shall be in writing and delivered to the addresses specified above.
9.2 Notices shall be deemed received upon delivery if hand-delivered, or three (3) business days after mailing if sent by registered mail.

IN WITNESS WHEREOF, the parties have executed this Agreement as of the date first written above.

LICENSOR:                                    LICENSEE:
{data['licensor']['name']}                   {data['licensee']['company']}

By: _________________________                By: _________________________
Title: ______________________               Title: _______________________
Date: _______________________               Date: _______________________

Signature: _________________                 Signature: _________________

This Agreement is legally binding and enforceable under Portuguese law.
"""
        return agreement
    
    def generate_agreement(self):
        """Generate and save the license agreement"""
        try:
            data = self.collect_data()
            
            # Validate required fields
            if not data['licensor']['name'] or not data['licensee']['company']:
                messagebox.showerror(
                    "Error", 
                    "Please fill in all required fields (Licensor name and Licensee company)"
                )
                return
            
            # Ask user for file format
            file_format = messagebox.askyesno(
                "File Format", 
                "Generate PDF document?\n\nYes = PDF\nNo = Text file"
            )
            
            if file_format:
                # Generate PDF
                filename = filedialog.asksaveasfilename(
                    defaultextension=".pdf",
                    filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                    title="Save Commercial License Agreement as PDF"
                )
                
                if filename:
                    self.generate_pdf_agreement(data, filename)
            else:
                # Generate text file
                filename = filedialog.asksaveasfilename(
                    defaultextension=".txt",
                    filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                    title="Save Commercial License Agreement as Text"
                )
                
                if filename:
                    agreement_text = self.generate_agreement_text(data)
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(agreement_text)
                    
                    messagebox.showinfo(
                        "Success", 
                        f"Commercial License Agreement has been generated and saved to:\n{filename}"
                    )
                    
                    # Also save data as JSON for future reference
                    json_filename = filename.replace('.txt', '_data.json')
                    with open(json_filename, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    
        except Exception as e:
            messagebox.showerror("Error", f"Error generating agreement: {str(e)}")
     
    def create_pdf_header(self, data, doc):
        """Create PDF header with logo in top right corner"""
        from reportlab.platypus import Image as RLImage
        
        header_elements = []
        
        # Check if logo exists
        logo_path = data.get("licensor", {}).get("logo_path", "")
        if logo_path and os.path.exists(logo_path):
            try:
                # Create a table to position logo in top right corner
                logo_img = RLImage(logo_path, width=80, height=60)
                
                # Create a table with the logo in the right column
                header_table_data = [
                    [Spacer(1, 1), logo_img]  # Empty space on left, logo on right
                ]
                
                header_table = Table(header_table_data, colWidths=[doc.width-100, 100])
                header_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                    ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                    ('TOPPADDING', (0, 0), (-1, -1), 0),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ]))
                
                header_elements.append(header_table)
                header_elements.append(Spacer(1, 5))
            except Exception:
                pass  # Skip logo if there's an error
        
        return header_elements
     
    def generate_pdf_agreement(self, data, filename):
        """Generate PDF version of the agreement"""
        try:
            # Create PDF document with minimal margins to utilize all space
            doc = SimpleDocTemplate(
                filename, 
                pagesize=A4,
                topMargin=20,  # Minimal top margin
                bottomMargin=20,
                leftMargin=30,
                rightMargin=30
            )
            story = []
            
            # Get styles
            styles = getSampleStyleSheet()
            
            # Title style - positioned at very top
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=17,
                spaceAfter=12,
                spaceBefore=0,  # No space before to start at top
                alignment=TA_CENTER
            )
            
            # Heading style - smaller font, less spacing
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=11,
                spaceAfter=5,
                spaceBefore=6
            )
            
            # Normal text style - smaller font, less spacing
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=7,
                spaceAfter=4
            )
            
            # Create header with logo - this will be positioned at the very top
            header_data = self.create_pdf_header(data, doc)
            story.extend(header_data)
            
            # Add title immediately after header (no extra spacing)
            story.append(Paragraph("COMMERCIAL LICENSE AGREEMENT", title_style))
            story.append(Spacer(1, 10))
            
            # Add date
            current_date = datetime.now().strftime("%d/%m/%Y")
            story.append(Paragraph(f"This Commercial License Agreement (the \"Agreement\") is entered into on {current_date} by and between:", normal_style))
            story.append(Spacer(1, 15))
            
            # Add parties information
            licensor_info = [
                f"<b>LICENSOR:</b>",
                f"{data['licensor']['name']}",
                f"{data['licensor']['address']}",
                f"NIF: {data['licensor']['nif']}",
                f"Email: {data['licensor']['email']}",
                f"Phone: {data['licensor']['phone']}"
            ]
            
            licensee_info = [
                f"<b>LICENSEE:</b>",
                f"{data['licensee']['company']}",
                f"Represented by: {data['licensee']['contact']}",
                f"{data['licensee']['address']}",
                f"NIF: {data['licensee']['nif']}",
                f"Email: {data['licensee']['email']}",
                f"Phone: {data['licensee']['phone']}",
                f"Website: {data['licensee']['website']}"
            ]
            
            # Create table for parties
            parties_data = [
                [Paragraph("<br/>".join(licensor_info), normal_style), 
                 Paragraph("<br/>".join(licensee_info), normal_style)]
            ]
            
            parties_table = Table(parties_data, colWidths=[doc.width/2.0]*2)
            parties_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            story.append(parties_table)
            story.append(Spacer(1, 15))
            
            # Add WHEREAS clause
            story.append(Paragraph("<b>WHEREAS:</b>", heading_style))
            story.append(Paragraph(f"A. The Licensor is the owner of the proprietary software \"{data['software']['name']}\" version {data['software']['version']} (the \"Software\");", normal_style))
            story.append(Paragraph(f"B. The Software is described as: {data['software']['description']};", normal_style))
            story.append(Paragraph("C. The Licensee wishes to obtain a commercial license to use the Software;", normal_style))
            story.append(Paragraph("D. The Licensor is willing to grant such license under the terms and conditions set forth herein;", normal_style))
            story.append(Spacer(1, 15))
            
            # Add main agreement text
            story.append(Paragraph("NOW, THEREFORE, in consideration of the mutual promises and covenants contained herein, the parties agree as follows:", normal_style))
            story.append(Spacer(1, 15))
            
            # Add sections with reduced spacing
            sections = [
                ("1. GRANT OF LICENSE", [
                    "1.1 Subject to the terms and conditions of this Agreement, Licensor hereby grants to Licensee a non-exclusive, non-transferable license to use the Software for commercial purposes.",
                    f"1.2 License Type: {data['license']['type'].title()} License",
                    f"1.3 License Duration: {data['license']['duration']} months",
                    f"1.4 Usage Limits: Maximum {data['license']['max_users']} users and {data['license']['max_instances']} instances"
                ]),
                ("2. LICENSE RESTRICTIONS", [
                    "2.1 Licensee may NOT:",
                    "   - Modify, alter, or create derivative works of the Software without explicit written permission from Licensor",
                    "   - Reverse engineer, decompile, or disassemble the Software",
                    "   - Remove or alter any proprietary notices or labels on the Software",
                    "   - Use the Software beyond the scope of this license",
                    "   - Transfer or sublicense the Software without written consent",
                    f"2.2 Code Modifications: {'Permitted with written consent' if data['license']['allow_modifications'] else 'Strictly prohibited without written permission'}",
                    f"2.3 Distribution Rights: {'Permitted' if data['license']['allow_distribution'] else 'Not permitted'}",
                    f"2.4 Sublicensing: {'Permitted' if data['license']['allow_sublicensing'] else 'Not permitted'}"
                ]),
                ("3. PAYMENT TERMS", [
                    f"3.1 Setup Fee: {data['pricing']['currency']} {data['pricing']['setup_fee']:.2f}",
                    f"3.2 Annual License Fee: {data['pricing']['currency']} {data['pricing']['annual_fee']:.2f}",
                    f"3.3 Royalty Percentage: {data['pricing']['royalty_percentage']:.2f}% of revenue generated from Software use",
                    f"3.4 Payment Schedule: {data['pricing']['payment_schedule']}",
                    f"3.5 Payment Terms: {data['pricing']['payment_terms']} days from invoice date"
                ]),
                ("4. INTELLECTUAL PROPERTY RIGHTS", [
                    "4.1 The Software and all intellectual property rights therein remain the exclusive property of Licensor.",
                    "4.2 Licensee acknowledges that the Software contains trade secrets and proprietary information of Licensor.",
                    "4.3 Licensee agrees to maintain the confidentiality of the Software and not disclose it to third parties."
                ]),
                ("5. WARRANTIES AND DISCLAIMERS", [
                    "5.1 Licensor warrants that it has the right to grant the license set forth in this Agreement.",
                    "5.2 THE SOFTWARE IS PROVIDED \"AS IS\" WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED.",
                    "5.3 Licensor disclaims all warranties, including but not limited to warranties of merchantability, fitness for a particular purpose, and non-infringement."
                ]),
                ("6. LIMITATION OF LIABILITY", [
                    "6.1 IN NO EVENT SHALL LICENSOR BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES.",
                    "6.2 Licensor's total liability under this Agreement shall not exceed the total amount paid by Licensee under this Agreement."
                ]),
                ("7. TERMINATION", [
                    "7.1 This Agreement may be terminated by either party upon written notice if the other party breaches any material term of this Agreement.",
                    "7.2 Upon termination, Licensee must cease all use of the Software and destroy all copies.",
                    "7.3 Sections 4, 5, 6, and 8 shall survive termination of this Agreement."
                ]),
                ("8. GENERAL PROVISIONS", [
                    "8.1 Governing Law: This Agreement shall be governed by and construed in accordance with the laws of Portugal.",
                    "8.2 Jurisdiction: Any disputes arising from this Agreement shall be subject to the exclusive jurisdiction of the courts of Portugal.",
                    "8.3 Entire Agreement: This Agreement constitutes the entire agreement between the parties concerning the Software.",
                    "8.4 Amendments: This Agreement may only be amended by written agreement of both parties.",
                    "8.5 Force Majeure: Neither party shall be liable for any delay or failure to perform due to circumstances beyond their reasonable control."
                ]),
                ("9. NOTICES", [
                    "9.1 All notices under this Agreement shall be in writing and delivered to the addresses specified above.",
                    "9.2 Notices shall be deemed received upon delivery if hand-delivered, or three (3) business days after mailing if sent by registered mail."
                ])
            ]
            
            for section_title, section_items in sections:
                story.append(Paragraph(section_title, heading_style))
                for item in section_items:
                    story.append(Paragraph(item, normal_style))
                story.append(Spacer(1, 8))
            
            # Add signature section
            story.append(Paragraph("IN WITNESS WHEREOF, the parties have executed this Agreement as of the date first written above.", normal_style))
            story.append(Spacer(1, 15))
            
            signature_data = [
                [Paragraph("<b>LICENSOR:</b><br/>" + data['licensor']['name'], normal_style),
                 Paragraph("<b>LICENSEE:</b><br/>" + data['licensee']['company'], normal_style)],
                [Paragraph("By: _________________________<br/>Title: ______________________<br/>Date: _______________________<br/>Signature: _________________", normal_style),
                 Paragraph("By: _________________________<br/>Title: _______________________<br/>Date: _______________________<br/>Signature: _________________", normal_style)]
            ]
            
            signature_table = Table(signature_data, colWidths=[doc.width/2.0]*2)
            signature_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            story.append(signature_table)
            story.append(Spacer(1, 15))
            
            # Add footer
            story.append(Paragraph("This Agreement is legally binding and enforceable under Portuguese law.", normal_style))
            
            # Build PDF
            doc.build(story)
            
            messagebox.showinfo(
                "Success", 
                f"Commercial License Agreement has been generated and saved as PDF to:\n{filename}"
            )
            
            # Also save data as JSON for future reference
            json_filename = filename.replace('.pdf', '_data.json')
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            messagebox.showerror("Error", f"Error generating PDF: {str(e)}")
    
    def run(self):
        """Run the application"""
        self.root.mainloop()


def main():
    """Main function"""
    app = CommercialLicenseGenerator()
    app.run()


if __name__ == "__main__":
    main()
