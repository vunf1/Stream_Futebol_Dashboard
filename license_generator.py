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
import os
import json
from typing import Dict, Any, Optional

class CommercialLicenseGenerator:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Commercial License Agreement Generator")
        self.root.geometry("800x900")
        self.root.configure(bg='#f0f0f0')
        
        # Data storage
        self.license_data = {}
        
        self.setup_ui()
        self.load_defaults()
        
    def setup_ui(self):
        """Setup the main user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Commercial License Agreement Generator", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 20))
        
        # Configure notebook weights
        main_frame.rowconfigure(1, weight=1)
        
        # Create tabs
        self.create_licensor_tab(notebook)
        self.create_licensee_tab(notebook)
        self.create_terms_tab(notebook)
        self.create_pricing_tab(notebook)
        self.create_preview_tab(notebook)
        
        # Generate button
        generate_btn = ttk.Button(main_frame, text="Generate License Agreement", 
                                 command=self.generate_agreement, style="Accent.TButton")
        generate_btn.grid(row=2, column=0, columnspan=2, pady=(10, 0))
        
    def create_licensor_tab(self, notebook):
        """Create the licensor information tab"""
        frame = ttk.Frame(notebook, padding="20")
        notebook.add(frame, text="Licensor Information")
        
        # Licensor details
        ttk.Label(frame, text="Licensor (Software Owner) Information", 
                 font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 15))
        
        # Name
        ttk.Label(frame, text="Full Name:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.licensor_name = ttk.Entry(frame, width=40)
        self.licensor_name.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        
        # Email
        ttk.Label(frame, text="Email:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.licensor_email = ttk.Entry(frame, width=40)
        self.licensor_email.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        
        # Address
        ttk.Label(frame, text="Address:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.licensor_address = tk.Text(frame, height=3, width=40)
        self.licensor_address.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        
        # NIF (Portuguese Tax Number)
        ttk.Label(frame, text="NIF (Tax Number):").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.licensor_nif = ttk.Entry(frame, width=40)
        self.licensor_nif.grid(row=4, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        
        # Phone
        ttk.Label(frame, text="Phone:").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.licensor_phone = ttk.Entry(frame, width=40)
        self.licensor_phone.grid(row=5, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        
        # Software details
        ttk.Label(frame, text="Software Information", 
                 font=("Arial", 12, "bold")).grid(row=6, column=0, columnspan=2, pady=(20, 15))
        
        # Software name
        ttk.Label(frame, text="Software Name:").grid(row=7, column=0, sticky=tk.W, pady=2)
        self.software_name = ttk.Entry(frame, width=40)
        self.software_name.grid(row=7, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        
        # Software version
        ttk.Label(frame, text="Software Version:").grid(row=8, column=0, sticky=tk.W, pady=2)
        self.software_version = ttk.Entry(frame, width=40)
        self.software_version.grid(row=8, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        
        # Software description
        ttk.Label(frame, text="Software Description:").grid(row=9, column=0, sticky=tk.W, pady=2)
        self.software_description = tk.Text(frame, height=4, width=40)
        self.software_description.grid(row=9, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        
        # Configure grid weights
        frame.columnconfigure(1, weight=1)
        
    def create_licensee_tab(self, notebook):
        """Create the licensee information tab"""
        frame = ttk.Frame(notebook, padding="20")
        notebook.add(frame, text="Licensee Information")
        
        # Licensee details
        ttk.Label(frame, text="Licensee (Client) Information", 
                 font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 15))
        
        # Company/Organization name
        ttk.Label(frame, text="Company/Organization:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.licensee_company = ttk.Entry(frame, width=40)
        self.licensee_company.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        
        # Contact person
        ttk.Label(frame, text="Contact Person:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.licensee_contact = ttk.Entry(frame, width=40)
        self.licensee_contact.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        
        # Email
        ttk.Label(frame, text="Email:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.licensee_email = ttk.Entry(frame, width=40)
        self.licensee_email.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        
        # Address
        ttk.Label(frame, text="Address:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.licensee_address = tk.Text(frame, height=3, width=40)
        self.licensee_address.grid(row=4, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        
        # NIF (Portuguese Tax Number)
        ttk.Label(frame, text="NIF (Tax Number):").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.licensee_nif = ttk.Entry(frame, width=40)
        self.licensee_nif.grid(row=5, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        
        # Phone
        ttk.Label(frame, text="Phone:").grid(row=6, column=0, sticky=tk.W, pady=2)
        self.licensee_phone = ttk.Entry(frame, width=40)
        self.licensee_phone.grid(row=6, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        
        # Website
        ttk.Label(frame, text="Website:").grid(row=7, column=0, sticky=tk.W, pady=2)
        self.licensee_website = ttk.Entry(frame, width=40)
        self.licensee_website.grid(row=7, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        
        # Configure grid weights
        frame.columnconfigure(1, weight=1)
        
    def create_terms_tab(self, notebook):
        """Create the license terms tab"""
        frame = ttk.Frame(notebook, padding="20")
        notebook.add(frame, text="License Terms")
        
        # License type
        ttk.Label(frame, text="License Type", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 15))
        
        self.license_type = tk.StringVar(value="commercial")
        ttk.Label(frame, text="Commercial License", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Label(frame, text="(Only Commercial License available)", font=("Arial", 8, "italic")).grid(row=2, column=0, sticky=tk.W, pady=(0, 15))
        
        # Contract start date
        ttk.Label(frame, text="Contract Start Date", font=("Arial", 12, "bold")).grid(row=3, column=0, columnspan=2, pady=(20, 15))
        
        ttk.Label(frame, text="Start Date (DD/MM/YYYY):").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.contract_start_date = ttk.Entry(frame, width=15)
        self.contract_start_date.grid(row=4, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        self.contract_start_date.insert(0, date.today().strftime("%d/%m/%Y"))
        
        # License duration
        ttk.Label(frame, text="License Duration", font=("Arial", 12, "bold")).grid(row=5, column=0, columnspan=2, pady=(20, 15))
        
        ttk.Label(frame, text="Duration (months):").grid(row=6, column=0, sticky=tk.W, pady=2)
        self.license_duration = ttk.Spinbox(frame, from_=1, to=120, width=10)
        self.license_duration.grid(row=6, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        self.license_duration.set(12)
        
        # Usage restrictions
        ttk.Label(frame, text="Usage Restrictions", font=("Arial", 12, "bold")).grid(row=7, column=0, columnspan=2, pady=(20, 15))
        
        self.allow_modifications = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text="Allow code modifications", 
                       variable=self.allow_modifications).grid(row=8, column=0, sticky=tk.W)
        
        self.allow_distribution = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text="Allow distribution/resale", 
                       variable=self.allow_distribution).grid(row=9, column=0, sticky=tk.W)
        
        self.allow_sublicensing = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text="Allow sublicensing", 
                       variable=self.allow_sublicensing).grid(row=10, column=0, sticky=tk.W)
        
        # Number of users/instances
        ttk.Label(frame, text="Usage Limits", font=("Arial", 12, "bold")).grid(row=11, column=0, columnspan=2, pady=(20, 15))
        
        ttk.Label(frame, text="Max number of users:").grid(row=12, column=0, sticky=tk.W, pady=2)
        self.max_users = ttk.Spinbox(frame, from_=1, to=10000, width=10)
        self.max_users.grid(row=12, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        self.max_users.set(1)
        
        ttk.Label(frame, text="Max number of instances:").grid(row=13, column=0, sticky=tk.W, pady=2)
        self.max_instances = ttk.Spinbox(frame, from_=1, to=1000, width=10)
        self.max_instances.grid(row=13, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        self.max_instances.set(1)
        
        # Configure grid weights
        frame.columnconfigure(1, weight=1)
        
    def create_pricing_tab(self, notebook):
        """Create the pricing tab"""
        frame = ttk.Frame(notebook, padding="20")
        notebook.add(frame, text="Pricing & Payment")
        
        # Pricing structure
        ttk.Label(frame, text="Pricing Structure", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 15))
        
        ttk.Label(frame, text="Setup Fee (€):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.setup_fee = ttk.Entry(frame, width=15)
        self.setup_fee.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        self.setup_fee.insert(0, "0.00")
        
        ttk.Label(frame, text="Annual License Fee (€):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.annual_fee = ttk.Entry(frame, width=15)
        self.annual_fee.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        self.annual_fee.insert(0, "0.00")
        
        ttk.Label(frame, text="Royalty Percentage (%):").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.royalty_percentage = ttk.Entry(frame, width=15)
        self.royalty_percentage.grid(row=3, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        self.royalty_percentage.insert(0, "0.00")
        
        # Payment terms
        ttk.Label(frame, text="Payment Terms", font=("Arial", 12, "bold")).grid(row=4, column=0, columnspan=2, pady=(20, 15))
        
        ttk.Label(frame, text="Payment Schedule:").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.payment_schedule = ttk.Combobox(frame, values=["Monthly", "Quarterly", "Annually", "One-time"], width=15)
        self.payment_schedule.grid(row=5, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        self.payment_schedule.set("Annually")
        
        ttk.Label(frame, text="Payment Terms (days):").grid(row=6, column=0, sticky=tk.W, pady=2)
        self.payment_terms = ttk.Spinbox(frame, from_=0, to=90, width=10)
        self.payment_terms.grid(row=6, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        self.payment_terms.set(30)
        
        # Currency
        ttk.Label(frame, text="Currency:").grid(row=7, column=0, sticky=tk.W, pady=2)
        self.currency = ttk.Combobox(frame, values=["EUR", "USD", "GBP"], width=15)
        self.currency.grid(row=7, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        self.currency.set("EUR")
        
        # Configure grid weights
        frame.columnconfigure(1, weight=1)
        
    def create_preview_tab(self, notebook):
        """Create the preview tab"""
        frame = ttk.Frame(notebook, padding="20")
        notebook.add(frame, text="Preview")
        
        # Preview text area
        ttk.Label(frame, text="License Agreement Preview", 
                 font=("Arial", 12, "bold")).grid(row=0, column=0, pady=(0, 10))
        
        # Create text widget with scrollbar
        text_frame = ttk.Frame(frame)
        text_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.preview_text = tk.Text(text_frame, height=20, width=80, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.preview_text.yview)
        self.preview_text.configure(yscrollcommand=scrollbar.set)
        
        self.preview_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Refresh preview button
        refresh_btn = ttk.Button(frame, text="Refresh Preview", command=self.update_preview)
        refresh_btn.grid(row=2, column=0, pady=(10, 0))
        
        # Configure grid weights
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        
    def load_defaults(self):
        """Load default values"""
        self.licensor_name.insert(0, "João Alexandre de Oliveira Maia")
        self.licensor_email.insert(0, "epg.joaomaia@gmail.com")
        self.licensor_address.insert("1.0", "Portugal")
        self.licensor_nif.insert(0, "252833902")
        self.licensor_phone.insert(0, "+351 934 330 807")
        self.software_name.insert(0, "Apito Final")
        self.software_version.insert(0, "All")
        self.software_description.insert("1.0", "a lightweight, real-time graphics/data platform for live production. A Desktop Dashboard controls a terminal-based Server that renders URL overlays (add to any streaming setup that supports web/browser sources—OBS, vMix, Streamlabs, etc.). Built for efficiency and low memory use, it updates instantly over WebSocket, works on modest hardware, and supports both offline and online workflows if license has not expired.")
        
    def collect_data(self) -> Dict[str, Any]:
        """Collect all form data"""
        return {
            "licensor": {
                "name": self.licensor_name.get(),
                "email": self.licensor_email.get(),
                "address": self.licensor_address.get("1.0", tk.END).strip(),
                "nif": self.licensor_nif.get(),
                "phone": self.licensor_phone.get()
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
                "type": self.license_type.get(),
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
        except:
            start_date = date.today().strftime("%d/%m/%Y")
        
        # Calculate end date based on start date and duration
        try:
            start_date_obj = datetime.strptime(start_date, "%d/%m/%Y").date()
            end_date_obj = start_date_obj.replace(year=start_date_obj.year + data["license"]["duration"] // 12)
            end_date = end_date_obj.strftime("%d/%m/%Y")
        except:
            end_date = (date.today().replace(year=date.today().year + data["license"]["duration"] // 12)).strftime("%d/%m/%Y")
        
        agreement = f"""
COMMERCIAL LICENSE AGREEMENT

This Commercial License Agreement (the "Agreement") is entered into on {current_date} by and between:

LICENSOR:
{data['licensor']['name']}
{data['licensor']['address']}
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
                messagebox.showerror("Error", "Please fill in all required fields (Licensor name and Licensee company)")
                return
            
            # Generate agreement text
            agreement_text = self.generate_agreement_text(data)
            
            # Save to file
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="Save Commercial License Agreement"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(agreement_text)
                
                messagebox.showinfo("Success", f"Commercial License Agreement has been generated and saved to:\n{filename}")
                
                # Also save data as JSON for future reference
                json_filename = filename.replace('.txt', '_data.json')
                with open(json_filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    
        except Exception as e:
            messagebox.showerror("Error", f"Error generating agreement: {str(e)}")
    
    def run(self):
        """Run the application"""
        self.root.mainloop()

def main():
    """Main function"""
    app = CommercialLicenseGenerator()
    app.run()

if __name__ == "__main__":
    main()
