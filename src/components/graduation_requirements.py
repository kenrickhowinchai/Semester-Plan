import tkinter as tk
from tkinter import ttk

class GraduationRequirementsFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        
        # Define the requirements
        self.requirements = {
            "Kernbereich": {
                "total": 48,
                "sub_requirements": {
                    "Informatik und Mathematik": 18,
                    "Simulation und Optimierung": 18,
                    "Messen, Steuern, Regeln": 12
                }
            },
            "Profilbereich": {
                "total": 18
            },
            "Projekt": {
                "total": 6
            },
            "Freiwahlbereich": {  # Renamed from Wahlbereich to Freiwahlbereich
                "total": 18
            },
            "Fachpraktikum": {
                "total": 6
            },
            "Masterarbeit": {
                "total": 24
            }
        }
        
        # Create the UI
        self.create_widgets()
        
        # Update the display
        self.update_requirements()
        
    def create_widgets(self):
        """Create the UI elements"""
        # Title label
        title_label = ttk.Label(
            self, 
            text="Graduation Requirements", 
            font=("Helvetica", 14, "bold")
        )
        title_label.pack(fill=tk.X, pady=(0, 10))
        
        # Create frame for requirements
        self.req_frame = ttk.Frame(self)
        self.req_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create progress bars for each requirement
        self.progress_bars = {}
        self.credits_labels = {}
        row = 0
        
        # Main requirements
        for req_name, req_data in self.requirements.items():
            # Add label for requirement name
            req_label = ttk.Label(
                self.req_frame, 
                text=f"{req_name}: ", 
                font=("Helvetica", 11, "bold")
            )
            req_label.grid(row=row, column=0, sticky="w", padx=(0, 5), pady=2)
            
            # Add progress bar
            progress_bar = ttk.Progressbar(
                self.req_frame, 
                orient="horizontal", 
                length=200, 
                mode="determinate",
                maximum=req_data["total"]
            )
            progress_bar.grid(row=row, column=1, sticky="ew", padx=5, pady=2)
            
            # Add credits label
            credits_label = ttk.Label(
                self.req_frame, 
                text=f"0/{req_data['total']} LP"
            )
            credits_label.grid(row=row, column=2, padx=5, pady=2)
            
            # Store references
            self.progress_bars[req_name] = progress_bar
            self.credits_labels[req_name] = credits_label
            
            row += 1
            
            # Add sub-requirements if any
            if "sub_requirements" in req_data:
                for sub_name, sub_total in req_data["sub_requirements"].items():
                    # Indented sub-requirement label
                    sub_label = ttk.Label(
                        self.req_frame, 
                        text=f"• {sub_name}: "
                    )
                    sub_label.grid(row=row, column=0, sticky="w", padx=(20, 5), pady=2)
                    
                    # Add sub progress bar
                    sub_progress = ttk.Progressbar(
                        self.req_frame, 
                        orient="horizontal", 
                        length=180, 
                        mode="determinate",
                        maximum=sub_total
                    )
                    sub_progress.grid(row=row, column=1, sticky="ew", padx=5, pady=2)
                    
                    # Add sub credits label
                    sub_credits = ttk.Label(
                        self.req_frame, 
                        text=f"0/{sub_total} LP"
                    )
                    sub_credits.grid(row=row, column=2, padx=5, pady=2)
                    
                    # Store references
                    self.progress_bars[f"{req_name}_{sub_name}"] = sub_progress
                    self.credits_labels[f"{req_name}_{sub_name}"] = sub_credits
                    
                    row += 1
        
        # Configure column weights
        self.req_frame.columnconfigure(1, weight=1)
        
        # Add a separator
        ttk.Separator(self, orient="horizontal").pack(fill=tk.X, pady=10)
        
        # Add total progress bar
        total_frame = ttk.Frame(self)
        total_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(
            total_frame, 
            text="Total Progress: ", 
            font=("Helvetica", 12, "bold")
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.total_progress = ttk.Progressbar(
            total_frame, 
            orient="horizontal", 
            length=300, 
            mode="determinate",
            maximum=120  # Total credits needed: 90 + 6 + 24
        )
        self.total_progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.total_label = ttk.Label(
            total_frame, 
            text="0/120 LP", 
            font=("Helvetica", 11)
        )
        self.total_label.pack(side=tk.LEFT, padx=5)
    
    def update_requirements(self):
        """Update the progress bars and labels based on current courses"""
        # Reset all counters
        credits_per_requirement = {
            "Kernbereich_Informatik und Mathematik": 0,
            "Kernbereich_Simulation und Optimierung": 0,
            "Kernbereich_Messen, Steuern, Regeln": 0,
            "Profilbereich": 0,
            "Projekt": 0,
            "Freiwahlbereich": 0,  # Renamed from Wahlbereich
            "Fachpraktikum": 0,
            "Masterarbeit": 0
        }
        
        # Count credits in each semester
        for semester_frame in self.app.semester_frames:
            for course in semester_frame.courses:
                # Skip courses without a group
                if not hasattr(course, 'group') or not course.group:
                    continue
                    
                # Fix the mapping issue with more strict group identifier checking
                group = course.group.strip()  # Remove any whitespace
                credits = course.credits
                
                # Use more explicit matching to fix the issues
                if group.startswith("1."):  # Kernbereich - Informatik und Mathematik
                    credits_per_requirement["Kernbereich_Informatik und Mathematik"] += credits
                elif group.startswith("2."):  # Kernbereich - Simulation und Optimierung
                    credits_per_requirement["Kernbereich_Simulation und Optimierung"] += credits
                elif group.startswith("3."):  # Kernbereich - Messen, Steuern, Regeln
                    credits_per_requirement["Kernbereich_Messen, Steuern, Regeln"] += credits
                elif group.startswith("4."):  # Profilbereich
                    credits_per_requirement["Profilbereich"] += credits
                elif group.startswith("6."):  # Projekt
                    credits_per_requirement["Projekt"] += credits
                elif group.startswith("7."):  # Freiwahlbereich (was Wahlbereich)
                    credits_per_requirement["Freiwahlbereich"] += credits
                elif group.startswith("8."):  # Fachpraktikum 
                    credits_per_requirement["Fachpraktikum"] += credits
                elif group.startswith("9."):  # Masterarbeit
                    credits_per_requirement["Masterarbeit"] += credits
        
        # Calculate total for Kernbereich
        kernbereich_total = (
            credits_per_requirement["Kernbereich_Informatik und Mathematik"] +
            credits_per_requirement["Kernbereich_Simulation und Optimierung"] +
            credits_per_requirement["Kernbereich_Messen, Steuern, Regeln"]
        )
        
        # Update the progress bars and labels for sub-requirements
        for sub_name in ["Informatik und Mathematik", "Simulation und Optimierung", "Messen, Steuern, Regeln"]:
            key = f"Kernbereich_{sub_name}"
            if key in self.progress_bars:
                credits = credits_per_requirement[key]
                max_credits = self.requirements["Kernbereich"]["sub_requirements"][sub_name]
                self.progress_bars[key]["value"] = min(credits, max_credits)
                self.credits_labels[key].config(text=f"{credits}/{max_credits} LP")
                
                # Highlight if requirement met
                if credits >= max_credits:
                    self.credits_labels[key].config(foreground="green")
                else:
                    self.credits_labels[key].config(foreground="black")
        
        # Update main requirement progress bars
        requirement_totals = {
            "Kernbereich": kernbereich_total,
            "Profilbereich": credits_per_requirement["Profilbereich"],
            "Projekt": credits_per_requirement["Projekt"],
            "Freiwahlbereich": credits_per_requirement["Freiwahlbereich"],  # Renamed
            "Fachpraktikum": credits_per_requirement["Fachpraktikum"],
            "Masterarbeit": credits_per_requirement["Masterarbeit"]
        }
        
        # Update all main progress bars
        for req_name, req_data in self.requirements.items():
            credits = requirement_totals[req_name]
            max_credits = req_data["total"]
            
            if req_name in self.progress_bars:
                self.progress_bars[req_name]["value"] = min(credits, max_credits)
                self.credits_labels[req_name].config(text=f"{credits}/{max_credits} LP")
                
                # Highlight if requirement met
                if credits >= max_credits:
                    self.credits_labels[req_name].config(foreground="green")
                else:
                    self.credits_labels[req_name].config(foreground="black")
        
        # Calculate and update total progress
        total_credits = sum(requirement_totals.values())
        self.total_progress["value"] = min(total_credits, 120)
        self.total_label.config(text=f"{total_credits}/120 LP")
        
        # Highlight if all requirements are met
        if total_credits >= 120:
            self.total_label.config(foreground="green", font=("Helvetica", 11, "bold"))
        else:
            self.total_label.config(foreground="black", font=("Helvetica", 11))
    
    def apply_scaling(self, scale_factor):
        """Apply scaling to this graduation requirements frame"""
        # Update fonts for all widgets recursively
        def update_widget_font(widget):
            try:
                current_font = widget.cget("font")
                if current_font:
                    if isinstance(current_font, (tuple, list)):
                        family, size = current_font[0], current_font[1]
                        new_size = max(8, int(size * scale_factor))
                        new_font = (family, new_size)
                        if len(current_font) > 2:
                            new_font = new_font + current_font[2:]
                        widget.configure(font=new_font)
                    elif isinstance(current_font, str):
                        # Handle font strings
                        parts = current_font.split()
                        if len(parts) >= 2:
                            try:
                                size = int(parts[1])
                                new_size = max(8, int(size * scale_factor))
                                parts[1] = str(new_size)
                                new_font = " ".join(parts)
                                widget.configure(font=new_font)
                            except (ValueError, IndexError):
                                pass
            except tk.TclError:
                pass
            
            # Update children
            try:
                for child in widget.winfo_children():
                    update_widget_font(child)
            except tk.TclError:
                pass
        
        update_widget_font(self)
        
        # Update progress bar lengths
        for progress_bar in self.progress_bars.values():
            base_length = 200
            new_length = int(base_length * scale_factor)
            progress_bar.configure(length=new_length)
    
    def set_scale_factor(self, scale_factor):
        """Update the graduation requirements frame based on scale factor"""
        self.scale_factor = scale_factor
        
        # Store base dimensions if not already stored
        if not hasattr(self, '_base_dimensions'):
            self._base_dimensions = {
                'title_font_size': 14,
                'label_font_size': 10,
                'padx': 5,
                'pady': 5
            }
        
        # Update fonts
        title_size = max(10, int(self._base_dimensions['title_font_size'] * scale_factor))
        label_size = max(8, int(self._base_dimensions['label_font_size'] * scale_factor))
        
        # Update padding
        new_padx = max(1, int(self._base_dimensions['padx'] * scale_factor))
        new_pady = max(1, int(self._base_dimensions['pady'] * scale_factor))
        
        # Find and update all labels in the frame
        def update_fonts_recursive(widget):
            try:
                current_font = widget.cget("font")
                if current_font:
                    if isinstance(current_font, (tuple, list)) and len(current_font) >= 2:
                        family, size = current_font[0], current_font[1]
                        # Determine if this is a title or regular label
                        if size >= 14:  # Title
                            new_size = max(10, int(size * scale_factor))
                        else:  # Regular label
                            new_size = max(8, int(size * scale_factor))
                        new_font = (family, new_size)
                        if len(current_font) > 2:
                            new_font = new_font + current_font[2:]
                        widget.configure(font=new_font)
            except tk.TclError:
                pass
            
            # Recursively update children
            try:
                for child in widget.winfo_children():
                    update_fonts_recursive(child)
            except tk.TclError:
                pass
        
        update_fonts_recursive(self)